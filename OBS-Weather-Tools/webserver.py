from flask import Flask, render_template, jsonify, request
import threading
import time
import os
import logging
import requests
from database import insert_or_update_alert, remove_expired_alerts, fetch_active_alerts
from datetime import datetime, timezone

# Explicitly set the template folder and static folder
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '../templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '../static')
)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable to store the current alert scroll content
current_alerts = []


@app.before_request
def log_request_info():
    """Log information about incoming requests."""
    logging.debug(f"Request to {request.path} with method {request.method}")


@app.route('/')
def index():
    """Serve the main webpage with the alert scroll."""
    return render_template('index.html')


@app.route('/alerts', methods=['GET'])
def get_alerts():
    """API endpoint to fetch the current active alerts for the scroll."""
    logging.debug("Fetching active alerts from the database.")
    remove_expired_alerts()  # Clean up expired alerts
    alerts = fetch_active_alerts()

    # Convert alerts from tuples to dictionaries
    alert_keys = ["id", "event", "details", "expiration_time", "locations"]
    max_length = 100  # Define a maximum length for the locations text
    alerts = [
        {
            **dict(zip(alert_keys, alert)),
            "scroll_required": len(alert[4]) > max_length  # Add a flag if locations text is too long
        }
        for alert in alerts
    ]

    logging.debug(f"Active alerts fetched: {alerts}")
    return jsonify(alerts)


@app.route('/debug/alerts', methods=['GET'])
def debug_alerts():
    """Debug route to fetch all alerts from the database."""
    try:
        alerts = fetch_active_alerts()
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)})


# NWS API endpoint and parameters
nws_endpoint = "https://api.weather.gov/alerts/active"
nws_params = {
    "status": "actual",
    "message_type": "alert,update",
    "code": "TOR,SVR,SVS,FFW",
    "region_type": "land",
    "urgency": "Immediate,Future,Expected",
    "severity": "Extreme,Severe,Moderate",
    "certainty": "Observed,Likely,Possible",
    "limit": 500
}


def update_alerts():
    """Fetch real alerts from the NWS API and update the database."""
    while True:
        try:
            response = requests.get(nws_endpoint, params=nws_params)
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])

                now = datetime.now(timezone.utc)
                for feature in features:
                    alert_id = feature["id"]

                    properties = feature["properties"]
                    event = properties["event"]
                    expiration_time = properties.get("expires", now.isoformat())
                    locations = properties.get("areaDesc", "")

                    parameters = properties.get("parameters", {})
                    hail_size = parameters.get("maxHailSize", ["N/A"])[0].title()
                    tornado_detection = parameters.get("tornadoDetection", ["N/A"])[0].title()
                    wind_gust = parameters.get("maxWindGust", ["N/A"])[0].title()

                    if event == "Tornado Warning":
                        details = f"Tornado: {tornado_detection}, Hail Size: {hail_size}"
                    elif event == "Severe Thunderstorm Warning":
                        details = f"Wind Gusts: {wind_gust}, Hail Size: {hail_size}"
                    elif event == "Flash Flood Warning":
                        details = "Flash flooding is occurring or imminent."
                    else:
                        details = "Details not available"

                    insert_or_update_alert(
                        alert_id=alert_id,
                        event=event,
                        details=details,
                        expiration_time=expiration_time,
                        locations=locations
                    )

                logging.debug("Real alerts fetched and updated successfully.")
            else:
                logging.error(f"Failed to fetch alerts: {response.status_code}")
        except Exception as e:
            logging.error(f"Error fetching alerts: {e}")

        time.sleep(60)  # Wait for 1 minute before fetching alerts again


def clear_database():
    """Clears all records from the active alerts table in the database when the application is launched."""
    from database import clear_database
    try:
        clear_database('active_alerts')
        logging.debug("Database cleared successfully on application launch.")
    except Exception as e:
        logging.error(f"Error clearing database: {e}")


if __name__ == '__main__':
    # Clear the database on application launch
    clear_database()

    # Start the alert updating thread
    alert_thread = threading.Thread(target=update_alerts, daemon=True)
    alert_thread.start()

    # Run the Flask webserver
    app.run(host='127.0.0.1', port=5000)

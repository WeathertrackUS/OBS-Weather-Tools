from flask import Flask, render_template, jsonify, request
import threading
import time
import os
import logging
from database import insert_or_update_alert, remove_expired_alerts, fetch_active_alerts
from datetime import datetime, timedelta, timezone

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
    """
    Log information about incoming requests.
    """
    logging.debug(f"Request to {request.path} with method {request.method}")

@app.route('/')
def index():
    """
    Serve the main webpage with the alert scroll.
    """
    return render_template('index.html')

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """
    API endpoint to fetch the current active alerts for the scroll.
    """
    logging.debug("Fetching active alerts from the database.")
    remove_expired_alerts()  # Clean up expired alerts
    alerts = fetch_active_alerts()

    # Convert alerts from tuples to dictionaries
    alert_keys = ["id", "event", "details", "expiration_time", "locations"]
    alerts = [dict(zip(alert_keys, alert)) for alert in alerts]

    logging.debug(f"Active alerts fetched: {alerts}")
    return jsonify(alerts)

@app.route('/debug/alerts', methods=['GET'])
def debug_alerts():
    """
    Debug route to fetch all alerts from the database.
    """
    from database import fetch_active_alerts
    try:
        alerts = fetch_active_alerts()
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)})

def update_alerts():
    """
    Simulate updating alerts periodically. Replace this with actual alert fetching logic.
    """
    while True:
        try:
            now = datetime.now(timezone.utc)
            logging.debug("Inserting test alerts into the database.")
            insert_or_update_alert(
                alert_id="1",
                event="Severe Thunderstorm Warning",
                details="Hail: <0.75 in | Wind: 60 MPH",
                expiration_time=(now + timedelta(minutes=25)).isoformat(),
                locations="Columbia, WI; Dane, WI"
            )
            insert_or_update_alert(
                alert_id="2",
                event="Tornado Warning",
                details="Take shelter immediately",
                expiration_time=(now + timedelta(minutes=15)).isoformat(),
                locations="Northwestern LA"
            )
            logging.debug("Test alerts inserted successfully.")
        except Exception as e:
            logging.error(f"Error inserting test alerts: {e}")
        time.sleep(300)  # Update every 5 minutes

if __name__ == '__main__':
    # Start the alert updating thread
    alert_thread = threading.Thread(target=update_alerts, daemon=True)
    alert_thread.start()

    # Run the Flask webserver
    app.run(host='0.0.0.0', port=5000)
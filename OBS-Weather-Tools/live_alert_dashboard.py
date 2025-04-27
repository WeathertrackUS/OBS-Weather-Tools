# alert-dashboard.py

from flask import Flask, render_template
import database
from datetime import datetime, timezone, timedelta
import os
import re
from collections import OrderedDict
import json  # Use json instead of ast for safer deserialization
from dateutil import parser  # Add this import for better date parsing
import logging  # Add this import for logging

base_dir = '.'

app = Flask(__name__, template_folder=os.path.join(base_dir, '../web/templates'))
app.config['ACTIVE_ALERTS'] = []  # Initialize the active_alerts list


def read_from_file(filename):
    """
    Read an integer from a file.

    If the file exists and contains an integer, return that integer.
    If the file does not exist or is empty, return 0.

    Parameters:
        filename (str): The name of the file to read from.

    Returns:
        int: The integer read from the file or 0 if file not found or empty.
    """
    if filename not in ("TOR Total.txt", "SVR Total.txt", "TOR Watch.txt", "SVR Watch.txt", "FFW Total.txt", "SPS.txt"):
        return "Invalid filename"

    try:
        with open(filename, "r") as file:
            content = file.read().strip()
            if content:
                return int(content)
            return 0
    except FileNotFoundError:
        return 0


@app.route('/')
def index():
    """
    This function handles the root route of the application, fetching and updating alerts,
    reading counts from files for various weather warnings, and rendering an HTML template
    with the retrieved data.

    Parameters:
        None

    Returns:
        A rendered HTML template with the retrieved data.
    """
    fetch_and_update_alerts()
    active_alerts = app.config.get('ACTIVE_ALERTS', [])

    tornado_warning_total_count = read_from_file(os.path.join('files/count', "TOR Total.txt"))

    severe_thunderstorm_warning_total_count = read_from_file(os.path.join('files/count', "SVR Total.txt"))

    tornado_watch_count = read_from_file(os.path.join('files/count', "TOR Watch.txt"))
    severe_thunderstorm_watch_count = read_from_file(os.path.join('files/count', "SVR Watch.txt"))

    flash_flood_warning_total_count = read_from_file(os.path.join('files/count', "FFW Total.txt"))

    special_weather_statement_count = read_from_file(os.path.join('files/count', "SPS.txt"))

    return render_template('index.html', active_alerts=active_alerts,
                           tornado_warning_total_count=tornado_warning_total_count,
                           severe_thunderstorm_warning_total_count=severe_thunderstorm_warning_total_count,
                           tornado_watch_count=tornado_watch_count,
                           severe_thunderstorm_watch_count=severe_thunderstorm_watch_count,
                           flash_flood_warning_total_count=flash_flood_warning_total_count,
                           special_weather_statement_count=special_weather_statement_count
                           )


ALERT_PRIORITY = OrderedDict([
    ('Tornado Warning', 1),
    ('Severe Thunderstorm Warning', 2),
    ('Flash Flood Warning', 3),
    ('Tornado Watch', 4),
    ('Severe Thunderstorm Watch', 5),
    ('Special Weather Statement', 6)
])


def sort_alerts(alerts):
    """
    Sorts a list of alerts based on their priority defined in the ALERT_PRIORITY dictionary.

    Parameters:
        alerts (list): A list of alerts to be sorted.

    Returns:
        list: A list of alerts sorted by priority.
    """
    sorted_alerts = sorted(alerts, key=lambda x: ALERT_PRIORITY.get(x['event'], float('inf')))
    return sorted_alerts


def get_timezone_keyword(offset):
    """
    Returns the timezone keyword corresponding to the given offset.

    Parameters:
        offset (timedelta): The time offset for which to retrieve the timezone keyword.

    Returns:
        str: The timezone keyword if the offset is found in the mapping, otherwise the offset representation as a string.
    """
    # Define a mapping of offsets to timezone keywords
    offset_to_keyword = {
        timedelta(hours=-5): "CDT",  # Central Daylight Time
        timedelta(hours=-4): "EDT",  # Eastern Daylight Time
        timedelta(hours=-6): "MDT",  # Mountain Daylight Time
        timedelta(hours=-7): "PDT",  # Pacific Daylight Time
        timedelta(hours=-9): "AKDT",  # Alaska Daylight Time
        timedelta(hours=-10): "HST",  # Hawaii Standard Time
        timedelta(hours=-3): "ADT",  # Atlantic Daylight Time (Puerto Rico)
        timedelta(hours=+10): "CHST",  # Chamorro Standard Time (Guam, Northern Mariana Islands)
        timedelta(hours=+11): "SAMT",  # Samoa Standard Time (American Samoa)
    }

    timezone_keyword = offset_to_keyword.get(offset)
    if timezone_keyword is None:
        return str(offset)
    return timezone_keyword


def fetch_and_update_alerts():  # skipcq: PY-R1000
    """
    Fetches and updates alerts from the database.

    This function retrieves all alerts from the 'sent_alerts' table,
    processes their properties, and updates the active alerts list.
    It also removes expired alerts from the database.

    Parameters:
        None

    Returns:
        None
    """
    active_alerts = []
    alerts = database.get_all_alerts(table_name="sent_alerts")
    current_time = datetime.now(timezone.utc)
    for alert in alerts:
        identifier, sent_datetime_str, expires_datetime_str, properties_str = alert  # skipcq: PYL-W0612

        # Use dateutil.parser for more robust datetime parsing
        try:
            # Handle datetime strings with timezone information
            expires_datetime = parser.parse(expires_datetime_str)
            if expires_datetime.tzinfo is None:
                # If no timezone info, assume UTC
                expires_datetime = expires_datetime.replace(tzinfo=timezone.utc)
        except Exception as e:
            print(f"Error parsing datetime: {e}")
            # Skip this alert if we can't parse the date
            continue

        properties = json.loads(properties_str)  # Convert the JSON string back to a dictionary

        alert_endtime = properties["expires"]
        alert_endtime_tz_offset = alert_endtime[-6:]  # Extract the timezone offset from the string

        # Ensure the 'expires' field is in the correct format
        try:
            alert_endtime_naive = datetime.strptime(alert_endtime[:-6], "%Y-%m-%dT%H:%M:%S")  # Parse the datetime part without the offset
        except ValueError as e:
            logging.error(f"Error parsing 'expires' field: {alert_endtime}. Skipping alert. Error: {e}")
            continue

        # Create a timezone object from the offset
        offset_hours = int(alert_endtime_tz_offset[:3])
        offset_minutes = int(alert_endtime_tz_offset[4:])
        offset = timedelta(hours=offset_hours, minutes=offset_minutes)
        alert_endtime_tz = timezone(offset)

        # Localize the naive datetime using the timezone offset
        expires_datetime_localized = alert_endtime_naive.replace(tzinfo=alert_endtime_tz)

        thunderstorm_damage_threat = clean_and_capitalize(properties.get("parameters", {}).get("thunderstormDamageThreat", ""))
        tornado_damage_threat = clean_and_capitalize(properties.get("parameters", {}).get("tornadoDamageThreat", ""))
        tornado_detection = clean_and_capitalize(properties.get("parameters", {}).get("tornadoDetection", ""))
        flash_flood_damage_threat = clean_and_capitalize(properties.get("parameters", {}).get("flashFloodDamageThreat", ""))

        if expires_datetime > current_time:
            event = properties["event"]
            messagetype = properties["messageType"]
            wfo = properties["senderName"]

            parameters = properties["parameters"]
            maxwind = clean_and_capitalize(parameters.get("maxWindGust"))
            maxhail = clean_and_capitalize(parameters.get("maxHailSize"))
            nwsheadline = clean_string(parameters.get("NWSheadline"))
            FFdetection = clean_and_capitalize(parameters.get("flashFloodDetection"))

            description = ''

            if messagetype == 'Update':
                if description != '':
                    description += ", UPDATE"
                else:
                    description += "UPDATE"

            if nwsheadline != 'None':
                if description != '':
                    description += f", NWS Headline: {nwsheadline}"
                else:
                    description += f"NWS Headline: {nwsheadline}"

            if thunderstorm_damage_threat:
                if description != '':
                    description += f", Thunderstorm Damage Threat: {(thunderstorm_damage_threat)}"
                else:
                    description += f"Thunderstorm Damage Threat: {(thunderstorm_damage_threat)}"

            if tornado_damage_threat:
                if description != '':
                    description += f", Tornado Damage Threat: {(tornado_damage_threat)}"
                else:
                    description += f"Tornado Damage Threat: {(tornado_damage_threat)}"

            if tornado_detection:
                if description != '':
                    description += f", Tornado Detection: {(tornado_detection)}"
                else:
                    description += f"Tornado Detection: {(tornado_detection)}"

            if flash_flood_damage_threat:
                if description != '':
                    description += f", Flash Flood Damage Threat: {(flash_flood_damage_threat)}"
                else:
                    description += f"Flash Flood Damage Threat: {(flash_flood_damage_threat)}"

            if maxwind != 'None':
                if description != '':
                    description += f", Max Wind: {(maxwind)}"
                else:
                    description += f"Max Wind: {(maxwind)}"

            if maxhail != 'None':
                if description != '':
                    description += f", Max Hail: {(maxhail)}"
                else:
                    description += f"Max Hail: {(maxhail)}"

            if FFdetection != 'None':
                if description != '':
                    description += f", Flash Flood Detection: {(FFdetection)}"
                else:
                    description += f"Flash Flood Detection: {(FFdetection)}"

            timezone_keyword = get_timezone_keyword(offset)
            formatted_expires_datetime = expires_datetime_localized.strftime(f"%B %d, %Y %I:%M %p {timezone_keyword}")

            area_desc = properties["areaDesc"]
            active_alerts.append({
                "event": event,
                "wfo": wfo,
                "description": description,
                "expiration": formatted_expires_datetime,
                "area": area_desc
            })
        else:
            database.remove_alert(identifier=identifier, table_name="sent_alerts")

    sorted_alerts = sort_alerts(active_alerts)

    with app.app_context():
        app.config['ACTIVE_ALERTS'] = sorted_alerts


def clean_and_capitalize(value):
    """
    Cleans and capitalizes a given value by removing unwanted characters and
    capitalizing the first letter. The function accepts a value that can be either
    a string or a list of strings, and returns the cleaned and capitalized string.

    Parameters:
        value (str or list): The value to be cleaned and capitalized

    Returns:
        str: The cleaned and capitalized string
    """
    if isinstance(value, list):
        # If the value is a list, join its elements into a string
        string = ''.join(str(item) for item in value)
    else:
        # If the value is not a list, treat it as a string
        string = str(value)

    if not string:
        return ""

    cleaned_string = re.sub(r'[\[\]\'\"]', '', string)
    return cleaned_string.capitalize()


def clean_string(value):
    """
    Cleans a given value by converting it to a string and removing unwanted characters.

    Parameters:
    value (list or str): The value to be cleaned. It can be either a list or a string.

    Returns:
    str: The cleaned string. If the input value is empty, an empty string is returned.
    """
    if isinstance(value, list):
        # If the value is a list, join its elements into a string
        string = ''.join(str(item) for item in value)
    else:
        # If the value is not a list, treat it as a string
        string = str(value)

    if not string:
        return ""

    cleaned_string = re.sub(r'[\[\]\'\"]', '', string)
    return cleaned_string


def update_active_alerts():
    """
    Updates the list of active alerts by fetching and updating the alerts based on the current time and alert expiration time.

    This function calls fetch_and_update_alerts to refresh the active alerts.

    Parameters:
        None

    Returns:
        None
    """
    with app.app_context():
        fetch_and_update_alerts()


def dashboard_kickstart(stop_event):
    """
    Starts the dashboard application and runs it indefinitely until the stop event is triggered.

    Parameters:
        stop_event (threading.Event): An event object used to signal the function to stop its execution.

    Returns:
        None
    """
    while not stop_event.is_set():
        app.run(debug=False, host='localhost', port=5000)

# alert-dashboard.py

from flask import Flask, render_template
import database
from datetime import datetime, timezone, timedelta
import os
import re
import pytz
import multiprocessing

base_dir = '.'

app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))
app.config['ACTIVE_ALERTS'] = []  # Initialize the active_alerts list

def read_from_file(filename):
    """
    Read an integer from a file. If the file exists and contains an integer, return that integer. If the file does not exist or is empty, return 0.
    @param filename - the name of the file to read from
    @return the integer read from the file or 0 if file not found or empty
    """
    try:
        with open(filename, "r") as file:
            content = file.read().strip()
            if content:
                return int(content)
            else:
                return 0
    except FileNotFoundError:
        return 0

@app.route('/')
def index():
    """
    This function fetches and updates alerts, reads counts from files for various weather warnings, and renders an HTML template with the retrieved data. @return: None
    """
    fetch_and_update_alerts()
    active_alerts = app.config.get('ACTIVE_ALERTS', [])

    tornado_warning_total_count = read_from_file(os.path.join('count', "TOR Total.txt"))
    
    severe_thunderstorm_warning_total_count = read_from_file(os.path.join('count', "SVR Total.txt"))
    
    tornado_watch_count = read_from_file(os.path.join('count', "TOR Watch.txt"))
    severe_thunderstorm_watch_count = read_from_file(os.path.join('count', "SVR Watch.txt"))
    
    flash_flood_warning_total_count = read_from_file(os.path.join('count', "FFW Total.txt"))

    special_weather_statement_count = read_from_file(os.path.join('count', "SPS.txt"))

    return render_template('index.html', active_alerts=active_alerts,
                           tornado_warning_total_count=tornado_warning_total_count,
                           severe_thunderstorm_warning_total_count=severe_thunderstorm_warning_total_count,
                           tornado_watch_count=tornado_watch_count,
                           severe_thunderstorm_watch_count=severe_thunderstorm_watch_count,
                           flash_flood_warning_total_count=flash_flood_warning_total_count,
                           special_weather_statement_count=special_weather_statement_count
                           )
    

from collections import OrderedDict

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
    Sort a list of alerts based on their priority defined in the ALERT_PRIORITY dictionary.
    @param alerts - List of alerts to be sorted
    @return List of alerts sorted by priority
    """
    sorted_alerts = sorted(alerts, key=lambda x: ALERT_PRIORITY.get(x['event'], float('inf')))
    return sorted_alerts

def get_timezone_keyword(offset):
    """
    Given a time offset, return the corresponding timezone keyword.
    @param offset - the time offset
    @return the timezone keyword or the offset as a string if no match is found.
    """
    # Define a mapping of offsets to timezone keywords
    offset_to_keyword = {
        timedelta(hours=-5): "CDT",  # Central Daylight Time
        timedelta(hours=-4): "EDT",  # Eastern Daylight Time
        timedelta(hours=-6): "MDT",  # Mountain Daylight Time
        timedelta(hours=-7): "PDT",  # Pacific Daylight Time
        timedelta(hours=-9): "AKDT", # Alaska Daylight Time
        timedelta(hours=-10): "HST", # Hawaii Standard Time
        timedelta(hours=-3): "ADT",  # Atlantic Daylight Time (Puerto Rico)
        timedelta(hours=+10): "CHST", # Chamorro Standard Time (Guam, Northern Mariana Islands)
        timedelta(hours=+11): "SAMT", # Samoa Standard Time (American Samoa)
        # Add more mappings as needed
    }

    timezone_keyword = offset_to_keyword.get(offset)
    if timezone_keyword is None:
        # If the offset is not found in the mapping, return the offset representation as a string
        return str(offset)
    else:
        return timezone_keyword

def fetch_and_update_alerts():
    """
    Fetches and updates active alerts based on the current time and alert expiration time.
    @return None
    """
    active_alerts = []
    alerts = database.get_all_alerts()
    current_time = datetime.now(timezone.utc)
    for alert in alerts:
        identifier, sent_datetime_str, expires_datetime_str, properties_str = alert

        sent_datetime = datetime.strptime(sent_datetime_str, '%Y-%m-%d %H:%M:%S')
        expires_datetime = datetime.strptime(expires_datetime_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        properties = eval(properties_str)  # Convert the string back to a dictionary

        alert_endtime = properties["expires"]
        alert_endtime_tz_offset = alert_endtime[-6:]  # Extract the timezone offset from the string
        alert_endtime_naive = datetime.strptime(alert_endtime[:-6], "%Y-%m-%dT%H:%M:%S")  # Parse the datetime part without the offset

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
            headline = properties["headline"]
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
                    description += f", UPDATE"
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
            database.remove_alert(identifier)

    sorted_alerts = sort_alerts(active_alerts)

    with app.app_context():
        app.config['ACTIVE_ALERTS'] = sorted_alerts

def clean_and_capitalize(value):
    """
    Clean and capitalize a given value, removing unwanted characters and capitalizing the first letter.
    @param value - The value to be cleaned and capitalized
    @return The cleaned and capitalized string
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
    with app.app_context():
        fetch_and_update_alerts()

def dashboard_kickstart(stop_event):
    while not stop_event.is_set():
        app.run(debug=False, host='localhost', port=5000)
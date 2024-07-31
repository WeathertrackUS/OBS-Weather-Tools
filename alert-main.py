import requests
import json
from plyer import notification
import time
from obswebsocket import obsws, requests as obs_requests
import os
import pystray
from PIL import Image
import threading
from datetime import datetime, timezone
import alerts
import database
from dateutil import parser, tz
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from dashboard import app, update_active_alerts
import pytz

database.create_table()

# OBS WebSocket settings
obs_socket_ip = "216.16.108.109"  # Replace with your OBS WebSocket IP
obs_socket_port = 4455  # Replace with your OBS WebSocket port
obs_socket_password = "wuqYpn5glvxmaudo"  # Replace with your OBS WebSocket password

# OBS source settings
obs_source_settings = {
    "Tornado Warning": "Alert-TOR",
    "Severe Thunderstorm Warning": "Alert-SVR",
    "Flash Flood Warning": "Alert-FFW",
    "Severe Thunderstorm Watch": "Alert-SVA",
    "Tornado Watch": "Alert-TOA",
    "Special Weather Statement": "Alert-SPS"
}

'''obs_scene_ids = {
    "Alert-TOR": 10,
    "Alert-SVR": 9,
    "Alert-FFW": 11,
    "Alert-SVA": 8,
    "Alert-TOA": 12
}'''

# Connect to the OBS WebSocket
ws = obsws(obs_socket_ip, obs_socket_port, obs_socket_password)
ws.connect()

# Create the 'warnings' directory if it doesn't exist
if not os.path.exists('warnings'):
    os.makedirs('warnings')
if not os.path.exists('count'):
    os.makedirs('count')

# Initialize the warning files with their names and 0
warning_files = {
    'TOR Total.txt': 'Active Tornado Warnings: 0',
    'TOR.txt': 'Tornado Warnings: 0',
    'TOR Observed.txt': 'Confirmed Tornado Warnings: 0',
    'PDS TOR.txt': 'PDS Tornado Warnings: 0',
    'TOR Emergancy.txt': 'Tornado Emergencies: 0',

    'SVR Total.txt': 'Active Severe Thunderstorm Warnings: 0',
    'SVR.txt': 'Severe Thunderstorm Warnings: 0',
    'Considerable SVR.txt': 'Considerable SVR Warnings: 0',
    'Destructive SVR.txt': 'Destructive SVR Warnings: 0',
    'TOR Possible SVR.txt': 'Tornado POSSIBLE SVR Warnings: 0',

    'TOR Watch.txt': 'Tornado Watches: 0',
    'SVR Watch.txt': 'Severe Thunderstorm Watches: 0',

    'FFW Total.txt': 'Active Flash Flood Warnings: 0',
    'FFW.txt': 'Flash Flood Warnings: 0',
    'Considerable FFW.txt': 'Considerable Flash Flood Warnings: 0',
    'FFE.txt': 'Flash Flood Emergencies: 0',
}

warning_count_files = {
    'TOR Total.txt': '0',
    'TOR.txt': '0',
    'TOR Observed.txt': '0',
    'PDS TOR.txt': '0',
    'TOR Emergancy.txt': '0',

    'SVR Total.txt': '0',
    'SVR.txt': '0',
    'Considerable SVR.txt': '0',
    'Destructive SVR.txt': '0',
    'TOR Possible SVR.txt': '0',

    'TOR Watch.txt': '0',
    'SVR Watch.txt': '0',

    'FFW Total.txt': '0',
    'FFW.txt': '0',
    'Considerable FFW.txt': '0',
    'FFE.txt': '0',
}

# Create the warning files with their initial content
for filename, content in warning_files.items():
    file_path = os.path.join('warnings', filename)
    with open(file_path, 'w') as file:
        file.write(content)

# Create the warning files with their initial content
for filename, content in warning_count_files.items():
    file_path = os.path.join('count', filename)
    with open(file_path, 'w') as file:
        file.write(content)

def close_program():
    os._exit(0)

def hide_to_system_tray():
        global icon
        image = Image.open('My_project.png')
        menu = (pystray.MenuItem("Exit", close_program),)
        icon = pystray.Icon("name", image, "My System Tray Icon", menu)
        icon.run()

def warning_count(data):
    tornado_warning_total_count = 0
    tornado_warning_count = 0
    torr_count = 0
    pds_tor_count = 0
    tore_count = 0

    tornado_watch_count = 0

    severe_thunderstorm_warning_total_count = 0
    severe_thunderstorm_warning_count = 0
    considerable_svr_count = 0
    destructive_svr_count = 0
    tor_possible_svr_count = 0

    severe_thunderstorm_watch_count = 0

    flash_flood_warning_total_count = 0
    flash_flood_warning_count = 0
    considerable_ffw_count = 0
    ffe_count = 0

    for alert in data["features"]:
        properties = alert["properties"]
        event = properties["event"]

        thunderstorm_damage_threat = properties.get("parameters", {}).get("thunderstormDamageThreat")
        tornado_damage_threat = properties.get("parameters", {}).get("tornadoDamageThreat")
        tornado_detection = properties.get("parameters", {}).get("tornadoDetection")
        flash_flood_damage_threat = properties.get("parameters", {}).get("flashFloodDamageThreat")

        if event == "Tornado Warning":
            tornado_warning_total_count += 1
            if tornado_detection == 'Observed':
                torr_count += 1
            elif tornado_damage_threat == 'Considerable':
                pds_tor_count += 1
            elif tornado_damage_threat == 'Catastrophic':
                tore_count += 1
            else:
                tornado_warning_count += 1
        elif event == "Severe Thunderstorm Warning":
            severe_thunderstorm_warning_total_count += 1
            if thunderstorm_damage_threat == 'Considerable':
                considerable_svr_count += 1
            elif thunderstorm_damage_threat == 'Destructive':
                destructive_svr_count += 1
            elif tornado_detection == 'Possible':
                tor_possible_svr_count += 1
            else:
                severe_thunderstorm_warning_count += 1
        elif event == "Tornado Watch":
            tornado_watch_count += 1
        elif event == "Severe Thunderstorm Watch":
            severe_thunderstorm_watch_count += 1
        elif event == "Flash Flood Warning":
            flash_flood_warning_total_count += 1
            if flash_flood_damage_threat == 'Considerable':
                considerable_ffw_count += 1
            elif flash_flood_damage_threat == 'Catastrophic':
                ffe_count += 1
            else:
                flash_flood_warning_count += 1

        # Read previous counts from files
        previous_tornado_warning_count = read_from_file(os.path.join("count", "TOR Count.txt"))
        previous_tornado_warning_total_count = read_from_file(os.path.join("count", "TOR Total.txt"))
        previous_torr_count = read_from_file(os.path.join("count", "TORR Count.txt"))
        previous_pds_tor_count = read_from_file(os.path.join("count", "PDS TOR Count.txt"))
        previous_tore_count = read_from_file(os.path.join("count", "Tore Count.txt"))
        
        previous_severe_thunderstorm_warning_total_count = read_from_file(os.path.join("count", "SVR Total.txt"))
        previous_severe_thunderstorm_warning_count = read_from_file(os.path.join("count", "SVR Count.txt"))
        previous_considerable_svr_count = read_from_file(os.path.join("count", "SVR Considerable Count.txt"))
        previous_destructive_svr_count = read_from_file(os.path.join("count", "SVR Destructive Count.txt"))
        previous_tor_possible_svr_count = read_from_file(os.path.join("count", "SVR Possible Count.txt"))
        
        previous_tornado_watch_count = read_from_file(os.path.join("count", "TOR Watch Count.txt"))
        previous_severe_thunderstorm_watch_count = read_from_file(os.path.join("count", "SVR Watch Count.txt"))
        
        previous_flash_flood_warning_count = read_from_file(os.path.join("count", "FFW Count.txt"))
        previous_flash_flood_warning_total_count = read_from_file(os.path.join("count", "FFW Total.txt"))
        previous_considerable_ffw_count = read_from_file(os.path.join("count", "Considerable FFW Count.txt"))
        previous_ffe_count = read_from_file(os.path.join("count", "FFE Count.txt"))

        # Update count files only if the count has changed
        if tornado_warning_count != previous_tornado_warning_count:
            count_file_path = os.path.join('count', 'TOR Count.txt')
            write_to_file(count_file_path, str(tornado_warning_count))
            warnings_file_path = os.path.join('warnings', 'TOR.txt')
            write_to_file(warnings_file_path, f'Active Tornado Warnings: {tornado_warning_count}')
        
        if tornado_warning_total_count != previous_tornado_warning_total_count:
            count_file_path = os.path.join('count', 'TOR Total.txt')
            write_to_file(count_file_path, str(tornado_warning_total_count))
            warnings_file_path = os.path.join('warnings', 'TOR Total.txt')
            write_to_file(warnings_file_path, f'Active Tornado Warnings: {tornado_warning_total_count}')
        
        if torr_count != previous_torr_count:
            count_file_path = os.path.join('count', 'TOR Observed Count.txt')
            write_to_file(count_file_path, str(torr_count))
            warnings_file_path = os.path.join('warnings', 'TOR Observed.txt')
            write_to_file(warnings_file_path, f'Tornado Observations: {torr_count}')
        
        if pds_tor_count != previous_pds_tor_count:
            count_file_path = os.path.join('count', 'PDS TOR Count.txt')
            write_to_file(count_file_path, str(pds_tor_count))
            warnings_file_path = os.path.join('warnings', 'PDS TOR.txt')
            write_to_file(warnings_file_path, f'PDS Tornado Observations: {pds_tor_count}')
        
        if tore_count != previous_tore_count:
            count_file_path = os.path.join('count', 'TOR Emergancy Count.txt')
            write_to_file(count_file_path, str(tore_count))
            warnings_file_path = os.path.join('warnings', 'TOR Emergancy.txt')
            write_to_file(warnings_file_path, f'Tornado Emergancy Observations: {tore_count}')
        

        if severe_thunderstorm_warning_count != previous_severe_thunderstorm_warning_count:
            count_file_path = os.path.join('count', 'SVR Count.txt')
            write_to_file(count_file_path, str(severe_thunderstorm_warning_count))
            warnings_file_path = os.path.join('warnings', 'SVR.txt')
            write_to_file(warnings_file_path, f'Active Severe Thunderstorm Warnings: {severe_thunderstorm_warning_count}')

        if severe_thunderstorm_warning_total_count != previous_severe_thunderstorm_warning_total_count:
            count_file_path = os.path.join('count', 'SVR Total.txt')
            write_to_file(count_file_path, str(severe_thunderstorm_warning_total_count))
            warnings_file_path = os.path.join('warnings', 'SVR Total.txt')
            write_to_file(warnings_file_path, f'Active Severe Thunderstorm Warnings: {severe_thunderstorm_warning_total_count}')
        
        if considerable_svr_count != previous_considerable_svr_count:
            count_file_path = os.path.join('count', 'Considerable SVR Count.txt')
            write_to_file(count_file_path, str(considerable_svr_count))
            warnings_file_path = os.path.join('warnings', 'Considerable SVR.txt')
            write_to_file(warnings_file_path, f'Considerable SVR Warnings: {considerable_svr_count}')

        if destructive_svr_count != previous_destructive_svr_count:
            count_file_path = os.path.join('count', 'Destructive SVR Count.txt')
            write_to_file(count_file_path, str(destructive_svr_count))
            warnings_file_path = os.path.join('warnings', 'Destructive SVR.txt')
            write_to_file(warnings_file_path, f'Destructive SVR Warnings: {destructive_svr_count}')

        if tor_possible_svr_count != previous_tor_possible_svr_count:
            count_file_path = os.path.join('count', 'TOR SVR Count.txt')
            write_to_file(count_file_path, str(tor_possible_svr_count))
            warnings_file_path = os.path.join('warnings', 'TOR SVR.txt')
            write_to_file(warnings_file_path, f'TOR SVR Warnings: {tor_possible_svr_count}')


        if tornado_watch_count != previous_tornado_watch_count:
            count_file_path = os.path.join('count', 'TOR Watch Count.txt')
            write_to_file(count_file_path, str(tornado_watch_count))
            warnings_file_path = os.path.join('warnings', 'TOR Watch.txt')
            write_to_file(warnings_file_path, f'Tornado Watches: {tornado_watch_count}')

        if severe_thunderstorm_watch_count != previous_severe_thunderstorm_watch_count:
            count_file_path = os.path.join('count', 'SVR Watch Count.txt')
            write_to_file(count_file_path, str(severe_thunderstorm_watch_count))
            warnings_file_path = os.path.join('warnings', 'SVR Watch.txt')
            write_to_file(warnings_file_path, f'Severe Thunderstorm Watches: {severe_thunderstorm_watch_count}')


        if flash_flood_warning_count != previous_flash_flood_warning_count:
            count_file_path = os.path.join('count', 'FFW Count.txt')
            write_to_file(count_file_path, str(flash_flood_warning_count))
            warnings_file_path = os.path.join('warnings', 'FFW.txt')
            write_to_file(warnings_file_path, f'Flash Flood Warnings: {flash_flood_warning_count}')
        
        if flash_flood_warning_total_count != previous_flash_flood_warning_total_count:
            count_file_path = os.path.join('count', 'FFW Total.txt')
            write_to_file(count_file_path, str(flash_flood_warning_total_count))
            warnings_file_path = os.path.join('warnings', 'FFW Total.txt')
            write_to_file(warnings_file_path, f'Flash Flood Warnings: {flash_flood_warning_total_count}')
        
        if considerable_ffw_count != previous_considerable_ffw_count:
            count_file_path = os.path.join('count', 'Considerable FFW Count.txt')
            write_to_file(count_file_path, str(considerable_ffw_count))
            warnings_file_path = os.path.join('warnings', 'Considerable FFW.txt')
            write_to_file(warnings_file_path, f'Considerable Flash Flood Warnings: {considerable_ffw_count}')

        if ffe_count != previous_ffe_count:
            count_file_path = os.path.join('count', 'FFE Count.txt')
            write_to_file(count_file_path, str(ffe_count))
            warnings_file_path = os.path.join('warnings', 'FFE.txt')

def write_to_file(filename, content):
    with open(filename, "w") as file:
        file.write(content + "\n")

def read_from_file(filename):
    try:
        with open(filename, "r") as file:
            content = file.read().strip()
            if content:
                # Remove any null bytes or invalid characters before converting to int
                cleaned_content = ''.join(char for char in content if char.isprintable())
                return int(cleaned_content)
            else:
                return 0
    except (FileNotFoundError, ValueError):
        return 0

def get_current_scene():
    current_scene = ws.call(obs_requests.GetCurrentProgramScene())
    return current_scene.get("name"), current_scene.get("sceneUuid")

def get_source_id(source_name, scene_name, scene_uuid):
    scene_items = ws.call(obs_requests.GetSceneItemList(sceneName=scene_name, sceneUuid=scene_uuid))
    for item in scene_items.get("sceneItems", []):
        if item["sourceName"] == source_name:
            return item["sourceItemId"]
    return None

def get_scene_and_source_info(source_name):
    if not obs_socket_ip or not obs_socket_port or not obs_socket_password:
        return None, None, None

    try:
        from obswebsocket import obsws, requests as obs_requests

        scenes_response = ws.call(obs_requests.GetSceneList())
        response_dict = scenes_response.__dict__

        if 'datain' in response_dict:
            data_in = response_dict['datain']
            current_scene_name = data_in.get('currentProgramSceneName')
            current_scene_uuid = data_in.get('currentProgramSceneUuid')
            if current_scene_name and current_scene_uuid:
                scene_items_response = ws.call(obs_requests.GetSceneItemList(sceneName=current_scene_name, sceneUuid=current_scene_uuid))
                scene_items_dict = scene_items_response.__dict__

                if 'datain' in scene_items_dict:
                    source_data_in = scene_items_dict['datain']
                    scene_items = source_data_in.get('sceneItems', [])

                    for item in scene_items:
                        if item["sourceName"] == source_name:
                            return current_scene_name, current_scene_uuid, item["sceneItemId"]
    except ImportError:
        pass

    return None, None, None

def fetch_alerts():
    endpoint = "https://api.weather.gov/alerts/active"
    params = {
        "status": "actual",
        "message_type": "alert,update",
        "code": 'TOR,TOA,SVR,SVA,FFW,SVS',
        "region_type": "land",
        "urgency": "Immediate,Future,Expected",
        "severity": "Extreme,Severe,Moderate",
        "certainty": "Observed,Likely,Possible",
        "limit": 500
    }

    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        features = data["features"]

        warning_count(data)

        for alert in features:
            properties = alert["properties"]
            event = properties["event"]
            identifier = properties["id"]
            sent = properties["sent"]
            area_desc = properties["areaDesc"]
            expires = properties["expires"]

            sent_datetime = parser.parse(sent).astimezone(pytz.utc)
            expires_datetime = parser.parse(expires).astimezone(pytz.utc)

            if not database.alert_exists(identifier):
                # This is a new alert
                event, notification_message, area_desc, expires_datetime = alerts.process_alert(identifier, properties, sent_datetime, area_desc)
                display_alert(event, notification_message, area_desc)
                database.insert_alert(identifier, sent_datetime, expires_datetime, properties)
            else:
                existing_alert = database.get_alert(identifier)
                existing_sent_datetime_str = existing_alert[1]
                existing_expires_datetime_str = existing_alert[2]
                existing_properties = existing_alert[3]

                # Convert existing_sent_datetime and existing_expires_datetime to UTC
                existing_sent_datetime = parser.parse(existing_sent_datetime_str).replace(tzinfo=tz.tzutc())
                existing_expires_datetime = parser.parse(existing_expires_datetime_str).replace(tzinfo=tz.tzutc())

                if sent_datetime != existing_sent_datetime:
                    # This is an update to an existing alert
                    event, notification_message, area_desc, expires_datetime = alerts.process_alert(identifier, properties, sent_datetime, area_desc)
                    display_alert(event, notification_message, area_desc)
                    database.update_alert(identifier, sent_datetime, expires_datetime, properties)
    update_active_alerts()

def update_active_alerts_and_exit():
    update_active_alerts()

def display_alert(event, notification_message, area_desc):
    # Display Windows notification
    notification.notify(
        title=f"{event}",
        message=notification_message,
        app_name="Weather Alert",
        timeout=10,
        toast=True
    )

    print('')
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(f'{current_time} - {notification_message}, {area_desc}')

    # Write the headline to the Warning Header.txt file
    write_to_file("Warning Header.txt", event)

    write_to_file("Warning Info.txt", notification_message)

    write_to_file("Warning Area.txt", area_desc)
    time.sleep(2)

    source_name = obs_source_settings.get(event)
    scene_name, scene_uuid, scene_item_id = get_scene_and_source_info(source_name)

    ws.call(obs_requests.SetSceneItemEnabled(sceneName=scene_name, sceneUuid=scene_uuid, sceneItemId=scene_item_id, sceneItemEnabled=True))
    time.sleep(5)
    ws.call(obs_requests.SetSceneItemEnabled(sceneName=scene_name, sceneUuid=scene_uuid, sceneItemId=scene_item_id, sceneItemEnabled=False))

    time.sleep(3)

system_thray_thread = threading.Thread(target=hide_to_system_tray)
system_thray_thread.start()

'''scheduler = BackgroundScheduler()
scheduler.add_job(func=fetch_alerts, trigger='interval', seconds=5)
scheduler.start()'''

atexit.register(update_active_alerts_and_exit)

while True:
    fetch_alerts()
    time.sleep(5)  # Wait for 5 seconds before checking for new alerts

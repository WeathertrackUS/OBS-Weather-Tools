import requests
from plyer import notification
import time
from obswebsocket import obsws, requests as obs_requests
import os
from datetime import datetime
import live_alerts_processing
import database
from dateutil import parser, tz
import atexit
from live_alert_dashboard import update_active_alerts
import pytz
import json  # Add this import for JSON serialization

# OBS WebSocket settings
obs_socket_ip = "192.168.1.231"
obs_socket_port = 4455
obs_socket_password = "KUYaPzQqResQ5CEt"

# OBS source settings
obs_source_settings_old = {
    "Tornado Warning": "Alert-TOR",
    "Severe Thunderstorm Warning": "Alert-SVR",
    "Flash Flood Warning": "Alert-FFW",
    "Severe Thunderstorm Watch": "Alert-SVA",
    "Tornado Watch": "Alert-TOA",
    "Special Weather Statement": "Alert-SPS"
}

obs_source_settings = {
    "Tornado Warning": "TORAlertTest",
    "Severe Thunderstorm Warning": "SevereAlertTest"
}

'''obs_scene_ids = {
    "Alert-TOR": 10,
    "Alert-SVR": 9,
    "Alert-FFW": 11,
    "Alert-SVA": 8,
    "Alert-TOA": 12
    "Alert-SPS": 13
}'''

alerting_alerts = ['Tornado Warning', 'Severe Thunderstorm Warning', 'Flash Flood Warning']

# Create the 'warnings' directory if it doesn't exist
if not os.path.exists('files/warnings'):
    os.makedirs('files/warnings')
if not os.path.exists('files/count'):
    os.makedirs('files/count')
# Add this for warning info files
if not os.path.exists('files'):
    os.makedirs('files')

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

    'SPS.txt': 'Special Weather Statements: 0',
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

    'SPS.txt': '0',
}

# Create the warning files with their initial content
for filename, content in warning_files.items():
    file_path = os.path.join('files/warnings', filename)
    with open(file_path, 'w') as file:
        file.write(content)

# Create the warning files with their initial content
for filename, content in warning_count_files.items():
    file_path = os.path.join('files/count', filename)
    with open(file_path, 'w') as file:
        file.write(content)


def close_program():
    """
    Closes the program immediately using os._exit(0).

    Parameters:
        None

    Returns:
        None
    """
    os._exit(0)


def warning_count(data):  # skipcq: PY-R1000
    """
    This function processes weather alert data and updates count files accordingly.

    It iterates through each alert in the provided data, checks the event type, and updates the corresponding count variables.
    The function also reads previous counts from files, compares them with the current counts, and updates the files only if the counts have changed.

    Parameters:
        data (dict): A dictionary containing weather alert data.

    Returns:
        None
    """
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
        previous_tornado_warning_count = read_from_file(os.path.join("files/count", "TOR Count.txt"))
        previous_tornado_warning_total_count = read_from_file(os.path.join("files/count", "TOR Total.txt"))
        previous_torr_count = read_from_file(os.path.join("files/count", "TORR Count.txt"))
        previous_pds_tor_count = read_from_file(os.path.join("files/count", "PDS TOR Count.txt"))
        previous_tore_count = read_from_file(os.path.join("files/count", "Tore Count.txt"))

        previous_severe_thunderstorm_warning_total_count = read_from_file(os.path.join("files/count", "SVR Total.txt"))
        previous_severe_thunderstorm_warning_count = read_from_file(os.path.join("files/count", "SVR Count.txt"))
        previous_considerable_svr_count = read_from_file(os.path.join("files/count", "SVR Considerable Count.txt"))
        previous_destructive_svr_count = read_from_file(os.path.join("files/count", "SVR Destructive Count.txt"))
        previous_tor_possible_svr_count = read_from_file(os.path.join("files/count", "SVR Possible Count.txt"))

        previous_tornado_watch_count = read_from_file(os.path.join("files/count", "TOR Watch Count.txt"))
        previous_severe_thunderstorm_watch_count = read_from_file(os.path.join("files/count", "SVR Watch Count.txt"))

        previous_flash_flood_warning_count = read_from_file(os.path.join("files/count", "FFW Count.txt"))
        previous_flash_flood_warning_total_count = read_from_file(os.path.join("files/count", "FFW Total.txt"))
        previous_considerable_ffw_count = read_from_file(os.path.join("files/count", "Considerable FFW Count.txt"))
        previous_ffe_count = read_from_file(os.path.join("files/count", "FFE Count.txt"))

        # Update count files only if the count has changed
        if tornado_warning_count != previous_tornado_warning_count:
            count_file_path = os.path.join('files/count', 'TOR Count.txt')
            write_to_file(count_file_path, str(tornado_warning_count))
            warnings_file_path = os.path.join('files/warnings', 'TOR.txt')
            write_to_file(warnings_file_path, f'Active Tornado Warnings: {tornado_warning_count}')

        if tornado_warning_total_count != previous_tornado_warning_total_count:
            count_file_path = os.path.join('files/count', 'TOR Total.txt')
            write_to_file(count_file_path, str(tornado_warning_total_count))
            warnings_file_path = os.path.join('files/warnings', 'TOR Total.txt')
            write_to_file(warnings_file_path, f'Active Tornado Warnings: {tornado_warning_total_count}')

        if torr_count != previous_torr_count:
            count_file_path = os.path.join('files/count', 'TOR Observed Count.txt')
            write_to_file(count_file_path, str(torr_count))
            warnings_file_path = os.path.join('files/warnings', 'TOR Observed.txt')
            write_to_file(warnings_file_path, f'Tornado Observations: {torr_count}')

        if pds_tor_count != previous_pds_tor_count:
            count_file_path = os.path.join('files/count', 'PDS TOR Count.txt')
            write_to_file(count_file_path, str(pds_tor_count))
            warnings_file_path = os.path.join('files/warnings', 'PDS TOR.txt')
            write_to_file(warnings_file_path, f'PDS Tornado Observations: {pds_tor_count}')

        if tore_count != previous_tore_count:
            count_file_path = os.path.join('files/count', 'TOR Emergancy Count.txt')
            write_to_file(count_file_path, str(tore_count))
            warnings_file_path = os.path.join('files/warnings', 'TOR Emergancy.txt')
            write_to_file(warnings_file_path, f'Tornado Emergancy Observations: {tore_count}')

        if severe_thunderstorm_warning_count != previous_severe_thunderstorm_warning_count:
            count_file_path = os.path.join('files/count', 'SVR Count.txt')
            write_to_file(count_file_path, str(severe_thunderstorm_warning_count))
            warnings_file_path = os.path.join('files/warnings', 'SVR.txt')
            write_to_file(warnings_file_path, f'Active Severe Thunderstorm Warnings: {severe_thunderstorm_warning_count}')

        if severe_thunderstorm_warning_total_count != previous_severe_thunderstorm_warning_total_count:
            count_file_path = os.path.join('files/count', 'SVR Total.txt')
            write_to_file(count_file_path, str(severe_thunderstorm_warning_total_count))
            warnings_file_path = os.path.join('files/warnings', 'SVR Total.txt')
            write_to_file(warnings_file_path, f'Active Severe Thunderstorm Warnings: {severe_thunderstorm_warning_total_count}')

        if considerable_svr_count != previous_considerable_svr_count:
            count_file_path = os.path.join('files/count', 'Considerable SVR Count.txt')
            write_to_file(count_file_path, str(considerable_svr_count))
            warnings_file_path = os.path.join('files/warnings', 'Considerable SVR.txt')
            write_to_file(warnings_file_path, f'Considerable SVR Warnings: {considerable_svr_count}')

        if destructive_svr_count != previous_destructive_svr_count:
            count_file_path = os.path.join('files/count', 'Destructive SVR Count.txt')
            write_to_file(count_file_path, str(destructive_svr_count))
            warnings_file_path = os.path.join('files/warnings', 'Destructive SVR.txt')
            write_to_file(warnings_file_path, f'Destructive SVR Warnings: {destructive_svr_count}')

        if tor_possible_svr_count != previous_tor_possible_svr_count:
            count_file_path = os.path.join('files/count', 'TOR SVR Count.txt')
            write_to_file(count_file_path, str(tor_possible_svr_count))
            warnings_file_path = os.path.join('files/warnings', 'TOR SVR.txt')
            write_to_file(warnings_file_path, f'TOR SVR Warnings: {tor_possible_svr_count}')

        if tornado_watch_count != previous_tornado_watch_count:
            count_file_path = os.path.join('files/count', 'TOR Watch Count.txt')
            write_to_file(count_file_path, str(tornado_watch_count))
            warnings_file_path = os.path.join('files/warnings', 'TOR Watch.txt')
            write_to_file(warnings_file_path, f'Tornado Watches: {tornado_watch_count}')

        if severe_thunderstorm_watch_count != previous_severe_thunderstorm_watch_count:
            count_file_path = os.path.join('files/count', 'SVR Watch Count.txt')
            write_to_file(count_file_path, str(severe_thunderstorm_watch_count))
            warnings_file_path = os.path.join('files/warnings', 'SVR Watch.txt')
            write_to_file(warnings_file_path, f'Severe Thunderstorm Watches: {severe_thunderstorm_watch_count}')

        if flash_flood_warning_count != previous_flash_flood_warning_count:
            count_file_path = os.path.join('files/count', 'FFW Count.txt')
            write_to_file(count_file_path, str(flash_flood_warning_count))
            warnings_file_path = os.path.join('files/warnings', 'FFW.txt')
            write_to_file(warnings_file_path, f'Flash Flood Warnings: {flash_flood_warning_count}')

        if flash_flood_warning_total_count != previous_flash_flood_warning_total_count:
            count_file_path = os.path.join('files/count', 'FFW Total.txt')
            write_to_file(count_file_path, str(flash_flood_warning_total_count))
            warnings_file_path = os.path.join('files/warnings', 'FFW Total.txt')
            write_to_file(warnings_file_path, f'Flash Flood Warnings: {flash_flood_warning_total_count}')

        if considerable_ffw_count != previous_considerable_ffw_count:
            count_file_path = os.path.join('files/count', 'Considerable FFW Count.txt')
            write_to_file(count_file_path, str(considerable_ffw_count))
            warnings_file_path = os.path.join('files/warnings', 'Considerable FFW.txt')
            write_to_file(warnings_file_path, f'Considerable Flash Flood Warnings: {considerable_ffw_count}')

        if ffe_count != previous_ffe_count:
            count_file_path = os.path.join('files/count', 'FFE Count.txt')
            write_to_file(count_file_path, str(ffe_count))
            warnings_file_path = os.path.join('files/warnings', 'FFE.txt')
            write_to_file(warnings_file_path, f'Flash Flood Emergencies: {ffe_count}')


def write_to_file(FILENAME, content1):  # skipcq: PYL-R1710
    """
    Writes content to a file.

    Parameters:
    filename (str): The name of the file to write to.
    content (str): The content to write to the file.

    Returns:
    None
    """
    # Fix the validation to properly handle the Warning info files
    valid_files = list(warning_count_files.keys()) + list(warning_files.keys()) + ["Warning Header.txt", "Warning Info.txt", "Warning Area.txt"]

    # Check if the filename is a full path
    if os.path.basename(FILENAME) in valid_files or FILENAME in valid_files:
        # Ensure directory exists for the file
        directory = os.path.dirname(FILENAME)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(FILENAME, "w") as file2:
            file2.write(content1 + "\n")
    else:
        return "Invalid filename"


def read_from_file(filename1):
    """
    Reads an integer from a file.

    Parameters:
    filename (str): The name of the file to read from.

    Returns:
    int: The integer read from the file. If the file does not exist or is empty, returns 0.
    """
    # Fix the validation to properly handle the Warning info files
    valid_files = list(warning_count_files.keys()) + list(warning_files.keys()) + ["Warning Header.txt", "Warning Info.txt", "Warning Area.txt"]

    # Check if the filename is a full path
    if os.path.basename(filename1) in valid_files or filename1 in valid_files:
        try:
            with open(filename1, "r") as file1:
                file_content = file1.read().strip()
                if file_content:
                    # Remove any null bytes or invalid characters before converting to int
                    cleaned_content = ''.join(char for char in file_content if char.isprintable())
                    try:
                        return int(cleaned_content)
                    except ValueError:
                        # If it's not an integer, return the string content
                        return cleaned_content
                return 0
        except FileNotFoundError:
            return 0
    else:
        return "Invalid filename"


def get_current_scene():
    """
    Retrieves the current scene from the OBS WebSocket.

    Returns:
        tuple: A tuple containing the name and scene UUID of the current scene.
    """
    # Connect to the OBS WebSocket
    ws = obsws(obs_socket_ip, obs_socket_port, obs_socket_password)
    ws.connect()
    current_scene = ws.call(obs_requests.GetCurrentProgramScene())
    ws.disconnect()
    return current_scene.get("name"), current_scene.get("sceneUuid")


def get_source_id(source_name, scene_name, scene_uuid):
    """
    Retrieves the source ID of a specific source in a given scene.

    Parameters:
        source_name (str): The name of the source to retrieve the ID for.
        scene_name (str): The name of the scene to search for the source in.
        scene_uuid (str): The UUID of the scene to search for the source in.

    Returns:
        str: The source ID of the specified source, or None if not found.
    """
    # Connect to the OBS WebSocket
    ws = obsws(obs_socket_ip, obs_socket_port, obs_socket_password)
    ws.connect()
    scene_items = ws.call(obs_requests.GetSceneItemList(sceneName=scene_name, sceneUuid=scene_uuid))
    for item in scene_items.get("sceneItems", []):
        if item["sourceName"] == source_name:
            ws.disconnect()
            return item["sourceItemId"]
    ws.disconnect()
    return None


def get_scene_and_source_info(source_name):
    """
    Retrieves the scene and source information for a given source name from the OBS WebSocket.

    Args:
        source_name (str): The name of the source to retrieve information for.

    Returns:
        tuple: A tuple containing the name, UUID, and scene item ID of the current scene and source if found,
               otherwise None, None, None.
    """
    if not obs_socket_ip or not obs_socket_port or not obs_socket_password:
        return None, None, None

    try:
        # Connect to the OBS WebSocket
        ws = obsws(obs_socket_ip, obs_socket_port, obs_socket_password)
        ws.connect()

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
                            ws.disconnect()
                            return current_scene_name, current_scene_uuid, item["sceneItemId"]
        ws.disconnect()
    except ImportError:
        pass

    return None, None, None


def fetch_alerts():
    """
    Fetches active weather alerts from the National Weather Service API.

    This function sends a GET request to the NWS API with parameters to filter
    the alerts by status, message type, code, region type, urgency, severity,
    certainty, and limit. It then processes the response and updates the
    database with new or updated alerts.

    Parameters:
        None

    Returns:
        None
    """
    endpoint = "https://api.weather.gov/alerts/active"
    params = {
        "status": "actual",
        "message_type": "alert,update",
        "code": 'TOR,TOA,SVR,SVA,FFW,SVS,SPS,SSW,HUW,TRW',
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

            # Convert properties dict to JSON string for database storage
            properties_json = json.dumps(properties)

            if not database.alert_exists(identifier, 'sent_alerts'):
                # This is a new alert
                event, notification_message, area_desc, expires_datetime, description = live_alerts_processing.process_alert(properties, area_desc)  # skipcq: FLK-E501  # skipcq: PYL-W0612
                if event in alerting_alerts:
                    display_alert(event, notification_message, area_desc)
                database.insert(identifier=identifier,
                                sent_datetime=sent_datetime,
                                expires_datetime=expires_datetime,
                                properties=properties_json,  # Use the JSON string instead of the dict
                                table_name='sent_alerts')
            else:
                existing_alert = database.get_alert(identifier, 'sent_alerts')
                existing_sent_datetime_str = existing_alert[1]

                # Convert existing_sent_datetime and existing_expires_datetime to UTC
                existing_sent_datetime = parser.parse(existing_sent_datetime_str).replace(tzinfo=tz.tzutc())

                if sent_datetime != existing_sent_datetime:
                    # This is an update to an existing alert
                    event, notification_message, area_desc, expires_datetime, description = live_alerts_processing.process_alert(properties, area_desc)  # skipcq: FLK-E501
                    if event in alerting_alerts:
                        display_alert(event, notification_message, area_desc)
                    database.update(identifier=identifier,
                                    sent_datetime=sent_datetime,
                                    expires_datetime=expires_datetime,
                                    properties=properties_json,  # Use the JSON string instead of the dict
                                    table_name='sent_alerts')
    update_active_alerts()


def update_active_alerts_and_exit():
    """
    Updates active alerts and exits the application.

    This function calls the update_active_alerts function to refresh the active alerts before exiting.

    Parameters:
        None

    Returns:
        None
    """
    update_active_alerts()


def display_alert(event, notification_message, area_desc):
    """
    Displays a weather alert notification and updates the OBS scene accordingly.

    Parameters:
        event (str): The type of weather event (e.g., tornado, severe thunderstorm).
        notification_message (str): The message to be displayed in the notification.
        area_desc (str): The area affected by the weather event.

    Returns:
        None
    """
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

    # Create files directory if it doesn't exist
    if not os.path.exists('files'):
        os.makedirs('files')

    # Write the headline to the Warning Header.txt file with full paths
    write_to_file(os.path.join("files", "Warning Header.txt"), event)
    write_to_file(os.path.join("files", "Warning Info.txt"), notification_message)
    write_to_file(os.path.join("files", "Warning Area.txt"), area_desc)

    time.sleep(2)

    # Connect to the OBS WebSocket
    ws = obsws(obs_socket_ip, obs_socket_port, obs_socket_password)
    ws.connect()

    source_name = obs_source_settings.get(event)
    if source_name:  # Check if source_name is not None
        scene_name, scene_uuid, scene_item_id = get_scene_and_source_info(source_name)
        if all((scene_name, scene_uuid, scene_item_id)):  # Check if we got all the values
            ws.call(obs_requests.SetSceneItemEnabled(sceneName=scene_name, sceneUuid=scene_uuid, sceneItemId=scene_item_id, sceneItemEnabled=True))
            time.sleep(5)
            ws.call(obs_requests.SetSceneItemEnabled(sceneName=scene_name, sceneUuid=scene_uuid, sceneItemId=scene_item_id, sceneItemEnabled=False))
        else:
            print(f"Could not find source '{source_name}' in the current scene.")
    else:
        print(f"No OBS source configured for event type: {event}")

    time.sleep(3)
    ws.disconnect()


atexit.register(update_active_alerts_and_exit)


def kickstart(stop_event):
    """
    Initializes the alert system by creating the necessary database table, clearing any existing data, and starting the alert fetching process.

    Parameters:
        stop_event (threading.Event): An event object used to signal the function to stop its execution.

    Returns:
        None
    """
    while not stop_event.is_set():
        fetch_alerts()
        time.sleep(5)  # Wait for 5 seconds before checking for new alerts

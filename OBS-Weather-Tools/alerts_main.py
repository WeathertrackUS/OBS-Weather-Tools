import os
import requests
from obswebsocket import obsws, requests as obs_requests
import time
from obswebsocket.exceptions import ConnectionFailure
import sqlite3  # Add SQLite for tracking processed alerts
import threading


# OBS WebSocket settings
obs_socket_ip = "192.168.4.78"
obs_socket_port = 4455
obs_socket_password = "VJFfpubelSgccfYR"

# OBS Source Settings
obs_source_settings = {
    "Warning Feed": "Warning-Feed"
}

# Global list to store active alerts
active_alerts = []
current_alert_index = 0  # Pointer to track the current alert being displayed


def get_current_scene():
    """
    Retrieves the current scene from the OBS WebSocket.

    Returns:
        tuple: A tuple containing the name and scene UUID of the current scene.
    """
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
        ws = obsws(obs_socket_ip, obs_socket_port, obs_socket_password)
        ws.connect()

        scene_response = ws.call(obs_requests.GetSceneList())
        response_dict = scene_response.__dict__

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


if not os.path.exists("files/headerText"):
    os.mkdir("files/headerText")
if not os.path.exists("files/descText"):
    os.mkdir("files/descText")

header_files = {
    'header1Text.txt': '',
}

desc_files = {
    'desc1Text.txt': '',
}

for filename, content in header_files.items():
    file_path = os.path.join('files/headerText', filename)
    with open(file_path, 'w') as file:
        file.write(content)

for filename, content in desc_files.items():
    file_path = os.path.join('files/descText', filename)
    with open(file_path, 'w') as file:
        file.write(content)


def write_to_file(filename1, content2):  # skipcq: PYL-R1710
    """
    Writes content to a file.

    Parameters:
        filename (str): The name of the file to write to.
        content (str): The content to write to the file.

    Returns:
        None
    """
    valid_files = {
        "header1Text.txt": "files/headerText/header1Text.txt",
        "desc1Text.txt": "files/descText/desc1Text.txt"
    }

    if filename1 not in valid_files:
        print(f"Invalid filename: {filename1}")
        return "Invalid filename"

    file_path = valid_files[filename1]
    try:
        with open(file_path, "w") as file2:
            file2.write(content2 + "\n")
        print(f"Successfully wrote to {file_path}: {content2}")
    except Exception as e:
        print(f"Error writing to file {file_path}: {e}")


def read_from_file(FILENAME):
    """
    Reads content from a file and returns it as a string, stripping any non-printable characters.

    Parameters:
        filename (str): The name of the file to read from.

    Returns:
        str: The content of the file as a string if the file exists and is not empty, otherwise 0.
    """
    if FILENAME not in ("header1Text.txt", "desc1Text.txt"):
        return "Invalid filename"

    try:
        with open(FILENAME, "r") as file1:
            content1 = file1.read().strip()
            if content1:
                cleaned_content = ''.join(char for char in content1 if char.isprintable())
                return cleaned_content
            return 0
    except (FileNotFoundError, ValueError):
        return 0


endpoint = "https://api.weather.gov/alerts/active"
params = {
    "status": "actual",
    "message_type": "alert,update",
    "code": 'TOR,SVR,FFW,SVS,SMW,HUW,TRW,SSW',
    "region_type": "land",
    "urgency": "Immediate,Future,Expected",
    "severity": "Extreme,Severe,Moderate",
    "certainty": "Observed,Likely,Possible",
    "limit": 500
}

response = requests.get(endpoint, params=params)


# Initialize SQLite database to track processed alerts
def initialize_database():
    """
    Initializes the SQLite database to track processed alerts.
    """
    conn = sqlite3.connect("alerts.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS processed_alerts (id TEXT PRIMARY KEY)""")
    conn.commit()
    conn.close()


def is_alert_processed(alert_id):
    """
    Checks if an alert has already been processed.

    Parameters:
        alert_id (str): The unique ID of the alert.

    Returns:
        bool: True if the alert has been processed, False otherwise.
    """
    conn = sqlite3.connect("alerts.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM processed_alerts WHERE id = ?", (alert_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def mark_alert_as_processed(alert_id):
    """
    Marks an alert as processed by adding its ID to the database.

    Parameters:
        alert_id (str): The unique ID of the alert.
    """
    conn = sqlite3.connect("alerts.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO processed_alerts (id) VALUES (?)", (alert_id,))
    conn.commit()
    conn.close()


def fetch_alerts(stop_event):
    """
    Fetches weather alerts and replaces the global active_alerts list.

    This function periodically fetches alerts and replaces the list with new ones.

    Parameters:
        stop_event (threading.Event): An event that signals the function to stop.

    Returns:
        None
    """
    global active_alerts
    while not stop_event.is_set():
        if response.status_code == 200:
            data = response.json()
            features = data["features"]

            new_alerts = []
            for feature in features:
                alert_id = feature["id"]  # Each alert has a unique ID
                if is_alert_processed(alert_id):
                    continue  # Skip already processed alerts

                properties = feature["properties"]
                event = properties["event"]
                description = properties["description"]
                areadesc = properties["areaDesc"]
                instruction = properties["instruction"]

                headline = properties.get("headline", "")
                warning_text = (
                    f'{headline} for {areadesc}. Protective Actions: {instruction}'
                    if headline
                    else f'{description}   Protective Actions: {instruction}'
                )

                new_alerts.append({"id": alert_id, "event": event, "warning_text": warning_text})
                mark_alert_as_processed(alert_id)  # Mark the alert as processed

            # Replace the global active_alerts list with the new alerts
            active_alerts = new_alerts

        else:
            print(f"Failed to fetch alerts: {response.status_code}")

        time.sleep(300)  # Wait for 5 minutes before fetching alerts again


def iterate_alerts(stop_event):
    """
    Iterates through the active alerts list and displays each alert in a loop.

    Parameters:
        stop_event (threading.Event): An event that signals the function to stop.

    Returns:
        None
    """
    global active_alerts, current_alert_index
    while not stop_event.is_set():
        if active_alerts:
            # Get the current alert
            alert = active_alerts[current_alert_index]
            event = alert["event"]
            warning_text = alert["warning_text"]

            # Process and display the alert
            processing(event, warning_text)

            # Move to the next alert
            current_alert_index = (current_alert_index + 1) % len(active_alerts)
        else:
            print("No active alerts to display.")
            current_alert_index = 0  # Reset the index when the list is empty
            time.sleep(5)  # Wait before checking again


def processing(event, warning_text):
    """
    Processes a weather alert event and warning text by writing them to file and displaying a warning feed.

    Parameters:
        event (str): The weather alert event.
        warning_text (str): The warning text associated with the event.

    Returns:
        None
    """
    print(f"Processing event: {event}")
    write_result = write_to_file("header1Text.txt", event)
    if write_result == "Invalid filename":
        print("Failed to write event to header file.")
    else:
        print(f"Event written to header file: {event}")

    single_line_warning = ' '.join(warning_text.split())
    write_result = write_to_file("desc1Text.txt", f"{single_line_warning}   ")
    if write_result == "Invalid filename":
        print("Failed to write warning text to description file.")
    else:
        print(f"Warning text written to description file: {single_line_warning}")

    time.sleep(2)

    display("Warning Feed")


def display(source):
    """
    Displays a specified source in OBS by enabling and disabling the corresponding scene item.

    Parameters:
        source (str): The name of the source to display.

    Returns:
        None
    """
    try:
        ws = obsws(obs_socket_ip, obs_socket_port, obs_socket_password)
        ws.connect()

        source_name = obs_source_settings.get(source)
        scene_name, scene_uuid, scene_item_id = get_scene_and_source_info(source_name)

        ws.call(obs_requests.SetSceneItemEnabled(sceneName=scene_name, sceneUuid=scene_uuid, sceneItemId=scene_item_id, sceneItemEnabled=True))
        time.sleep(15)
        ws.call(obs_requests.SetSceneItemEnabled(sceneName=scene_name, sceneUuid=scene_uuid, sceneItemId=scene_item_id, sceneItemEnabled=False))

        ws.disconnect()
    except obsws.exceptions.ConnectionFailure as e:
        print(f"OBS WebSocket connection failed: {e}")
        time.sleep(5)  # Retry after a delay


def kickstart(stop_event):
    """
    Initializes the alert fetching and scrolling process.

    Parameters:
        stop_event (threading.Event): An event object used to signal the function to stop its execution.

    Returns:
        None
    """
    # Initialize the database
    initialize_database()

    fetch_thread = threading.Thread(target=fetch_alerts, args=(stop_event,))
    iterate_thread = threading.Thread(target=iterate_alerts, args=(stop_event,))

    # Start the threads
    fetch_thread.start()
    iterate_thread.start()
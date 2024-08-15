import os
from dateutil import parser
import pytz
import requests
from obswebsocket import obsws, requests as obs_requests
import time


# OBS WebSocket settings
obs_socket_ip = "216.16.115.246"
obs_socket_port = 4455
obs_socket_password = "VJFfpubelSgccfYR"

# OBS Source Settings
obs_source_settings = {
    "Warning Feed": "Warning-Feed"
}


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


def write_to_file(filename1, content2):
    """
    Writes content to a file.

    Parameters:
        filename (str): The name of the file to write to.
        content (str): The content to write to the file.

    Returns:
        None
    """
    with open(filename1, "w") as file2:
        file2.write(content2 + "\n")


def read_from_file(FILENAME):
    """
    Reads content from a file and returns it as a string, stripping any non-printable characters.

    Parameters:
        filename (str): The name of the file to read from.

    Returns:
        str: The content of the file as a string if the file exists and is not empty, otherwise 0.
    """
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
    "code": 'TOR,SVR,FFW,SVS',
    "region_type": "land",
    "urgency": "Immediate,Future,Expected",
    "severity": "Extreme,Severe,Moderate",
    "certainty": "Observed,Likely,Possible",
    "limit": 500
}

response = requests.get(endpoint, params=params)


def fetch_alerts(stop_event):
    """
    Fetches and processes weather alerts from a given response.

    This function continuously checks for new alerts until the stop event is set.
    It processes each alert by extracting relevant information such as the event,
    description, instruction, and headline. The alert is then passed to the
    processing function for further handling.

    Parameters:
        stop_event (threading.Event): An event that signals the function to stop.

    Returns:
        None
    """
    while not stop_event.is_set():
        if response.status_code == 200:
            data = response.json()
            features = data["features"]

            if alert in features:
                for alert in features:
                    while not stop_event.is_set():
                        properties = alert["properties"]

                        event = properties["event"]
                        description = properties["description"]
                        instruction = properties["instruction"]
                        sent = properties["sent"]

                        parameters = properties["parameters"]
                        headline = parameters["NWSheadline"]

                        sent_datetime = parser.parse(sent).astimezone(pytz.utc)

                        if headline:
                            warning_text = f'{headline}   {description}   Protective Actions: {instruction}'
                        else:
                            warning_text = f'{description}   Protective Actions: {instruction}'

                        processing(event, warning_text)
            else:
                pass
        else:
            pass


def processing(event, warning_text):
    """
    Processes a weather alert event and warning text by writing them to file and displaying a warning feed.

    Parameters:
        event (str): The weather alert event.
        warning_text (str): The warning text associated with the event.

    Returns:
        None
    """
    write_to_file("files/headerText/header1Text.txt", event)
    single_line_warning = ' '.join(warning_text.split())
    write_to_file("files/descText/desc1Text.txt", f"{single_line_warning}   ")

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
    ws = obsws(obs_socket_ip, obs_socket_port, obs_socket_password)
    ws.connect()

    source_name = obs_source_settings.get(source)
    scene_name, scene_uuid, scene_item_id = get_scene_and_source_info(source_name)

    ws.call(obs_requests.SetSceneItemEnabled(sceneName=scene_name, sceneUuid=scene_uuid, sceneItemId=scene_item_id, sceneItemEnabled=True))
    time.sleep(180)
    ws.call(obs_requests.SetSceneItemEnabled(sceneName=scene_name, sceneUuid=scene_uuid, sceneItemId=scene_item_id, sceneItemEnabled=False))

    ws.disconnect()


def kickstart(stop_event):
    """
    Initializes the alert fetching process and runs it indefinitely until the stop event is triggered.

    Parameters:
        stop_event (threading.Event): An event object used to signal the function to stop its execution.

    Returns:
        None
    """
    while not stop_event.is_set():
        fetch_alerts(stop_event)

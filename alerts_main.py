import os
from dateutil import parser, tz
import pytz
import requests
from obswebsocket import obsws, requests as obs_requests
import time


# OBS WebSocket settings
obs_socket_ip = "216.16.96.60"  
obs_socket_port = 4455  
obs_socket_password = "VJFfpubelSgccfYR" 

# OBS Source Settings
obs_source_settings = {
    "Warning Feed": "Warning-Feed"
}

def get_current_scene():
    ws = obsws(obs_socket_ip, obs_socket_port, obs_socket_password)
    ws.connect()
    current_scene = ws.call(obs_requests.GetCurrentProgramScene())
    ws.disconnect()
    return current_scene.get("name"), current_scene.get("sceneUuid")

def get_source_id(source_name, scene_name, scene_uuid):
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
                    

if not os.path.exists("headerText"):
    os.mkdir("headerText")
if not os.path.exists("descText"):
    os.mkdir("descText")

header_files = {
    'header1Text.txt': '',
}

desc_files = {
    'desc1Text.txt': '',
}

for filename, content in header_files.items():
    file_path = os.path.join('headerText', filename)
    with open(file_path, 'w') as file:
        file.write(content)

for filename, content in desc_files.items():
    file_path = os.path.join('descText', filename)
    with open(file_path, 'w') as file:
        file.write(content)

def write_to_file(filename, content):
    with open(filename, "w") as file:
        file.write(content + "\n")

def read_from_file(filename):
    try:
        with open(filename, "r") as file:
            content = file.read().strip()
            if content:
                cleaned_content = ''.join(char for char in content if char.isprintable())
                return cleaned_content
            else:
                return 0
    except(FileNotFoundError, ValueError):
        return 0


endpoint = "https://api.weather.gov/alerts/active"
params = {
    "status": "actual",
    "message_type": "alert,update",
    "code": 'TOR,TOA,SVR,SVA,FFW,SVS,SPS',
    "region_type": "land",
    "urgency": "Immediate,Future,Expected",
    "severity": "Extreme,Severe,Moderate",
    "certainty": "Observed,Likely,Possible",
    "limit": 500
}

response = requests.get(endpoint, params=params)

def fetch_alerts():
    while True:
        if response.status_code == 200:
            data = response.json()
            features = data["features"]

            for alert in features:
                properties = alert["properties"]

                event = properties["event"]
                identifier = properties["id"]
                description = properties["description"]
                instruction = properties["instruction"]
                sent = properties["sent"]

                sent_datetime = parser.parse(sent).astimezone(pytz.utc)

                warning_text = (f'{description}   Protective Actions: {instruction}')

                processing(event, warning_text)

def processing(event, warning_text):
    write_to_file("headerText/header1Text.txt", event)
    single_line_warning = ' '.join(warning_text.split())
    write_to_file("descText/desc1Text.txt", f"{single_line_warning}   ")

    time.sleep(2)

    display("Warning Feed")



def display(source):
    ws = obsws(obs_socket_ip, obs_socket_port, obs_socket_password)
    ws.connect()

    source_name = obs_source_settings.get(source)
    scene_name, scene_uuid, scene_item_id = get_scene_and_source_info(source_name)

    ws.call(obs_requests.SetSceneItemEnabled(sceneName=scene_name, sceneUuid=scene_uuid, sceneItemId=scene_item_id, sceneItemEnabled=True))
    time.sleep(180)
    print('time')
    ws.call(obs_requests.SetSceneItemEnabled(sceneName=scene_name, sceneUuid=scene_uuid, sceneItemId=scene_item_id, sceneItemEnabled=False))

    ws.disconnect()

def kickstart(stop_event):
    while not stop_event.is_set():
        fetch_alerts(stop_event)

fetch_alerts()
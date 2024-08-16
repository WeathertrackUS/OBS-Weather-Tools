# alerts.py
from datetime import datetime

MAX_MESSAGE_LENGTH = 256


def process_alert(properties, area_desc):
    """
    Process a weather alert and extract relevant information.

    Parameters:
    identifier (str): Unique identifier for the alert.
    properties (dict): Dictionary containing alert properties.
    sent_datetime (datetime): Date and time the alert was sent.
    area_desc (str): Description of the affected area.

    Returns:
    event (str): Type of weather event.
    notification_message (str): Formatted message for notification.
    area_desc (str): Description of the affected area.
    expires_datetime (datetime): Date and time the alert expires.
    description (str): Detailed description of the alert.
    """
    headline = properties["headline"]
    description = ''
    event = properties["event"]

    thunderstorm_damage_threat = properties.get("parameters", {}).get("thunderstormDamageThreat")
    tornado_damage_threat = properties.get("parameters", {}).get("tornadoDamageThreat")
    tornado_detection = properties.get("parameters", {}).get("tornadoDetection")
    flash_flood_damage_threat = properties.get("parameters", {}).get("flashFloodDamageThreat")

    if properties['messageType'] == 'Update':
        description += 'UPDATE'

    # Check if the "thunderstormDamageThreat" tag is present
    if thunderstorm_damage_threat:
        description += f", Thunderstorm Damage Threat: {(thunderstorm_damage_threat)}"

    if tornado_damage_threat:
        description += f", Tornado Damage Threat: {(tornado_damage_threat)}"

    if tornado_detection:
        description += f", Tornado Detection: {(tornado_detection)}"

    if flash_flood_damage_threat:
        description += f", Flash Flood Damage Threat: {(flash_flood_damage_threat)}"

    if description != '':
        notification_message = f"{headline}, {description}"
    else:
        notification_message = f"{headline}"

    if len(notification_message) > MAX_MESSAGE_LENGTH:
        notification_message = notification_message[:MAX_MESSAGE_LENGTH - 3] + "..."

    # Get the expiration time from the properties
    expires_datetime = datetime.strptime(properties["expires"], "%Y-%m-%dT%H:%M:%S%z")

    return event, notification_message, area_desc, expires_datetime, description

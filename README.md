# OBS-Weather-Tools

OBS-Weather-Tools is a comprehensive system for fetching, processing, and displaying weather alerts in OBS (Open Broadcaster Software). It integrates with the National Weather Service API to provide real-time weather information and alerts.

## Features

- Fetches active weather alerts from the National Weather Service API
- Processes and categorizes various types of weather alerts (Tornado, Severe Thunderstorm, Flash Flood, etc.)
- Displays alerts in OBS scenes
- Maintains a count of different types of weather warnings
- Provides a dashboard for viewing active alerts
- Integrates with OBS via WebSocket for scene and source management

## Setup

1. Install required dependencies:
    pip install -r requirements.txt

2. Configure OBS WebSocket settings in the script (obs_socket_ip, obs_socket_port, obs_socket_password)

3. Set up necessary OBS scenes and sources as referenced in the code

## Usage

Run the main script:
    python main.py

This will start the alert fetching and processing system. The script will run in the background, updating OBS scenes and sources as new alerts come in or existing ones expire.

## Components

- `live_alert_main.py`: Main script that orchestrates the alert fetching and processing
- `live_alerts_processing.py`: Handles the processing of individual alerts
- `live_alert_dashboard.py`: Provides a dashboard view of active alerts
- `alerts_main.py`: Contains utility functions for OBS scene and source management

## Notes

- The system uses a SQLite database to store alert information
- Alert counts are stored in text files in a 'count' directory
- The system can be minimized to the system tray for background operation

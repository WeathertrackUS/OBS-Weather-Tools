# Main.py

from live_alert_main import kickstart
from live_alert_dashboard import dashboard_kickstart
import tkinter
import customtkinter as ctk
import threading
import spc_outlook
import database
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging.debug("Starting OBS Weather Tools main.py")

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.geometry("540x800")
root.title("OBS Weather Tools")

main_frame = ctk.CTkFrame(master=root)
main_frame.grid(row=0, column=0, padx=10, pady=10)

alerts_thread = None
dashboard_thread = None

live_alert_stop_event = threading.Event()
dashboard_stop_event = threading.Event()
alert_stop_event = threading.Event()

live_alert_var = tkinter.BooleanVar()
dashboard_var = tkinter.BooleanVar()
spc_outlook_var = tkinter.BooleanVar()
alert_scroll_var = tkinter.BooleanVar()


def update_dashboard_state(*args):
    """
    Updates the state of the dashboard checkbox based on the value of the live_alert_var.

    Parameters:
        *args: Variable length argument list.

    Returns:
        None
    """
    if live_alert_var.get():
        dashboard_checkbox.configure(state="normal")
    else:
        dashboard_checkbox.configure(state="disabled")
        dashboard_var.set(False)


def start_dashboard():
    """
    Starts the dashboard thread if it is not already running.

    Parameters:
        None

    Returns:
        None
    """
    global dashboard_thread  # skipcq: PYL-W0603  # skipcq: PYL-W0601
    if dashboard_thread is None or not dashboard_thread.is_alive():
        dashboard_thread = threading.Thread(target=dashboard_kickstart, args=(dashboard_stop_event,))
        dashboard_thread.start()


def stop_dashboard():
    """
    Stops the dashboard thread if it is currently running.

    Parameters:
        None

    Returns:
        None
    """
    if dashboard_thread and dashboard_thread.is_alive():
        dashboard_thread._stop()  # skipcq: PYL-W0212


def enable_alert_scroll():
    """
    Enables the new alert scroll (beta) by starting the Flask webserver.

    Parameters:
        None

    Returns:
        None
    """
    import subprocess
    subprocess.Popen(['python', 'webserver.py'], cwd='e:\\OBS-Weather-Tools\\obs-weather-tools')


def confirm_action():
    """
    Confirms the current action based on the state of the live alert,
    dashboard, alert, and alert scroll variables.

    It checks the state of the live alert variable
    and starts or stops the live alerts thread accordingly.

    It also checks the state of the dashboard variable
    and starts or stops the dashboard thread.

    Finally, it checks the state of the alert variable
    and starts or stops the alerts thread.

    Parameters:
        None

    Returns:
        None
    """
    logging.debug("Confirm action called.")
    if live_alert_var.get():
        if not alerts_thread or not alerts_thread.is_alive():  # skipcq: PYL-E0601
            alert_stop_event.clear()
            live_alerts_thread = threading.Thread(target=kickstart, args=(alert_stop_event,))
            live_alerts_thread.start()
    else:
        alert_stop_event.set()
        dashboard_stop_event.set()
        dashboard_var.set(False)

    if dashboard_var.get():
        start_dashboard()
    else:
        dashboard_stop_event.set()

    if spc_outlook_var.get():
        spc_outlook.kickstart()

    if alert_scroll_var.get():
        logging.debug("Alert scroll (Beta) enabled.")
        enable_alert_scroll()


live_alert_checkbox = ctk.CTkCheckBox(main_frame, text="Alert Monitor", variable=live_alert_var, command=update_dashboard_state)
live_alert_checkbox.grid(row=0, column=0, padx=10, pady=10)

dashboard_checkbox = ctk.CTkCheckBox(main_frame, text="Dashboard", variable=dashboard_var, state="disabled")
dashboard_checkbox.grid(row=1, column=0, padx=10, pady=10)

spcoutlook_checkbox = ctk.CTkCheckBox(main_frame, text="SPC Outlook", variable=spc_outlook_var)
spcoutlook_checkbox.grid(row=3, column=0, padx=10, pady=10)

alert_scroll_checkbox = ctk.CTkCheckBox(main_frame, text="Alert Scroll (Beta)", variable=alert_scroll_var)
alert_scroll_checkbox.grid(row=4, column=0, padx=10, pady=10)

confirm_button = ctk.CTkButton(main_frame, text="Confirm", command=confirm_action)
confirm_button.grid(row=5, column=0, padx=10, pady=10)

live_alert_var.trace_add("write", update_dashboard_state)

database.create_table('sent_alerts', '(id TEXT PRIMARY KEY, sent_datetime TEXT, expires_datetime TEXT, properties TEXT)')

root.mainloop()

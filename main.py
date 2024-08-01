# Main.py

from alert_main import kickstart
from alert_dashboard import dashboard_kickstart
import tkinter
import customtkinter as ctk
import threading
import multiprocessing

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.geometry("540x800")
root.title("OBS Weather Tools")

main_frame = ctk.CTkFrame(master=root)
main_frame.grid(row=0, column=0, padx=10, pady=10)

alert_stop_event = threading.Event()
dashboard_stop_event = threading.Event()

alerts_thread = None
dashboard_thread = None

alert_var = tkinter.BooleanVar()
dashboard_var = tkinter.BooleanVar()

def update_dashboard_state(*args):
    if alert_var.get():
        dashboard_checkbox.configure(state="normal")
    else:
        dashboard_checkbox.configure(state="disabled")
        dashboard_var.set(False)

alert_checkbox = ctk.CTkCheckBox(main_frame, text="Alert Monitor", variable=alert_var, command=update_dashboard_state)
alert_checkbox.grid(row=0, column=0, padx=10, pady=10)

dashboard_checkbox = ctk.CTkCheckBox(main_frame, text="Dashboard", variable=dashboard_var, state="disabled")
dashboard_checkbox.grid(row=1, column=0, padx=10, pady=10)

def start_dashboard():
    global dashboard_thread
    if dashboard_thread is None or not dashboard_thread.is_alive():
        dashboard_thread = threading.Thread(target=dashboard_kickstart, args=(dashboard_stop_event,))
        dashboard_thread.start()

def stop_dashboard():
    global dashboard_thread
    if dashboard_thread and dashboard_thread.is_alive():
        dashboard_thread._stop()

def confirm_action():
    global alerts_thread

    if alert_var.get():
        if not alerts_thread or not alerts_thread.is_alive():
            alert_stop_event.clear()
            alerts_thread = threading.Thread(target=kickstart, args=(alert_stop_event,))
            alerts_thread.start()
    else:
        alert_stop_event.set()
        dashboard_stop_event.set()
        dashboard_var.set(False)

    if dashboard_var.get():
        start_dashboard()
    else:
        dashboard_stop_event.set()

confirm_button = ctk.CTkButton(main_frame, text="Confirm", command=confirm_action)
confirm_button.grid(row=2, column=0, padx=10, pady=10)

alert_var.trace_add("write", update_dashboard_state)

root.mainloop()

# Main.py

from alert_main import kickstart
import tkinter
import customtkinter as ctk

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.geometry("540x800")
root.title("OBS Weather Tools")

main_frame = ctk.CTkFrame(master=root)
main_frame.grid(row=0, column=0, padx=10, pady=10)

test_button = ctk.CTkButton(main_frame, text="Alert Monitor", command=kickstart)
test_button.grid(row=0, column=0, padx=10, pady=10)

root.mainloop()
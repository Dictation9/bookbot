import customtkinter as ctk

def get_tab(parent):
    frame = ctk.CTkFrame(parent)
    ctk.CTkLabel(frame, text="Log Viewer Frame - Log file content will be here.", text_color="black").pack(pady=20)
    return {"name": "Log Viewer", "frame": frame} 
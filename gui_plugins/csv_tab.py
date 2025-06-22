import customtkinter as ctk

def get_tab(parent):
    frame = ctk.CTkFrame(parent)
    ctk.CTkLabel(frame, text="CSV Viewer Frame - Data table will be here.", text_color="black").pack(pady=20)
    return {"name": "CSV Viewer", "frame": frame} 
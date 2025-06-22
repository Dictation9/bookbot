import customtkinter as ctk

def get_tab(parent):
    frame = ctk.CTkFrame(parent)
    ctk.CTkLabel(frame, text="Configuration Frame - Settings editor will be here.", text_color="black").pack(pady=20)
    return {"name": "Configuration", "frame": frame, "top_level": True} 
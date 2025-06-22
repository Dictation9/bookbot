import customtkinter as ctk

def get_tab(parent):
    frame = ctk.CTkFrame(parent)
    label = ctk.CTkLabel(frame, text="This is a sample plugin tab!", text_color="black")
    label.pack(padx=20, pady=20)
    return {"name": "Sample Tab", "frame": frame} 
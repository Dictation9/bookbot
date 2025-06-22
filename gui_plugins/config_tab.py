import customtkinter as ctk
import configparser
import os
from gui_plugins.scrollable_frame import ScrollableFrame

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")


def get_tab(parent):
    return {"name": "Configuration", "frame": ConfigTab(parent).frame, "top_level": True, "position": 2}

class ConfigTab:
    def __init__(self, parent):
        self.frame = ScrollableFrame(parent, width=900, height=700)
        self.inner = self.frame.inner
        self.entries = {}  # (section, option): entry
        self.load_config()
    def load_config(self):
        # Clear previous widgets
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.entries = {}
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        row = 0
        for section in config.sections():
            ctk.CTkLabel(self.inner, text=f"[{section}]", text_color="black", font=ctk.CTkFont(weight="bold", size=15)).grid(row=row, column=0, sticky="w", pady=(10,2))
            row += 1
            for option in config[section]:
                ctk.CTkLabel(self.inner, text=option, text_color="black").grid(row=row, column=0, sticky="e", padx=5, pady=2)
                entry = ctk.CTkEntry(self.inner, width=400)
                entry.insert(0, config[section][option])
                entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                self.entries[(section, option)] = entry
                row += 1
        # Place Save/Reload buttons at the next available row
        btn_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10, sticky="w")
        self.save_button = ctk.CTkButton(btn_frame, text="Save Changes", command=self.save_config, text_color="black")
        self.save_button.pack(side="left", padx=10)
        self.reload_button = ctk.CTkButton(btn_frame, text="Reload", command=self.reload_config, text_color="black")
        self.reload_button.pack(side="left", padx=10)
    def save_config(self):
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        for (section, option), entry in self.entries.items():
            if not config.has_section(section):
                config.add_section(section)
            config[section][option] = entry.get()
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            config.write(f)
    def reload_config(self):
        self.load_config() 
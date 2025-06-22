import customtkinter as ctk
import configparser
import os
from gui_plugins.scrollable_frame import ScrollableFrame

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")


def get_tab(parent):
    return {"name": "Configuration", "frame": ConfigTab(parent).frame, "top_level": True, "position": 2}

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)
    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tw, text=self.text, text_color="black", fg_color="white", corner_radius=5, font=ctk.CTkFont(size=12))
        label.pack(ipadx=6, ipady=2)
    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class ConfigTab:
    def __init__(self, parent):
        self.frame = ScrollableFrame(parent, always_show_scrollbar=True)
        self.inner = self.frame.inner
        self.entries = {}  # (section, option): entry
        self.hints = self.parse_hints()
        self.load_config()
    def parse_hints(self):
        # Parse config.ini for comments and map them to (section, option)
        hints = {}
        current_section = None
        last_comments = []
        with open(CONFIG_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("[") and "]" in line:
                    # Support inline section comments
                    if "#" in line:
                        section_part, comment_part = line.split("#", 1)
                        current_section = section_part.strip("[] ")
                        last_comments = [comment_part.strip()]
                    else:
                        current_section = line[1:line.index("]")]
                        last_comments = []
                elif line.startswith("#"):
                    last_comments.append(line[1:].strip())
                elif "=" in line and current_section:
                    option = line.split("=", 1)[0].strip()
                    if last_comments:
                        hint = " ".join(last_comments)
                        hints[(current_section, option)] = hint
                        last_comments = []
        return hints
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
                hint = self.hints.get((section, option), "Fill in this value if unsure. Hover for more info.")
                ToolTip(entry, hint)
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
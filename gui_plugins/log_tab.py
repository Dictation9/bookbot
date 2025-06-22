import customtkinter as ctk
import os
from gui_plugins.scrollable_frame import ScrollableFrame

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
DEFAULT_LOGS = ["bot.log", "comment_data.log", "cron.log"]


def get_tab(parent):
    return {"name": "Log Viewer", "frame": LogTab(parent).frame, "top_level": True, "position": 4}

class LogTab:
    def __init__(self, parent):
        self.frame = ScrollableFrame(parent, always_show_scrollbar=True)
        self.inner = self.frame.inner
        self.log_files = self.get_log_files()
        self.selected_log = ctk.StringVar(value=self.log_files[0] if self.log_files else "")
        self.dropdown = ctk.CTkOptionMenu(self.inner, values=self.log_files, variable=self.selected_log, command=self.load_log)
        self.dropdown.pack(pady=10)
        self.reload_button = ctk.CTkButton(self.inner, text="Reload", command=self.reload_log, text_color="black")
        self.reload_button.pack(pady=2)
        self.log_textbox = ctk.CTkTextbox(self.inner, width=800, height=500, font=ctk.CTkFont(size=12), text_color="black")
        self.log_textbox.pack(pady=10)
        self.log_textbox.configure(state="disabled")
        if self.log_files:
            self.load_log(self.selected_log.get())
    def get_log_files(self):
        if not os.path.isdir(LOGS_DIR):
            return []
        files = [f for f in os.listdir(LOGS_DIR) if f.endswith('.log')]
        # Always show default logs if present, then any others
        ordered = [f for f in DEFAULT_LOGS if f in files]
        for f in files:
            if f not in ordered:
                ordered.append(f)
        return ordered
    def load_log(self, log_name):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        log_path = os.path.join(LOGS_DIR, log_name)
        if os.path.exists(log_path):
            with open(log_path, encoding="utf-8", errors="replace") as f:
                self.log_textbox.insert("end", f.read())
        else:
            self.log_textbox.insert("end", f"Log file not found: {log_name}")
        self.log_textbox.configure(state="disabled")
    def reload_log(self):
        self.load_log(self.selected_log.get()) 
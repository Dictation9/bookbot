import customtkinter as ctk
from gui_plugins.scrollable_frame import ScrollableFrame
import subprocess
import os
import sys
import threading
import shutil

def get_tab(parent):
    return {"name": "Admin", "frame": AdminTab(parent).frame, "top_level": True, "position": 99}

class AdminTab:
    def __init__(self, parent):
        self.frame = ScrollableFrame(parent, always_show_scrollbar=True)
        inner = self.frame.inner
        ctk.CTkLabel(inner, text="Admin", font=ctk.CTkFont(size=18, weight="bold"), text_color="black").pack(pady=(20, 10))
        ctk.CTkLabel(inner, text="Admin tools and settings will appear here.", text_color="black").pack(pady=10)
        self.status_label = ctk.CTkLabel(inner, text="", text_color="black")
        self.status_label.pack(pady=5)
        self.update_button = ctk.CTkButton(inner, text="Manual Update", command=self.run_update, text_color="black")
        self.update_button.pack(pady=10)
        self.reinstall_button = ctk.CTkButton(inner, text="Reinstall App", command=self.confirm_reinstall, text_color="black")
        self.reinstall_button.pack(pady=10)
    def run_update(self):
        def do_update():
            self.update_button.configure(state="disabled", text="Updating...")
            self.status_label.configure(text="Running manual_update.sh...")
            try:
                subprocess.check_call(["bash", "manual_update.sh"], cwd=os.path.dirname(os.path.dirname(__file__)))
                self.status_label.configure(text="Update complete. Restarting...")
            except Exception as e:
                self.status_label.configure(text=f"Update failed: {e}")
                self.update_button.configure(state="normal", text="Manual Update")
                return
            # Relaunch the GUI after update
            os.execv(sys.executable, [sys.executable] + sys.argv)
        threading.Thread(target=do_update, daemon=True).start()

    def confirm_reinstall(self):
        self.confirm_dialog = ctk.CTkToplevel(self.frame)
        self.confirm_dialog.title("Confirm Reinstall")
        self.confirm_dialog.grab_set()  # Make modal
        ctk.CTkLabel(self.confirm_dialog, text="Are you sure you want to reinstall? This will DELETE ALL FILES (except .git) and reinstall from GitHub. This cannot be undone!", wraplength=400, text_color="red").pack(padx=20, pady=20)
        btn_frame = ctk.CTkFrame(self.confirm_dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.confirm_dialog.destroy, text_color="black").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Reinstall", command=lambda: self.reinstall_app(self.confirm_dialog), text_color="white", fg_color="red").pack(side="left", padx=10)

    def reinstall_app(self, dialog):
        dialog.destroy()
        def do_reinstall():
            self.reinstall_button.configure(state="disabled", text="Reinstalling...")
            self.status_label.configure(text="Deleting all files except .git...")
            app_dir = os.path.dirname(os.path.dirname(__file__))
            # WARNING: The following is a simulation. Uncomment to enable real deletion.
            for item in os.listdir(app_dir):
                if item in ['.git', '.', '..']:
                    continue
                path = os.path.join(app_dir, item)
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                except Exception as e:
                    self.status_label.configure(text=f"Failed to delete {item}: {e}")
                    self.reinstall_button.configure(state="normal", text="Reinstall App")
                    return
            self.status_label.configure(text="Cloning latest from GitHub...")
            try:
                subprocess.check_call(["git", "reset", "--hard"], cwd=app_dir)
                subprocess.check_call(["git", "clean", "-fdx"], cwd=app_dir)
                subprocess.check_call(["git", "pull"], cwd=app_dir)
            except Exception as e:
                self.status_label.configure(text=f"Git error: {e}")
                self.reinstall_button.configure(state="normal", text="Reinstall App")
                return
            self.status_label.configure(text="Running install.sh...")
            try:
                subprocess.check_call(["bash", "install.sh"], cwd=app_dir)
            except Exception as e:
                self.status_label.configure(text=f"Install failed: {e}")
                self.reinstall_button.configure(state="normal", text="Reinstall App")
                return
            self.status_label.configure(text="Reinstall complete. Restarting...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        threading.Thread(target=do_reinstall, daemon=True).start() 
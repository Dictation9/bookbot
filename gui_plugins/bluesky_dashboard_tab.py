import customtkinter as ctk
import threading
import time
import datetime
import subprocess
import os
import sys
import signal
from gui_plugins.scrollable_frame import ScrollableFrame

class BlueskyDashboardTab:
    def __init__(self, parent):
        self.frame = ScrollableFrame(parent, always_show_scrollbar=True)
        inner = self.frame.inner
        # Status and scan controls
        self.status_label = ctk.CTkLabel(inner, text="Status: Idle", text_color="black", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(pady=(20, 5))
        self.last_scan_label = ctk.CTkLabel(inner, text="Last Bluesky Scan: Never", text_color="black")
        self.last_scan_label.pack(pady=5)
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(pady=10)
        self.run_button = ctk.CTkButton(btn_frame, text="Run Bluesky Scan", command=self.start_scan, text_color="black")
        self.run_button.pack(side="left", padx=10)
        self.stop_button = ctk.CTkButton(btn_frame, text="Stop Scan", command=self.stop_scan, text_color="black", state="disabled")
        self.stop_button.pack(side="left", padx=10)
        # Post count label
        self.post_count_label = ctk.CTkLabel(inner, text="Posts to process: ...", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.post_count_label.pack(pady=(10, 0))
        # Duplicate count label
        self.duplicate_count_label = ctk.CTkLabel(inner, text="Duplicates found: ...", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.duplicate_count_label.pack(pady=(0, 0))
        # Books added/ignored labels
        self.books_added_label = ctk.CTkLabel(inner, text="Books added to CSV: ...", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.books_added_label.pack(pady=(0, 0))
        self.books_ignored_label = ctk.CTkLabel(inner, text="Books ignored (already in CSV): ...", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.books_ignored_label.pack(pady=(0, 0))
        # Log output
        self.log_label = ctk.CTkLabel(inner, text="Bluesky Log Output:", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.log_label.pack(pady=(15, 0))
        self.log_textbox = ctk.CTkTextbox(inner, width=800, height=300, font=ctk.CTkFont(size=12), text_color="black")
        self.log_textbox.pack(pady=5)
        self.log_textbox.configure(state="disabled")
        self.scan_thread = None
        self.bot_process = None
    def start_scan(self):
        if self.scan_thread and self.scan_thread.is_alive():
            return
        self.status_label.configure(text="Status: Running", text_color="green")
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.post_count_label.configure(text="Posts to process: ...")
        self.duplicate_count_label.configure(text="Duplicates found: ...")
        self.books_added_label.configure(text="Books added to CSV: ...")
        self.books_ignored_label.configure(text="Books ignored (already in CSV): ...")
        self.scan_thread = threading.Thread(target=self.run_bluesky_scan_subprocess, daemon=True)
        self.scan_thread.start()
    def stop_scan(self):
        if self.bot_process and self.bot_process.poll() is None:
            try:
                self.status_label.configure(text="Status: Stopping...", text_color="orange")
                self.bot_process.send_signal(signal.SIGINT)
            except Exception as e:
                self.append_log(f"Error stopping Bluesky scan: {e}")
    def run_bluesky_scan_subprocess(self):
        # Run the Bluesky scan as a subprocess and stream output to the log
        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bookbot.py")
        self.bot_process = subprocess.Popen(
            [sys.executable, bot_path, "--bluesky-only", "--count-posts-for-dashboard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            text=True,
            bufsize=1
        )
        try:
            for line in self.bot_process.stdout:
                # Look for a special line indicating the post count
                if line.startswith("[BLUESKY_POST_COUNT] "):
                    try:
                        count = int(line.strip().split(" ", 1)[1])
                        self.post_count_label.configure(text=f"Posts to process: {count}")
                    except Exception:
                        self.post_count_label.configure(text="Posts to process: (unknown)")
                # Look for a special line indicating the duplicate count
                elif line.startswith("[BLUESKY_DUPLICATES] "):
                    try:
                        count = int(line.strip().split(" ", 1)[1])
                        self.duplicate_count_label.configure(text=f"Duplicates found: {count}")
                    except Exception:
                        self.duplicate_count_label.configure(text="Duplicates found: (unknown)")
                elif line.startswith("[BLUESKY_ADDED] "):
                    try:
                        count = int(line.strip().split(" ", 1)[1])
                        self.books_added_label.configure(text=f"Books added to CSV: {count}")
                    except Exception:
                        self.books_added_label.configure(text="Books added to CSV: (unknown)")
                elif line.startswith("[BLUESKY_IGNORED] "):
                    try:
                        count = int(line.strip().split(" ", 1)[1])
                        self.books_ignored_label.configure(text=f"Books ignored (already in CSV): {count}")
                    except Exception:
                        self.books_ignored_label.configure(text="Books ignored (already in CSV): (unknown)")
                else:
                    self.append_log(line.rstrip())
            self.bot_process.wait()
            if self.bot_process.returncode == 0:
                self.status_label.configure(text="Status: Complete", text_color="blue")
            else:
                self.status_label.configure(text="Status: Error", text_color="red")
        except Exception as e:
            self.append_log(f"Bluesky scan error: {e}")
            self.status_label.configure(text="Status: Error", text_color="red")
        finally:
            self.run_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.bot_process = None
            self.last_scan_label.configure(text=f"Last Bluesky Scan: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    def append_log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

def get_tab(parent):
    tab = BlueskyDashboardTab(parent)
    return {"name": "Bluesky Dashboard", "frame": tab.frame, "top_level": True, "position": 2} 
import customtkinter as ctk
import threading
import time
import datetime
import subprocess
import os
import sys
import signal
from gui_plugins.scrollable_frame import ScrollableFrame

class DashboardTab:
    def __init__(self, parent):
        self.frame = ScrollableFrame(parent, always_show_scrollbar=True)
        inner = self.frame.inner
        # Status and scan controls
        self.status_label = ctk.CTkLabel(inner, text="Status: Idle", text_color="black", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(pady=(20, 5))
        # Version and update info
        self.version_label = ctk.CTkLabel(inner, text="Version: ...", text_color="black")
        self.version_label.pack(pady=2)
        self.last_updated_label = ctk.CTkLabel(inner, text="Last updated: ...", text_color="black")
        self.last_updated_label.pack(pady=2)
        self.latest_version_label = ctk.CTkLabel(inner, text="Latest: ...", text_color="black")
        self.latest_version_label.pack_forget()
        self.update_label = ctk.CTkLabel(inner, text="Update status: ...", text_color="black")
        self.update_label.pack(pady=2)
        btn_update_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_update_frame.pack(pady=2)
        self.check_updates_button = ctk.CTkButton(btn_update_frame, text="Check for Updates", command=self.refresh_version_and_update, text_color="black")
        self.check_updates_button.pack(side="left", padx=5)
        self.update_button = ctk.CTkButton(btn_update_frame, text="Update Now", command=self.run_update, text_color="black")
        self.update_button.pack(side="left", padx=5)
        self.update_button.pack_forget()  # Hide by default
        self.last_scan_label = ctk.CTkLabel(inner, text="Last Scan: Never", text_color="black")
        self.last_scan_label.pack(pady=5)
        # --- Stats labels ---
        self.books_count_label = ctk.CTkLabel(inner, text="Books in CSV: ...", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.books_count_label.pack(pady=(5, 0))
        self.posts_checked_label = ctk.CTkLabel(inner, text="Posts checked: ...", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.posts_checked_label.pack(pady=(0, 0))
        self.comments_checked_label = ctk.CTkLabel(inner, text="Comments checked: ...", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.comments_checked_label.pack(pady=(0, 0))
        self.ignored_comments_label = ctk.CTkLabel(inner, text="Ignored comments: ...", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.ignored_comments_label.pack(pady=(0, 0))
        self.last_email_label = ctk.CTkLabel(inner, text="Last email sent: ...", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.last_email_label.pack(pady=(0, 0))
        self.last_email_csv_label = ctk.CTkLabel(inner, text="Last email with CSV: ...", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.last_email_csv_label.pack(pady=(0, 0))
        # ---
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(pady=10)
        self.run_button = ctk.CTkButton(btn_frame, text="Run Scan", command=self.start_scan, text_color="black")
        self.run_button.pack(side="left", padx=10)
        self.stop_button = ctk.CTkButton(btn_frame, text="Stop Scan", command=self.stop_scan, text_color="black", state="disabled")
        self.stop_button.pack(side="left", padx=10)
        # Log output
        self.log_label = ctk.CTkLabel(inner, text="Live Log Output:", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.log_label.pack(pady=(15, 0))
        self.log_textbox = ctk.CTkTextbox(inner, width=800, height=300, font=ctk.CTkFont(size=12), text_color="black")
        self.log_textbox.pack(pady=5)
        self.log_textbox.configure(state="disabled")
        self.scan_thread = None
        self.bot_process = None
        self.refresh_version_and_update()
        self.refresh_stats()

    def refresh_stats(self):
        import csv
        import os
        # Count books in CSV
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "book_mentions.csv")
        books_count = 0
        if os.path.exists(csv_path):
            with open(csv_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                books_count = sum(1 for _ in reader)
        self.books_count_label.configure(text=f"Books in CSV: {books_count}")
        # Parse bot.log for stats
        log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "bot.log")
        posts_checked = comments_checked = ignored_comments = None
        last_email_time = last_email_csv_time = "..."
        if os.path.exists(log_path):
            with open(log_path, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            # Find last [STATS] and last email lines
            for line in reversed(lines):
                if posts_checked is None and "[STATS]" in line:
                    import re
                    m = re.search(r"posts=(\d+) comments=(\d+) ignored=(\d+)", line)
                    if m:
                        posts_checked = int(m.group(1))
                        comments_checked = int(m.group(2))
                        ignored_comments = int(m.group(3))
                if last_email_time == "..." and ("CSV and logs email sent" in line or "CSV report email process completed" in line):
                    # Extract timestamp
                    ts = line.split("[")[0].strip()
                    last_email_time = ts
                    last_email_csv_time = ts
                if posts_checked is not None and last_email_time != "...":
                    break
        self.posts_checked_label.configure(text=f"Posts checked: {posts_checked if posts_checked is not None else '...'}")
        self.comments_checked_label.configure(text=f"Comments checked: {comments_checked if comments_checked is not None else '...'}")
        self.ignored_comments_label.configure(text=f"Ignored comments: {ignored_comments if ignored_comments is not None else '...'}")
        self.last_email_label.configure(text=f"Last email sent: {last_email_time}")
        self.last_email_csv_label.configure(text=f"Last email with CSV: {last_email_csv_time}")

    def refresh_version_and_update(self):
        # Get git commit hash
        try:
            version = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=os.path.dirname(os.path.dirname(__file__))).decode().strip()
            self.version_label.configure(text=f"Version: {version}")
            # Get last commit date/time
            commit_time = subprocess.check_output([
                "git", "show", "-s", "--format=%cd", "--date=iso", "HEAD"
            ], cwd=os.path.dirname(os.path.dirname(__file__))).decode().strip()
            self.last_updated_label.configure(text=f"Last updated: {commit_time}")
        except Exception:
            self.version_label.configure(text="Version: unknown")
            self.last_updated_label.configure(text="Last updated: unknown")
        # Get latest remote commit hash
        latest_version = None
        try:
            subprocess.check_output(["git", "remote", "update"], cwd=os.path.dirname(os.path.dirname(__file__)))
            latest_version = subprocess.check_output(["git", "rev-parse", "--short", "origin/main"], cwd=os.path.dirname(os.path.dirname(__file__))).decode().strip()
            self.latest_version_label.configure(text=f"Latest: {latest_version}")
            self.latest_version_label.pack_forget()  # Hide by default, show only if update available
        except Exception:
            self.latest_version_label.configure(text="Latest: unknown")
            self.latest_version_label.pack_forget()
        # Check for updates
        try:
            status = subprocess.check_output(["git", "status", "-uno"], cwd=os.path.dirname(os.path.dirname(__file__))).decode()
            if "Your branch is behind" in status:
                self.update_label.configure(text="Update status: Update available!", text_color="orange")
                self.update_button.pack(pady=2)
                self.latest_version_label.pack(pady=2)
            elif "Your branch is up to date" in status:
                self.update_label.configure(text="Update status: Up to date", text_color="green")
                self.update_button.pack_forget()
                self.latest_version_label.pack_forget()
            else:
                self.update_label.configure(text="Update status: Unknown", text_color="gray")
                self.update_button.pack_forget()
                self.latest_version_label.pack_forget()
        except Exception:
            self.update_label.configure(text="Update status: unknown", text_color="gray")
            self.update_button.pack_forget()
            self.latest_version_label.pack_forget()
    def start_scan(self):
        if self.scan_thread and self.scan_thread.is_alive():
            return
        self.status_label.configure(text="Status: Running", text_color="green")
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.scan_thread = threading.Thread(target=self.run_bot_subprocess, daemon=True)
        self.scan_thread.start()
    def stop_scan(self):
        if self.bot_process and self.bot_process.poll() is None:
            try:
                self.status_label.configure(text="Status: Stopping...", text_color="orange")
                self.bot_process.send_signal(signal.SIGINT)
            except Exception as e:
                self.append_log(f"Error stopping bot: {e}")
    def run_bot_subprocess(self):
        # Run the bot as a subprocess and stream output to the log
        bot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bookbot.py")
        self.bot_process = subprocess.Popen(
            [sys.executable, bot_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.path.dirname(os.path.dirname(__file__)),
            text=True,
            bufsize=1
        )
        try:
            for line in self.bot_process.stdout:
                self.append_log(line.rstrip())
            self.bot_process.wait()
            if self.bot_process.returncode == 0:
                self.status_label.configure(text="Status: Complete", text_color="blue")
            else:
                self.status_label.configure(text="Status: Error", text_color="red")
        except Exception as e:
            self.append_log(f"Bot error: {e}")
            self.status_label.configure(text="Status: Error", text_color="red")
        finally:
            self.run_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.bot_process = None
            self.refresh_stats()
    def append_log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
    def run_update(self):
        # Run manual_update.sh and refresh version/update status
        import threading
        def do_update():
            self.update_button.configure(state="disabled", text="Updating...")
            try:
                subprocess.check_call(["bash", "manual_update.sh"], cwd=os.path.dirname(os.path.dirname(__file__)))
            except Exception as e:
                self.append_log(f"Update failed: {e}")
            self.update_button.configure(state="normal", text="Update Now")
            self.refresh_version_and_update()
            # Relaunch the GUI after update
            os.execv(sys.executable, [sys.executable] + sys.argv)
        threading.Thread(target=do_update, daemon=True).start()

def get_tab(parent):
    tab = DashboardTab(parent)
    return {"name": "Dashboard", "frame": tab.frame, "top_level": True, "position": 1} 
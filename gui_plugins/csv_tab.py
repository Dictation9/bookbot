import customtkinter as ctk
import csv
import os
from gui_plugins.scrollable_frame import ScrollableFrame

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "book_mentions.csv")
DEFAULT_COLUMNS = [
    "title", "author", "isbn13", "tags", "cover_url", "romance_io_url", "google_books_url", "steam", "steam_rating", "datetime_added", "reddit_created_utc", "reddit_created_date"
]

def get_tab(parent):
    return {"name": "CSV Viewer", "frame": CSVTab(parent).frame, "top_level": True, "position": 3}

class CSVTab:
    def __init__(self, parent):
        self.frame = ScrollableFrame(parent, width=900, height=700)
        self.inner = self.frame.inner
        self.entries = []
        self.header = []
        self.load_csv()
        btn_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        btn_frame.pack(pady=10)
        self.save_button = ctk.CTkButton(btn_frame, text="Save Changes", command=self.save_csv, text_color="black")
        self.save_button.pack(side="left", padx=10)
        self.reload_button = ctk.CTkButton(btn_frame, text="Reload", command=self.reload_csv, text_color="black")
        self.reload_button.pack(side="left", padx=10)
    def load_csv(self):
        # Clear previous widgets
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.entries = []
        # Load CSV
        if os.path.exists(CSV_PATH):
            with open(CSV_PATH, newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f))
                if reader:
                    self.header = reader[0]
                    rows = reader[1:]
                else:
                    self.header = DEFAULT_COLUMNS
                    rows = []
        else:
            self.header = DEFAULT_COLUMNS
            rows = []
        # Header row
        for col, name in enumerate(self.header):
            ctk.CTkLabel(self.inner, text=name, text_color="black", font=ctk.CTkFont(weight="bold")).grid(row=0, column=col, padx=2, pady=2)
        # Data rows
        for r, row in enumerate(rows):
            row_entries = []
            for c, value in enumerate(row):
                e = ctk.CTkEntry(self.inner, width=120)
                e.insert(0, value)
                e.grid(row=r+1, column=c, padx=2, pady=2)
                row_entries.append(e)
            self.entries.append(row_entries)
    def save_csv(self):
        # Gather data from entries
        data = [self.header]
        for row_entries in self.entries:
            data.append([e.get() for e in row_entries])
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data)
    def reload_csv(self):
        self.load_csv()
        # Re-add buttons
        btn_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        btn_frame.pack(pady=10)
        self.save_button = ctk.CTkButton(btn_frame, text="Save Changes", command=self.save_csv, text_color="black")
        self.save_button.pack(side="left", padx=10)
        self.reload_button = ctk.CTkButton(btn_frame, text="Reload", command=self.reload_csv, text_color="black")
        self.reload_button.pack(side="left", padx=10) 
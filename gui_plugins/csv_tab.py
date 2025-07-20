import customtkinter as ctk
import csv
import os
from gui_plugins.scrollable_frame import ScrollableFrame
from gui_plugins.user_plugins.lgbt_filter_tab import is_lgbt_filter_enabled, LGBT_TAGS

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "book_mentions.csv")
DEFAULT_COLUMNS = [
    "title", "author", "isbn13", "tags", "cover_url", "romance_io_url", "google_books_url", "steam", "steam_rating", "datetime_added", "reddit_created_utc", "reddit_created_date"
]

def get_tab(parent):
    return {"name": "CSV Viewer", "frame": CSVTab(parent).frame, "top_level": True, "position": 3}

class CSVTab:
    def __init__(self, parent):
        self.frame = ScrollableFrame(parent, always_show_scrollbar=True, show_horizontal_scrollbar=True)
        self.inner = self.frame.inner
        self.entries = []
        self.header = []
        self.current_columns = []  # List of selected column indices
        self.current_page = 0      # Page index for rows
        self.rows = []             # All rows loaded from CSV
        self.column_dropdowns = [] # For dropdown widgets
        self.column_selector_frame = None
        self.pagination_frame = None
        self.lgbt_filter_var = ctk.BooleanVar(value=is_lgbt_filter_enabled())
        self.load_csv(initial=True)

    def load_csv(self, initial=False):
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
                    self.rows = reader[1:]
                else:
                    self.header = DEFAULT_COLUMNS
                    self.rows = []
        else:
            self.header = DEFAULT_COLUMNS
            self.rows = []
        # LGBT filter UI
        filter_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        filter_frame.grid(row=0, column=0, columnspan=10, sticky="w", pady=(0, 5))
        filter_checkbox = ctk.CTkCheckBox(filter_frame, text="Show only LGBT books", variable=self.lgbt_filter_var, command=self.load_csv)
        filter_checkbox.pack(side="left", padx=(0, 10))
        # Setup column selection (dropdowns for each slot)
        if initial or not self.current_columns:
            self.current_columns = list(range(min(5, len(self.header))))
        if self.column_selector_frame:
            self.column_selector_frame.destroy()
        self.column_selector_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.column_selector_frame.grid(row=1, column=0, columnspan=10, sticky="w", pady=(0, 5))
        ctk.CTkLabel(self.column_selector_frame, text="Select columns to display:", text_color="black").pack(side="left", padx=(0, 10))
        self.column_dropdowns = []
        for slot in range(5):
            var = ctk.StringVar()
            if slot < len(self.current_columns):
                var.set(self.header[self.current_columns[slot]])
            else:
                var.set(self.header[0])
            dropdown = ctk.CTkOptionMenu(self.column_selector_frame, values=self.header, variable=var, command=lambda value, s=slot: self.update_columns_dropdown(s, value))
            dropdown.pack(side="left", padx=2)
            self.column_dropdowns.append(var)
        # Setup pagination controls
        if self.pagination_frame:
            self.pagination_frame.destroy()
        self.pagination_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.pagination_frame.grid(row=2, column=0, columnspan=10, sticky="w", pady=(0, 5))
        prev_btn = ctk.CTkButton(self.pagination_frame, text="Prev", command=self.prev_page, text_color="black")
        prev_btn.pack(side="left", padx=2)
        page_label = ctk.CTkLabel(self.pagination_frame, text=f"Page {self.current_page+1}", text_color="black")
        page_label.pack(side="left", padx=5)
        next_btn = ctk.CTkButton(self.pagination_frame, text="Next", command=self.next_page, text_color="black")
        next_btn.pack(side="left", padx=2)
        # LGBT filter logic
        def is_lgbt_row(row):
            try:
                tags_idx = self.header.index("tags")
                tags = row[tags_idx].lower().split(',') if row[tags_idx] else []
                return any(tag.strip() in LGBT_TAGS for tag in tags)
            except Exception:
                return False
        filtered_rows = self.rows
        if self.lgbt_filter_var.get():
            filtered_rows = [row for row in self.rows if is_lgbt_row(row)]
        # Display selected columns and paginated rows
        display_columns = [var.get() for var in self.column_dropdowns if var.get() in self.header]
        display_indices = [self.header.index(col) for col in display_columns if col in self.header]
        start_row = self.current_page * 15
        end_row = start_row + 15
        display_rows = filtered_rows[start_row:end_row]
        # Header row
        for col, name in enumerate(display_columns):
            ctk.CTkLabel(self.inner, text=name, text_color="black", font=ctk.CTkFont(weight="bold")).grid(row=3, column=col, padx=2, pady=2)
        # Data rows
        for r, row in enumerate(display_rows):
            row_entries = []
            for c, col_idx in enumerate(display_indices):
                value = row[col_idx] if col_idx < len(row) else ""
                e = ctk.CTkEntry(self.inner, width=120)
                e.insert(0, value)
                e.grid(row=r+4, column=c, padx=2, pady=2)
                row_entries.append(e)
            self.entries.append(row_entries)
        # Place Save/Reload/Export buttons at the next available row
        btn_frame = ctk.CTkFrame(self.inner, fg_color="transparent")
        btn_frame.grid(row=len(display_rows)+4, column=0, columnspan=len(display_columns) if display_columns else 1, pady=10, sticky="w")
        self.save_button = ctk.CTkButton(btn_frame, text="Save Changes", command=self.save_csv, text_color="black")
        self.save_button.pack(side="left", padx=10)
        self.reload_button = ctk.CTkButton(btn_frame, text="Reload", command=self.reload_csv, text_color="black")
        self.reload_button.pack(side="left", padx=10)
        self.export_button = ctk.CTkButton(btn_frame, text="Export with LGBT Column", command=self.export_csv_with_lgbt, text_color="black")
        self.export_button.pack(side="left", padx=10)
        self.status_label = ctk.CTkLabel(self.inner, text="", text_color="green")
        self.status_label.grid(row=len(display_rows)+5, column=0, columnspan=len(display_columns) if display_columns else 1, pady=(0, 10), sticky="w")

    def update_columns_dropdown(self, slot, value):
        # Prevent duplicate columns
        selected = [var.get() for var in self.column_dropdowns]
        if selected.count(value) > 1:
            # Revert to previous value if duplicate
            for i, var in enumerate(self.column_dropdowns):
                if i != slot and var.get() == value:
                    # Set this slot to a different column
                    for col in self.header:
                        if col not in selected:
                            var.set(col)
                            break
        # Update current_columns to reflect dropdowns
        self.current_columns = [self.header.index(var.get()) for var in self.column_dropdowns if var.get() in self.header]
        self.load_csv(initial=False)

    def next_page(self):
        max_page = max(0, (len(self.rows) - 1) // 15)
        if self.current_page < max_page:
            self.current_page += 1
            self.load_csv(initial=False)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_csv(initial=False)

    def save_csv(self):
        # Gather data from entries
        data = [self.header]
        # Only update the visible page's rows
        start_row = self.current_page * 15
        for i, row_entries in enumerate(self.entries):
            row_data = [e.get() for e in row_entries]
            # Update the correct columns in the backing data
            row_idx = start_row + i
            if row_idx < len(self.rows):
                for col_pos, col_idx in enumerate(self.current_columns):
                    if col_idx < len(self.rows[row_idx]):
                        self.rows[row_idx][col_idx] = row_data[col_pos]
        data.extend(self.rows)
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        # Show confirmation
        self.status_label.configure(text="Saved successfully!")
        self.status_label.after(3000, lambda: self.status_label.configure(text=""))

    def reload_csv(self):
        self.current_page = 0
        self.load_csv(initial=True)

    def export_csv_with_lgbt(self):
        # Export CSV with an extra 'is_lgbt' column
        export_path = os.path.join(os.path.dirname(CSV_PATH), "book_mentions_with_lgbt.csv")
        header_with_lgbt = self.header + ["is_lgbt"]
        def is_lgbt_row(row):
            try:
                tags_idx = self.header.index("tags")
                tags = row[tags_idx].lower().split(',') if row[tags_idx] else []
                return any(tag.strip() in LGBT_TAGS for tag in tags)
            except Exception:
                return False
        with open(export_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header_with_lgbt)
            for row in self.rows:
                lgbt_val = "yes" if is_lgbt_row(row) else "no"
                writer.writerow(row + [lgbt_val])
        self.status_label.configure(text=f"Exported to {export_path}")
        self.status_label.after(5000, lambda: self.status_label.configure(text="")) 
import customtkinter as ctk
import threading
import time
import datetime

class DashboardTab:
    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent)
        # Status and scan controls
        self.status_label = ctk.CTkLabel(self.frame, text="Status: Idle", text_color="black", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(pady=(20, 5))
        self.last_scan_label = ctk.CTkLabel(self.frame, text="Last Scan: Never", text_color="black")
        self.last_scan_label.pack(pady=5)
        btn_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        self.run_button = ctk.CTkButton(btn_frame, text="Run Scan", command=self.start_scan, text_color="black")
        self.run_button.pack(side="left", padx=10)
        self.stop_button = ctk.CTkButton(btn_frame, text="Stop Scan", command=self.stop_scan, text_color="black", state="disabled")
        self.stop_button.pack(side="left", padx=10)
        # Book viewer/editor area
        self.books = []
        self.current_book_index = 0
        self.total_books_label = ctk.CTkLabel(self.frame, text="Total number of books found: 0", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.total_books_label.pack(pady=(10, 0))
        self.book_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.book_frame.pack(pady=5)
        self.title_label = ctk.CTkLabel(self.book_frame, text="Title:", text_color="black")
        self.title_label.grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.title_entry = ctk.CTkEntry(self.book_frame, width=400)
        self.title_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.author_label = ctk.CTkLabel(self.book_frame, text="Author:", text_color="black")
        self.author_label.grid(row=1, column=0, sticky="e", padx=5, pady=2)
        self.author_entry = ctk.CTkEntry(self.book_frame, width=400)
        self.author_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self.link_label = ctk.CTkLabel(self.book_frame, text="Book link:", text_color="black")
        self.link_label.grid(row=2, column=0, sticky="e", padx=5, pady=2)
        self.link_entry = ctk.CTkEntry(self.book_frame, width=400)
        self.link_entry.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.tags_label = ctk.CTkLabel(self.book_frame, text="Tags:", text_color="black")
        self.tags_label.grid(row=3, column=0, sticky="e", padx=5, pady=2)
        self.tags_entry = ctk.CTkEntry(self.book_frame, width=400)
        self.tags_entry.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        self.steam_label = ctk.CTkLabel(self.book_frame, text="Steam level:", text_color="black")
        self.steam_label.grid(row=4, column=0, sticky="e", padx=5, pady=2)
        self.steam_entry = ctk.CTkEntry(self.book_frame, width=400)
        self.steam_entry.grid(row=4, column=1, sticky="w", padx=5, pady=2)
        # Navigation and save controls
        self.nav_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.nav_frame.pack(pady=5)
        self.left_button = ctk.CTkButton(self.nav_frame, text="←", width=40, command=self.prev_book, text_color="black")
        self.left_button.pack(side="left", padx=5)
        self.save_button = ctk.CTkButton(self.nav_frame, text="Save manual edit to book entry", command=self.save_book_edit, text_color="black")
        self.save_button.pack(side="left", padx=10)
        self.right_button = ctk.CTkButton(self.nav_frame, text="→", width=40, command=self.next_book, text_color="black")
        self.right_button.pack(side="left", padx=5)
        # Log output
        self.log_label = ctk.CTkLabel(self.frame, text="Live Log Output:", text_color="black", font=ctk.CTkFont(size=13, weight="bold"))
        self.log_label.pack(pady=(15, 0))
        self.log_textbox = ctk.CTkTextbox(self.frame, width=800, height=300, font=ctk.CTkFont(size=12), text_color="black")
        self.log_textbox.pack(pady=5)
        self.log_textbox.configure(state="disabled")
        self.scan_thread = None
        self.stop_event = threading.Event()
    def start_scan(self):
        if self.scan_thread and self.scan_thread.is_alive():
            return
        self.status_label.configure(text="Status: Running", text_color="green")
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.stop_event.clear()
        self.books = []
        self.current_book_index = 0
        self.hide_book_area()
        self.scan_thread = threading.Thread(target=self.simulate_scan, daemon=True)
        self.scan_thread.start()
    def stop_scan(self):
        if self.scan_thread and self.scan_thread.is_alive():
            self.stop_event.set()
            self.status_label.configure(text="Status: Stopping...", text_color="orange")
    def simulate_scan(self):
        fake_books = [
            {"title": "Red, White & Royal Blue", "author": "Casey McQuiston", "link": "https://www.romance.io/books/abc", "tags": ["LGBTQ", "Romance"], "steam": "Open Door"},
            {"title": "The Song of Achilles", "author": "Madeline Miller", "link": "https://openlibrary.org/works/OL12345W", "tags": ["Mythology", "Romance"], "steam": "Closed Door"},
            {"title": "Boyfriend Material", "author": "Alexis Hall", "link": "https://www.romance.io/books/def", "tags": ["Comedy", "Romance"], "steam": "Open Door"},
            {"title": "Cemetery Boys", "author": "Aiden Thomas", "link": "https://openlibrary.org/works/OL67890W", "tags": ["Paranormal", "LGBTQ"], "steam": "Fade to Black"},
            {"title": "Heartstopper", "author": "Alice Oseman", "link": "https://www.romance.io/books/ghi", "tags": ["Graphic Novel", "YA"], "steam": "No Steam"},
            {"title": "The House in the Cerulean Sea", "author": "TJ Klune", "link": "https://openlibrary.org/works/OL54321W", "tags": ["Fantasy", "Found Family"], "steam": "Closed Door"},
            {"title": "One Last Stop", "author": "Casey McQuiston", "link": "https://www.romance.io/books/jkl", "tags": ["Time Travel", "Romance"], "steam": "Open Door"},
            {"title": "Simon vs. the Homo Sapiens Agenda", "author": "Becky Albertalli", "link": "https://openlibrary.org/works/OL13579W", "tags": ["YA", "Coming of Age"], "steam": "No Steam"},
            {"title": "Aristotle and Dante Discover the Secrets of the Universe", "author": "Benjamin Alire Sáenz", "link": "https://www.romance.io/books/mno", "tags": ["YA", "Romance"], "steam": "Fade to Black"},
            {"title": "They Both Die at the End", "author": "Adam Silvera", "link": "https://openlibrary.org/works/OL24680W", "tags": ["Drama", "LGBTQ"], "steam": "No Steam"},
        ]
        for i, book in enumerate(fake_books):
            if self.stop_event.is_set():
                self.append_log("Scan stopped by user.")
                self.status_label.configure(text="Status: Stopped", text_color="red")
                self.run_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.hide_book_area()
                return
            time.sleep(0.4)
            self.append_log(f"Processed: {book['title']}")
            self.books.append(book)
            self.update_book_area()
        self.status_label.configure(text="Status: Complete", text_color="blue")
        self.last_scan_label.configure(text=f"Last Scan: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.append_log("Scan finished successfully.")
        self.update_book_area()
    def update_book_area(self):
        if not self.books:
            self.book_frame.pack_forget()
            self.nav_frame.pack_forget()
            self.total_books_label.pack_forget()
            return
        self.total_books_label.configure(text=f"Total number of books found: {len(self.books)}")
        if not self.total_books_label.winfo_ismapped():
            self.total_books_label.pack(pady=(10, 0))
        self.book_frame.pack(pady=5)
        self.nav_frame.pack(pady=5)
        book = self.books[self.current_book_index]
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, book.get("title", ""))
        self.author_entry.delete(0, "end")
        self.author_entry.insert(0, book.get("author", ""))
        self.link_entry.delete(0, "end")
        self.link_entry.insert(0, book.get("link", ""))
        self.tags_entry.delete(0, "end")
        self.tags_entry.insert(0, ", ".join(book.get("tags", [])))
        self.steam_entry.delete(0, "end")
        self.steam_entry.insert(0, book.get("steam", ""))
        self.left_button.configure(state="normal" if self.current_book_index > 0 else "disabled")
        self.right_button.configure(state="normal" if self.current_book_index < len(self.books)-1 else "disabled")
    def hide_book_area(self):
        self.book_frame.pack_forget()
        self.nav_frame.pack_forget()
        self.total_books_label.pack_forget()
    def prev_book(self):
        if self.current_book_index > 0:
            self.save_book_edit()
            self.current_book_index -= 1
            self.update_book_area()
    def next_book(self):
        if self.current_book_index < len(self.books)-1:
            self.save_book_edit()
            self.current_book_index += 1
            self.update_book_area()
    def save_book_edit(self):
        if not self.books:
            return
        book = self.books[self.current_book_index]
        book["title"] = self.title_entry.get()
        book["author"] = self.author_entry.get()
        book["link"] = self.link_entry.get()
        book["tags"] = [t.strip() for t in self.tags_entry.get().split(",") if t.strip()]
        book["steam"] = self.steam_entry.get()
    def append_log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

def get_tab(parent):
    tab = DashboardTab(parent)
    return {"name": "Dashboard", "frame": tab.frame, "top_level": True, "position": 1} 
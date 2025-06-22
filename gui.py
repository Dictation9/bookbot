import customtkinter as ctk
import threading
import time
import datetime
import importlib.util
import os

class BookBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Book Bot Control Panel")
        self.geometry("1024x768")

        # Set up the main grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Navigation Frame ---
        self.nav_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        self.nav_frame.grid_rowconfigure(5, weight=1) # Push widgets to the top

        self.logo_label = ctk.CTkLabel(self.nav_frame, text="Book Bot", font=ctk.CTkFont(size=20, weight="bold"), text_color="black")
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        self.plugin_tabs = []
        self.plugin_buttons = []
        self.plugin_frames = []
        self.load_plugins()

        # Select the first plugin tab by default if any
        if self.plugin_tabs:
            self.select_frame_by_name("plugin_0")

    def load_plugins(self):
        def load_from_dir(plugins_dir):
            if not os.path.isdir(plugins_dir):
                return []
            tabs = []
            for fname in os.listdir(plugins_dir):
                if fname.endswith('.py') and fname != '__init__.py':
                    plugin_path = os.path.join(plugins_dir, fname)
                    spec = importlib.util.spec_from_file_location(fname[:-3], plugin_path)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        try:
                            spec.loader.exec_module(mod)
                            if hasattr(mod, 'get_tab'):
                                tab_info = mod.get_tab(self)
                                if isinstance(tab_info, dict) and 'name' in tab_info and 'frame' in tab_info:
                                    tabs.append(tab_info)
                        except Exception as e:
                            print(f"Failed to load plugin {fname}: {e}")
            return tabs
        # Load core plugins
        plugins_dir = os.path.join(os.path.dirname(__file__), 'gui_plugins')
        self.plugin_tabs = load_from_dir(plugins_dir)
        # Load user plugins
        user_plugins_dir = os.path.join(plugins_dir, 'user_plugins')
        self.plugin_tabs += load_from_dir(user_plugins_dir)
        # Add plugin buttons to nav if any plugins found
        if self.plugin_tabs:
            ctk.CTkLabel(self.nav_frame, text="Plugins", font=ctk.CTkFont(size=15, weight="bold"), text_color="black").grid(row=6, column=0, padx=20, pady=(30, 5), sticky="w")
            for i, tab in enumerate(self.plugin_tabs):
                btn = ctk.CTkButton(self.nav_frame, text=tab['name'], command=lambda idx=i: self.plugin_frame_event(idx), text_color="black")
                btn.grid(row=7+i, column=0, padx=20, pady=5)
                self.plugin_buttons.append(btn)
                self.plugin_frames.append(tab['frame'])

    def plugin_frame_event(self, idx):
        self.select_frame_by_name(f"plugin_{idx}")

    def select_frame_by_name(self, name):
        # Set button colors
        for btn in self.plugin_buttons:
            btn.configure(fg_color=("gray75", "gray25") if btn.cget("text") == name else "transparent")

        # Show the selected frame
        idx = None
        if name.startswith("plugin_"):
            try:
                idx = int(name.split("_")[1])
            except Exception:
                idx = None
        if idx is not None:
            for i, frame in enumerate(self.plugin_frames):
                if i == idx:
                    frame.grid(row=0, column=1, sticky="nsew")
                else:
                    frame.grid_forget()

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
        self.books = []
        self.current_book_index = 0
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
        # Enable/disable nav buttons
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


if __name__ == "__main__":
    ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("blue") # Themes: "blue" (default), "green", "dark-blue"
    
    app = BookBotGUI()
    app.mainloop() 
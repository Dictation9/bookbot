import customtkinter as ctk

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

        self.dashboard_button = ctk.CTkButton(self.nav_frame, text="Dashboard", command=self.dashboard_frame_event, text_color="black")
        self.dashboard_button.grid(row=1, column=0, padx=20, pady=10)

        self.config_button = ctk.CTkButton(self.nav_frame, text="Configuration", command=self.config_frame_event, text_color="black")
        self.config_button.grid(row=2, column=0, padx=20, pady=10)

        self.csv_button = ctk.CTkButton(self.nav_frame, text="CSV Viewer", command=self.csv_frame_event, text_color="black")
        self.csv_button.grid(row=3, column=0, padx=20, pady=10)

        self.logs_button = ctk.CTkButton(self.nav_frame, text="Log Viewer", command=self.log_frame_event, text_color="black")
        self.logs_button.grid(row=4, column=0, padx=20, pady=10)

        # --- Create Frames for Each Tab ---
        self.dashboard_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.config_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.csv_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.log_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # --- Placeholder Content for Frames ---
        ctk.CTkLabel(self.dashboard_frame, text="Dashboard Frame - Controls and Live Log will be here.", text_color="black").pack(pady=20)
        ctk.CTkLabel(self.config_frame, text="Configuration Frame - Settings editor will be here.", text_color="black").pack(pady=20)
        ctk.CTkLabel(self.csv_frame, text="CSV Viewer Frame - Data table will be here.", text_color="black").pack(pady=20)
        ctk.CTkLabel(self.log_frame, text="Log Viewer Frame - Log file content will be here.", text_color="black").pack(pady=20)

        # Select the default frame
        self.select_frame_by_name("dashboard")

    def select_frame_by_name(self, name):
        # Set button colors
        self.dashboard_button.configure(fg_color=("gray75", "gray25") if name == "dashboard" else "transparent")
        self.config_button.configure(fg_color=("gray75", "gray25") if name == "config" else "transparent")
        self.csv_button.configure(fg_color=("gray75", "gray25") if name == "csv" else "transparent")
        self.logs_button.configure(fg_color=("gray75", "gray25") if name == "log" else "transparent")

        # Show the selected frame
        if name == "dashboard":
            self.dashboard_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.dashboard_frame.grid_forget()
        if name == "config":
            self.config_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.config_frame.grid_forget()
        if name == "csv":
            self.csv_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.csv_frame.grid_forget()
        if name == "log":
            self.log_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.log_frame.grid_forget()

    def dashboard_frame_event(self):
        self.select_frame_by_name("dashboard")

    def config_frame_event(self):
        self.select_frame_by_name("config")

    def csv_frame_event(self):
        self.select_frame_by_name("csv")

    def log_frame_event(self):
        self.select_frame_by_name("log")


if __name__ == "__main__":
    ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("blue") # Themes: "blue" (default), "green", "dark-blue"
    
    app = BookBotGUI()
    app.mainloop() 
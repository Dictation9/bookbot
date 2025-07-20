import customtkinter as ctk
import configparser
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'lgbt_filter_config.ini')
LGBT_TAGS = {'lgbt', 'lgbtq', 'queer', 'gay', 'lesbian', 'trans', 'bisexual', 'nonbinary'}

def is_lgbt_filter_enabled():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH)
        return config.getboolean('filter', 'enabled', fallback=False)
    return False

def set_lgbt_filter_enabled(enabled: bool):
    config = configparser.ConfigParser()
    config['filter'] = {'enabled': str(enabled).lower()}
    with open(CONFIG_PATH, 'w') as f:
        config.write(f)

def get_tab(parent):
    frame = ctk.CTkFrame(parent)
    label = ctk.CTkLabel(frame, text="LGBT Book Filter", text_color="black", font=ctk.CTkFont(size=16, weight="bold"))
    label.pack(pady=(20, 10))
    desc = ctk.CTkLabel(frame, text="Enable this option to only show books with LGBT-related tags in the dashboard and CSV.", wraplength=400, text_color="black")
    desc.pack(pady=(0, 20))
    var = ctk.BooleanVar(value=is_lgbt_filter_enabled())
    def on_toggle():
        set_lgbt_filter_enabled(var.get())
    toggle = ctk.CTkCheckBox(frame, text="Enable LGBT Book Filtering", variable=var, command=on_toggle)
    toggle.pack(pady=10)

    # Add Close button to return to Dashboard
    def close_tab():
        # Try to call select_frame_by_name on the parent (root window)
        root = frame.master
        while root.master is not None:
            root = root.master
        if hasattr(root, 'select_frame_by_name'):
            root.select_frame_by_name('top_0')  # Assumes Dashboard is top_0
    close_btn = ctk.CTkButton(frame, text="Close", command=close_tab)
    close_btn.pack(pady=(20, 10))

    return {"name": "LGBT Filter", "frame": frame}

# Helper for other plugins to use
__all__ = ["is_lgbt_filter_enabled", "LGBT_TAGS"] 
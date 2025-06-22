# GUI Plugins

This folder allows you to add custom tabs or menus to the Book Bot GUI without modifying the main code.

## How to Add a Plugin

1. Create a new Python file in the `user_plugins/` subfolder (e.g., `user_plugins/my_tab.py`).
2. Define a function called `get_tab(parent)` that returns a dictionary with:
   - `name`: The name of the tab/menu (string)
   - `frame`: A `CTkFrame` or widget to display as the tab content

Example:
```python
import customtkinter as ctk

def get_tab(parent):
    frame = ctk.CTkFrame(parent)
    label = ctk.CTkLabel(frame, text="This is my custom tab!", text_color="black")
    label.pack(padx=20, pady=20)
    return {"name": "My Tab", "frame": frame}
```

3. Restart the GUI. Your tab will appear in the navigation under "Plugins".

**Note:** Core tabs (Dashboard, Configuration, etc.) are in the main `gui_plugins/` folder. User plugins should go in `gui_plugins/user_plugins/`. 
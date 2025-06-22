#!/bin/bash
echo "Installing Book Bot..."
git clone https://github.com/Dictation9/bookbot ~/bookbot || cd ~/bookbot
cd ~/bookbot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install praw rich prawcore beautifulsoup4 setproctitle customtkinter
chmod +x run.sh run_gui.sh cron_setup.sh manual_update.sh

# Dynamically create the .desktop file with the correct absolute path
APP_DIR=$(pwd)
echo "Creating desktop shortcut with path: $APP_DIR"
cat << EOF > bookbot.desktop
[Desktop Entry]
Version=1.0
Name=Book Bot
Comment=A GUI for managing the Reddit Book Bot
Exec="$APP_DIR/run_gui.sh"
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
EOF

# Ensure the .desktop file is executable
chmod +x bookbot.desktop
# Copy to Desktop
cp bookbot.desktop ~/Desktop/
# Also copy to application menu for future users
cp bookbot.desktop ~/.local/share/applications/
./cron_setup.sh
echo "Installation complete."
echo "You can now run the bot using:"
echo "  - ./run.sh (command line interface)"
echo "  - ./run_gui.sh (graphical user interface)"
echo "  - Double-click the Book Bot icon on your desktop"

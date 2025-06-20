#!/bin/bash
echo "Installing Book Bot..."
git clone https://github.com/Dictation9/bookbot ~/bookbot || cd ~/bookbot
cd ~/bookbot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install praw rich prawcore beautifulsoup4 setproctitle
chmod +x run.sh cron_setup.sh bookbot.desktop manual_update.sh
cp bookbot.desktop ~/Desktop/
./cron_setup.sh
echo "Installation complete."

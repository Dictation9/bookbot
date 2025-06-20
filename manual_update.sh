#!/bin/bash
cd ~/bookbot

# Backup config.ini if it exists
if [ -f config.ini ]; then
    cp config.ini config.ini.bak
fi

git pull

# Update Python requirements
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Restore config.ini if it was overwritten
if [ -f config.ini.bak ]; then
    mv config.ini.bak config.ini
fi

echo "Manual update complete. Your config.ini is preserved." 
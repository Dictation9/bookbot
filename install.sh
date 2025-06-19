#!/bin/bash

echo "[1/5] Cloning repo..."
git clone https://github.com/YOURUSERNAME/bookbot.git ~/bookbot
cd ~/bookbot || exit 1

echo "[2/5] Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "[3/5] Making launcher executable..."
chmod +x run.sh
chmod +x bookbot.desktop

echo "[4/5] Creating desktop shortcut..."
cp bookbot.desktop ~/Desktop/

echo "[5/5] Done! You can now run 'Queernook Book Bot' from your desktop."

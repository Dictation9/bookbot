#!/bin/bash

# Get the absolute path to the script's directory and cd into it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Run the GUI application
echo "🚀 Launching Book Bot GUI..."
python3 gui.py
echo "✅ GUI closed." 
#!/bin/bash
cd ~/bookbot

# 1. Create a timestamped backup of the entire project
timestamp=$(date +"%Y%m%d_%H%M%S")
backup_dir="backups/backup_$timestamp"
mkdir -p "$backup_dir"
cp -r . "$backup_dir"

echo "Backup created at $backup_dir"

# 2. Backup config.ini separately (optional, for extra safety)
if [ -f config.ini ]; then
    cp config.ini config.ini.bak
fi

# 3. Pull latest code from git, favoring local changes
git pull --strategy=ours

# 4. Merge configuration files (if config.example.ini exists)
if [ -f config.example.ini ] && [ -f config.ini ]; then
    python3 merge_config.py config.example.ini config.ini
fi

# 5. Update Python requirements
source venv/bin/activate
pip install --upgrade -r requirements.txt

# 6. Check for merge conflicts
if grep -r '<<<<<<< HEAD' .; then
    echo "Merge conflicts detected! Please resolve manually."
    # Optionally, move conflicted files to .conflict
fi

# 7. Restore config.ini if it was overwritten (legacy step)
if [ -f config.ini.bak ]; then
    mv config.ini.bak config.ini
fi

echo "Manual update complete. Your config.ini and project are preserved." 
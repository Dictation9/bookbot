#!/bin/bash

# Bookbot Manual Update Script (Merged & Adapted)
# Provides robust update, backup, and management for Bookbot

set -e  # Exit on any error

# Ensure logs directory exists
mkdir -p logs
LOG_FILE="logs/update.log"
echo -e "\n--- $(date '+%Y-%m-%d %H:%M:%S') [update.sh invocation] $0 $@ ---" >> "$LOG_FILE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "[INFO] $1" | tee -a "$LOG_FILE"
}
print_warning() {
    echo -e "[WARNING] $1" | tee -a "$LOG_FILE"
}
print_error() {
    echo -e "[ERROR] $1" | tee -a "$LOG_FILE"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Bookbot Manual Update Script${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

check_git_repo() {
    if [ ! -d ".git" ]; then
        print_warning "Not a git repository. Some update options will be limited."
        return 1
    fi
    return 0
}

backup_current_state() {
    print_status "Creating backup of current state..."
    timestamp=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="backups/backup_$timestamp"
    mkdir -p "$BACKUP_DIR"
    # Backup key files and directories
    cp -r gui.py bookbot.py scheduled_check.py manual_enrich.py merge_config.py requirements.txt config.ini config.example.ini gui_plugins handlers email_handlers bluesky_scan.py book_utils.py bot_handler_template.py "$BACKUP_DIR/" 2>/dev/null || true
    print_status "Backup created in: $BACKUP_DIR"
}

update_dependencies() {
    print_status "Updating Python dependencies..."
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    source venv/bin/activate
    print_status "Upgrading pip..."
    pip install --upgrade pip
    print_status "Updating requirements..."
    pip install -r requirements.txt --upgrade
    print_status "Generating updated requirements.txt..."
    pip freeze > requirements.txt.new
    if [ -f "requirements.txt" ]; then
        print_status "Changes in dependencies:"
        diff requirements.txt requirements.txt.new || true
        mv requirements.txt.new requirements.txt
    else
        mv requirements.txt.new requirements.txt
    fi
    print_status "Dependencies updated successfully!"
}

merge_ini_file() {
    local current_file="$1"
    local backup_file="$2"
    local output_file="$3"
    print_status "Merging INI-style configuration..."
    cp "$current_file" "$output_file"
    while IFS= read -r line; do
        if [[ "$line" =~ ^\[.*\]$ ]]; then
            section="${line#[}"
            section="${section%]}"
            if ! grep -q "^\[$section\]" "$output_file"; then
                echo "" >> "$output_file"
                echo "$line" >> "$output_file"
                sed -n "/^\[$section\]/,/^\[/p" "$backup_file" | tail -n +2 | head -n -1 >> "$output_file" 2>/dev/null || true
            fi
        fi
    done < "$backup_file"
    mv "$output_file" "$current_file"
    print_status "INI file merged successfully"
}

merge_config_files() {
    local file_path="$1"
    local backup_file="$2"
    if [ -f "$file_path" ] && [ -f "$backup_file" ]; then
        print_status "Merging configuration file: $file_path"
        local temp_file=$(mktemp)
        case "$file_path" in
            *.ini|*.cfg|*.conf)
                merge_ini_file "$file_path" "$backup_file" "$temp_file"
                ;;
            *)
                print_warning "Unknown file type or merge not implemented. Please manually merge $file_path"
                ;;
        esac
        rm -f "$temp_file"
    fi
}

handle_merge_conflicts() {
    local backup_dir="$1"
    print_warning "Merge conflicts detected. Attempting to resolve automatically..."
    for file in *.py *.ini *.cfg *.conf; do
        if [ -f "$file" ] && grep -q "<<<<<<< HEAD" "$file"; then
            print_status "Resolving conflicts in $file..."
            cp "$file" "$file.conflict"
            if [[ "$file" == *.py ]]; then
                sed '/<<<<<<< HEAD/,/=======/d' "$file" | sed '/>>>>>>> /d' > "$file.tmp"
                mv "$file.tmp" "$file"
            elif [[ "$file" == *.ini ]] || [[ "$file" == *.cfg ]] || [[ "$file" == *.conf ]]; then
                merge_ini_file "$file" "$backup_dir/$file" "$file.tmp"
            else
                print_warning "Manual resolution needed for $file"
                cp "$file" "${file}.conflict"
            fi
        fi
    done
    find . -name "*.py" -o -name "*.ini" -o -name "*.cfg" -o -name "*.conf" | xargs sed -i '/<<<<<<< HEAD/,/>>>>>>> /d' 2>/dev/null || true
}

update_code() {
    if ! check_git_repo; then
        print_error "Cannot update code: not a git repository"
        return 1
    fi
    print_status "Updating code from git repository..."
    IMPORTANT_FILES=("config.ini" "config.example.ini" "requirements.txt")
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    for file in "${IMPORTANT_FILES[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$BACKUP_DIR/"
        fi
    done
    if ! git diff-index --quiet HEAD --; then
        print_warning "You have uncommitted changes. Stashing them..."
        git stash
        STASHED=true
    else
        STASHED=false
    fi
    print_status "Fetching latest changes..."
    git fetch origin
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main 2>/dev/null || git rev-parse origin/master 2>/dev/null)
    if [ "$LOCAL" = "$REMOTE" ]; then
        print_status "Code is already up to date!"
        return 0
    fi
    print_status "Pulling latest changes with merge strategy..."
    git config pull.rebase false
    git config merge.ours.driver true
    if git pull origin main 2>/dev/null || git pull origin master 2>/dev/null; then
        print_status "Successfully pulled and merged changes!"
    else
        print_warning "Automatic merge failed. Attempting manual merge..."
        git reset --hard HEAD
        if git pull --strategy=ours origin main 2>/dev/null || git pull --strategy=ours origin master 2>/dev/null; then
            print_status "Merged with local changes preserved!"
        else
            print_error "Merge failed. Attempting automatic conflict resolution..."
            handle_merge_conflicts "$BACKUP_DIR"
            if git add . && git commit -m "Auto-resolved merge conflicts" 2>/dev/null; then
                print_status "Successfully resolved conflicts automatically!"
            else
                print_error "Automatic resolution failed. Manual intervention required."
                print_status "Backup files are available in: $BACKUP_DIR"
                print_status "Please resolve conflicts manually and then run:"
                print_status "  git add ."
                print_status "  git commit -m 'Resolved merge conflicts'"
                return 1
            fi
        fi
    fi
    if [ "$STASHED" = true ]; then
        print_status "Restoring stashed changes..."
        if ! git stash pop; then
            print_warning "Could not restore stashed changes. Check git status."
        fi
    fi
    print_status "Checking for configuration file conflicts..."
    for file in "${IMPORTANT_FILES[@]}"; do
        if [ -f "$file" ] && [ -f "$BACKUP_DIR/$file" ]; then
            if ! cmp -s "$file" "$BACKUP_DIR/$file"; then
                merge_config_files "$file" "$BACKUP_DIR/$file"
            fi
        fi
    done
    print_status "Code updated successfully!"
    print_status "Backup files available in: $BACKUP_DIR"
}

update_system() {
    print_status "Updating system packages..."
    if [ -f "/etc/rpi-issue" ] || grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_status "Detected Raspberry Pi - updating system packages..."
        sudo apt update
        sudo apt upgrade -y
        sudo apt autoremove -y
        sudo apt autoclean
        print_status "System packages updated successfully!"
    else
        print_warning "Not running on Raspberry Pi. Skipping system updates."
    fi
}

stop_app() {
    print_status "Stopping Bookbot application..."
    PID=$(pgrep -f "python.*bookbot.py" || pgrep -f "python.*gui.py" || echo "")
    if [ ! -z "$PID" ]; then
        print_status "Stopping Bookbot process (PID: $PID)..."
        kill $PID
        sleep 2
        if kill -0 $PID 2>/dev/null; then
            print_warning "Process still running, forcing termination..."
            kill -9 $PID
            sleep 1
        fi
        if ! kill -0 $PID 2>/dev/null; then
            print_status "Bookbot stopped successfully!"
        else
            print_error "Failed to stop Bookbot process"
            return 1
        fi
    else
        print_status "Bookbot is not currently running"
    fi
}

restart_app() {
    print_status "Restarting Bookbot application..."
    PID=$(pgrep -f "python.*bookbot.py" || pgrep -f "python.*gui.py" || echo "")
    if [ ! -z "$PID" ]; then
        print_status "Stopping existing Bookbot process (PID: $PID)..."
        kill $PID
        sleep 2
    fi
    print_status "Starting Bookbot..."
    nohup python3 bookbot.py > bookbot.log 2>&1 &
    print_status "Bookbot restarted successfully!"
    print_status "Check logs with: tail -f bookbot.log"
}

start_gui() {
    print_status "Starting Bookbot GUI..."
    nohup python3 gui.py > gui.log 2>&1 &
    print_status "GUI started successfully!"
    print_status "Check logs with: tail -f gui.log"
}

setup_autostart() {
    print_status "Setting up Bookbot to start on boot..."
    CURRENT_DIR=$(pwd)
    SCRIPT_PATH="$CURRENT_DIR/bookbot.py"
    if [ -f "/etc/rpi-issue" ] || grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_status "Detected Raspberry Pi - setting up systemd service..."
        SERVICE_FILE="/etc/systemd/system/bookbot.service"
        cat > /tmp/bookbot.service << EOF
[Unit]
Description=Bookbot Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python $SCRIPT_PATH
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        sudo cp /tmp/bookbot.service "$SERVICE_FILE"
        sudo systemctl daemon-reload
        sudo systemctl enable bookbot.service
        print_status "Bookbot autostart service created and enabled!"
        print_status "Service file: $SERVICE_FILE"
        print_status "To manage the service:"
        print_status "  sudo systemctl start bookbot"
        print_status "  sudo systemctl stop bookbot"
        print_status "  sudo systemctl status bookbot"
        print_status "  sudo systemctl disable bookbot"
    else
        print_status "Setting up crontab for autostart..."
        STARTUP_SCRIPT="$CURRENT_DIR/startup.sh"
        cat > "$STARTUP_SCRIPT" << EOF
#!/bin/bash
cd "$CURRENT_DIR"
source venv/bin/activate
python3 bookbot.py > bookbot.log 2>&1 &
EOF
        chmod +x "$STARTUP_SCRIPT"
        (crontab -l 2>/dev/null; echo "@reboot $STARTUP_SCRIPT") | crontab -
        print_status "Bookbot autostart configured via crontab!"
        print_status "Startup script: $STARTUP_SCRIPT"
        print_status "To remove autostart: crontab -e"
    fi
}

remove_autostart() {
    print_status "Removing Bookbot autostart configuration..."
    if [ -f "/etc/rpi-issue" ] || grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_status "Removing systemd service..."
        sudo systemctl disable bookbot.service 2>/dev/null || true
        sudo rm -f /etc/systemd/system/bookbot.service
        sudo systemctl daemon-reload
        print_status "Systemd service removed!"
    else
        print_status "Removing from crontab..."
        crontab -l 2>/dev/null | grep -v "startup.sh" | crontab -
        rm -f "$CURRENT_DIR/startup.sh"
        print_status "Crontab autostart removed!"
    fi
}

hard_reset() {
    print_warning "🚨 HARD RESET WARNING 🚨"
    echo ""
    echo "This will completely delete everything and perform a fresh install:"
    echo "  - All current files will be deleted"
    echo "  - Virtual environment will be removed"
    echo "  - All backups will be deleted"
    echo "  - Application will be stopped"
    echo "  - Fresh code will be downloaded from git"
    echo "  - New virtual environment will be created"
    echo "  - Dependencies will be reinstalled"
    echo ""
    echo -e "${RED}This action cannot be undone!${NC}"
    echo ""
    read -p "Are you absolutely sure you want to proceed? (type 'YES' to confirm): " confirm
    if [ "$confirm" != "YES" ]; then
        print_status "Hard reset cancelled."
        return
    fi
    print_status "Starting hard reset..."
    stop_app
    remove_autostart 2>/dev/null || true
    CURRENT_DIR=$(pwd)
    PARENT_DIR=$(dirname "$CURRENT_DIR")
    PROJECT_NAME=$(basename "$CURRENT_DIR")
    # Copy this script to /tmp and run the rest from there
    cp "$0" /tmp/bookbot_update_backup.sh
    chmod +x /tmp/bookbot_update_backup.sh
    print_status "Switching to backup script to complete hard reset..."
    cd "$PARENT_DIR"
    exec /tmp/bookbot_update_backup.sh --finish-hard-reset "$PROJECT_NAME" "$CURRENT_DIR"
}

show_menu() {
    echo ""
    echo "Available update options:"
    echo "1) Update dependencies only"
    echo "2) Update code from git repository"
    echo "3) Update system packages (Raspberry Pi only)"
    echo "4) Full update (dependencies + code + system)"
    echo "5) Restart application"
    echo "6) Stop application"
    echo "7) Start GUI"
    echo "8) Show current status"
    echo "9) Setup autostart (start on boot)"
    echo "10) Remove autostart"
    echo "11) 🚨 HARD RESET (delete everything & fresh install)"
    echo "12) Exit"
    echo ""
    read -p "Select an option (1-12): " choice
}

show_status() {
    print_status "Current Bookbot Status:"
    echo ""
    PID=$(pgrep -f "python.*bookbot.py" || pgrep -f "python.*gui.py" || echo "")
    if [ ! -z "$PID" ]; then
        echo -e "${GREEN}✓${NC} Bookbot is running (PID: $PID)"
    else
        echo -e "${RED}✗${NC} Bookbot is not running"
    fi
    if check_git_repo; then
        echo -e "${GREEN}✓${NC} Git repository detected"
        BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
        echo "   Current branch: $BRANCH"
        COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
        echo "   Current commit: $COMMIT"
    else
        echo -e "${YELLOW}⚠${NC} Not a git repository"
    fi
    if [ -d "venv" ]; then
        echo -e "${GREEN}✓${NC} Virtual environment exists"
    else
        echo -e "${YELLOW}⚠${NC} Virtual environment not found"
    fi
    if [ -f "/etc/rpi-issue" ] || grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Running on Raspberry Pi"
    else
        echo -e "${YELLOW}⚠${NC} Not running on Raspberry Pi"
    fi
}

main() {
    print_header
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. This is not recommended for security reasons."
    fi
    if [ "$1" = "--deps" ]; then
        update_dependencies
        exit 0
    elif [ "$1" = "--code" ]; then
        update_code
        exit 0
    elif [ "$1" = "--system" ]; then
        update_system
        exit 0
    elif [ "$1" = "--full" ]; then
        backup_current_state
        update_dependencies
        update_code
        update_system
        exit 0
    elif [ "$1" = "--restart" ]; then
        restart_app
        exit 0
    elif [ "$1" = "--stop" ]; then
        stop_app
        exit 0
    elif [ "$1" = "--status" ]; then
        show_status
        exit 0
    elif [ "$1" = "--autostart" ]; then
        setup_autostart
        exit 0
    elif [ "$1" = "--remove-autostart" ]; then
        remove_autostart
        exit 0
    elif [ "$1" = "--hard-reset" ]; then
        hard_reset
        exit 0
    elif [ "$1" = "--gui" ]; then
        start_gui
        exit 0
    elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --deps              Update Python dependencies only"
        echo "  --code              Update code from git repository"
        echo "  --system            Update system packages (Raspberry Pi only)"
        echo "  --full              Perform full update (dependencies + code + system)"
        echo "  --restart           Restart the Bookbot application"
        echo "  --stop              Stop the Bookbot application"
        echo "  --status            Show current status"
        echo "  --autostart         Setup autostart (start on boot)"
        echo "  --remove-autostart  Remove autostart configuration"
        echo "  --hard-reset        🚨 Delete everything and perform fresh install"
        echo "  --gui               Start the Bookbot GUI"
        echo "  --help              Show this help message"
        echo ""
        echo "If no option is provided, an interactive menu will be shown."
        exit 0
    fi
    while true; do
        show_menu
        case $choice in
            1)
                backup_current_state
                update_dependencies
                ;;
            2)
                backup_current_state
                update_code
                ;;
            3)
                update_system
                ;;
            4)
                backup_current_state
                update_dependencies
                update_code
                update_system
                ;;
            5)
                restart_app
                ;;
            6)
                stop_app
                ;;
            7)
                start_gui
                ;;
            8)
                show_status
                ;;
            9)
                setup_autostart
                ;;
            10)
                remove_autostart
                ;;
            11)
                hard_reset
                ;;
            12)
                print_status "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid option. Please select 1-12."
                ;;
        esac
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Handler for finishing the hard reset from /tmp
if [[ "$1" == "--finish-hard-reset" ]]; then
    PROJECT_NAME="$2"
    PROJECT_PATH="$3"
    echo "[INFO] Deleting project directory: $PROJECT_PATH"
    rm -rf "$PROJECT_PATH"
    echo "[INFO] Cloning fresh code from git..."
    if git clone https://github.com/Dictation9/Bookbot.git "$PROJECT_NAME"; then
        cd "$PROJECT_NAME"
        echo "[INFO] Creating new virtual environment..."
        python3 -m venv venv
        echo "[INFO] Installing dependencies..."
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        echo "[INFO] Setting up fresh installation..."
        mkdir -p logs
        mkdir -p backups
        echo "[INFO] Hard reset completed successfully!"
        echo "[INFO] Fresh installation is ready."
        echo "[INFO] You can now run: python3 bookbot.py"
    else
        echo "[ERROR] Failed to download fresh code from git."
        echo "[ERROR] Please manually download the code and reinstall."
        exit 1
    fi
    exit 0
fi

main "$@" 
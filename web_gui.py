import os
import threading
import time
from flask import Flask, render_template, jsonify, send_file, request, abort
import psutil
import platform
import csv
import configparser
import glob
import zipfile
import io
import subprocess
import sys
try:
    from gpiozero import CPUTemperature, PWMOutputDevice
except ImportError:
    CPUTemperature = None
    PWMOutputDevice = None

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

# Store up to 10 minutes of stats (sampled every 5 seconds)
stats_history = []
stats_lock = threading.Lock()
HISTORY_SECONDS = 600  # 10 minutes
SAMPLE_INTERVAL = 5    # seconds

# --- Bluesky Scan Process Management ---
bluesky_scan_process = None
bluesky_scan_log = []
bluesky_scan_status = 'Idle'
bluesky_scan_status_color = ''
bluesky_last_scan = None
bluesky_post_count = None
bluesky_duplicate_count = None
bluesky_books_added = None
bluesky_books_ignored = None
bluesky_log_lock = threading.Lock()

def run_bluesky_scan_subprocess():
    global bluesky_scan_process, bluesky_scan_log, bluesky_scan_status, bluesky_scan_status_color
    global bluesky_last_scan, bluesky_post_count, bluesky_duplicate_count, bluesky_books_added, bluesky_books_ignored
    bluesky_scan_status = 'Running'
    bluesky_scan_status_color = 'green'
    bluesky_scan_log = []
    bluesky_post_count = None
    bluesky_duplicate_count = None
    bluesky_books_added = None
    bluesky_books_ignored = None
    bot_path = os.path.join(os.path.dirname(__file__), 'bookbot.py')
    process = subprocess.Popen(
        [sys.executable, bot_path, '--bluesky-only', '--count-posts-for-dashboard'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=os.path.dirname(__file__),
        text=True,
        bufsize=1
    )
    bluesky_scan_process = process
    try:
        for line in process.stdout:
            with bluesky_log_lock:
                bluesky_scan_log.append(line.rstrip())
                if len(bluesky_scan_log) > 500:
                    bluesky_scan_log = bluesky_scan_log[-500:]
            # Parse special lines for stats
            if line.startswith('[BLUESKY_POST_COUNT] '):
                try:
                    bluesky_post_count = int(line.strip().split(' ', 1)[1])
                except Exception:
                    bluesky_post_count = None
            elif line.startswith('[BLUESKY_DUPLICATES] '):
                try:
                    bluesky_duplicate_count = int(line.strip().split(' ', 1)[1])
                except Exception:
                    bluesky_duplicate_count = None
            elif line.startswith('[BLUESKY_ADDED] '):
                try:
                    bluesky_books_added = int(line.strip().split(' ', 1)[1])
                except Exception:
                    bluesky_books_added = None
            elif line.startswith('[BLUESKY_IGNORED] '):
                try:
                    bluesky_books_ignored = int(line.strip().split(' ', 1)[1])
                except Exception:
                    bluesky_books_ignored = None
        process.wait()
        bluesky_last_scan = time.strftime('%Y-%m-%d %H:%M:%S')
        if process.returncode == 0:
            bluesky_scan_status = 'Complete'
            bluesky_scan_status_color = 'blue'
        else:
            bluesky_scan_status = 'Error'
            bluesky_scan_status_color = 'red'
    except Exception as e:
        with bluesky_log_lock:
            bluesky_scan_log.append(f'Bluesky scan error: {e}')
        bluesky_scan_status = 'Error'
        bluesky_scan_status_color = 'red'
    finally:
        bluesky_scan_process = None


def sample_stats():
    while True:
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_used = mem.used // (1024 * 1024)
        mem_total = mem.total // (1024 * 1024)
        temp = None
        fan_speed = None
        if platform.system() == "Linux" and (os.path.exists("/sys/class/thermal/thermal_zone0/temp") or CPUTemperature):
            try:
                if CPUTemperature:
                    temp = CPUTemperature().temperature
                else:
                    with open("/sys/class/thermal/thermal_zone0/temp") as f:
                        temp = int(f.read()) / 1000.0
            except Exception:
                temp = None
            fan_speed = get_fan_speed()
        stat = {
            'timestamp': int(time.time()),
            'cpu_percent': cpu_percent,
            'mem_percent': mem_percent,
            'mem_used': mem_used,
            'mem_total': mem_total,
            'temp': temp,
            'fan_speed': fan_speed
        }
        with stats_lock:
            stats_history.append(stat)
            # Remove old stats
            cutoff = int(time.time()) - HISTORY_SECONDS
            while stats_history and stats_history[0]['timestamp'] < cutoff:
                stats_history.pop(0)
        time.sleep(SAMPLE_INTERVAL)

# Start background sampling thread
threading.Thread(target=sample_stats, daemon=True).start()

def get_fan_speed():
    """
    Comprehensive fan speed detection for Raspberry Pi 5.
    Looks in multiple possible locations for fan data.
    """
    fan_speed = None
    
    # Method 1: Raspberry Pi 5 specific cooling fan path
    try:
        for root, dirs, files in os.walk("/sys/devices/platform/cooling_fan/hwmon"):
            for file in files:
                if file.startswith("fan") and file.endswith("_input"):
                    with open(os.path.join(root, file)) as f:
                        fan_speed = int(f.read().strip())
                    if fan_speed:
                        return fan_speed
    except Exception:
        pass
    
    # Method 1.2: Raspberry Pi 5 specific cooling fan path
    try:
        for root, dirs, files in os.walk("/sys/devices/platform/cooling_fan/hwmon/*"):
            for file in files:
                if file.startswith("fan") and file.endswith("_input"):
                    with open(os.path.join(root, file)) as f:
                        fan_speed = int(f.read().strip())
                    if fan_speed:
                        return fan_speed
    except Exception:
        pass

    # Method 2: Look for fan files in /sys/class/hwmon
    try:
        for root, dirs, files in os.walk("/sys/class/hwmon"):
            for file in files:
                # Look for various fan file patterns
                if (file.startswith("fan") or file.startswith("pwmfan")) and file.endswith("_input"):
                    with open(os.path.join(root, file)) as f:
                        fan_speed = int(f.read().strip())
                    if fan_speed:
                        return fan_speed
    except Exception:
        pass
    
    # Method 3: Look for PWM fan control files
    try:
        for root, dirs, files in os.walk("/sys/class/hwmon"):
            for file in files:
                if file.startswith("pwm") and file.endswith("_input"):
                    with open(os.path.join(root, file)) as f:
                        fan_speed = int(f.read().strip())
                    if fan_speed:
                        return fan_speed
    except Exception:
        pass
    
    # Method 3.5: Look for PWM control files (0-255 range)
    try:
        for root, dirs, files in os.walk("/sys/class/hwmon"):
            for file in files:
                if file.startswith("pwm") and not file.endswith("_input"):
                    # PWM files without _input are typically 0-255 range
                    with open(os.path.join(root, file)) as f:
                        pwm_value = int(f.read().strip())
                    if pwm_value > 0:
                        # Convert PWM value (0-255) to RPM estimate
                        # This is approximate - actual RPM depends on fan specs
                        fan_speed = int((pwm_value / 255.0) * 2500)  # Assume max 2500 RPM
                        return fan_speed
    except Exception:
        pass
    
    # Method 3.6: Check specific Raspberry Pi 5 PWM path
    try:
        pwm_file = "/sys/class/hwmon/hwmon1/pwm1"
        if os.path.exists(pwm_file):
            with open(pwm_file) as f:
                pwm_value = int(f.read().strip())
            if pwm_value > 0:
                # Convert PWM value (0-255) to RPM estimate
                fan_speed = int((pwm_value / 255.0) * 2500)  # Assume max 2500 RPM
                return fan_speed
    except Exception:
        pass
    
    # Method 4: Look for fan files in /sys/devices/platform
    try:
        for root, dirs, files in os.walk("/sys/devices/platform"):
            for file in files:
                if (file.startswith("fan") or file.startswith("pwm")) and file.endswith("_input"):
                    with open(os.path.join(root, file)) as f:
                        fan_speed = int(f.read().strip())
                    if fan_speed:
                        return fan_speed
    except Exception:
        pass
    
    # Method 5: Look for thermal zone fan files
    try:
        for i in range(10):  # Check thermal zones 0-9
            fan_file = f"/sys/class/thermal/thermal_zone{i}/fan_input"
            if os.path.exists(fan_file):
                with open(fan_file) as f:
                    fan_speed = int(f.read().strip())
                if fan_speed:
                    return fan_speed
    except Exception:
        pass
    
    # Method 6: Try to read from PWM device directly (if using gpiozero)
    try:
        if PWMOutputDevice:
            # Try common PWM pins for fan control
            for pin in [12, 13, 18, 19]:  # Common PWM pins
                try:
                    fan = PWMOutputDevice(pin)
                    if fan.value > 0:
                        # Convert PWM value (0-1) to RPM estimate
                        # This is approximate - actual RPM depends on fan specs
                        fan_speed = int(fan.value * 2500)  # Assume max 2500 RPM
                        return fan_speed
                except Exception:
                    continue
    except Exception:
        pass
    
    return 0

@app.route('/')
def dashboard():
    # Gather system stats
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    mem_percent = mem.percent
    mem_used = mem.used // (1024 * 1024)
    mem_total = mem.total // (1024 * 1024)
    temp = None
    fan_speed = None
    # Only try to get temp/fan if on Raspberry Pi
    if platform.system() == "Linux" and (os.path.exists("/sys/class/thermal/thermal_zone0/temp") or CPUTemperature):
        try:
            if CPUTemperature:
                temp = CPUTemperature().temperature
            else:
                with open("/sys/class/thermal/thermal_zone0/temp") as f:
                    temp = int(f.read()) / 1000.0
        except Exception:
            temp = None
        # Fan speed: If using a PWM fan via gpiozero, you could read it here. Otherwise, try to read from /sys/class/hwmon or similar.
        # For now, set to None unless you have a specific fan setup.
        # Example for a PWM fan on GPIO18:
        # try:
        #     fan = PWMOutputDevice(18)
        #     fan_speed = fan.value  # 0.0 to 1.0
        # except Exception:
        #     fan_speed = None
        # Alternatively, try to read from /sys/class/hwmon/hwmon*/fan*_input
        fan_speed = get_fan_speed()
    return render_template(
        'dashboard.html',
        cpu_percent=cpu_percent,
        mem_percent=mem_percent,
        mem_used=mem_used,
        mem_total=mem_total,
        temp=temp,
        fan_speed=fan_speed
    )

@app.route('/api/stats')
def api_stats():
    window = request.args.get('window', default=None, type=int)
    with stats_lock:
        if window is not None:
            cutoff = int(time.time()) - (window * 60)
            filtered = [s for s in stats_history if s['timestamp'] >= cutoff]
            return jsonify(filtered)
        else:
            return jsonify(stats_history)

@app.route('/api/book_mentions')
def api_book_mentions():
    csv_path = os.path.join(os.path.dirname(__file__), 'book_mentions.csv')
    if not os.path.exists(csv_path):
        return jsonify({'error': 'CSV file not found'}), 404
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
    return jsonify(rows)

@app.route('/download/book_mentions')
def download_book_mentions():
    csv_path = os.path.join(os.path.dirname(__file__), 'book_mentions.csv')
    if not os.path.exists(csv_path):
        return 'CSV file not found', 404
    return send_file(csv_path, as_attachment=True, download_name='book_mentions.csv')

@app.route('/api/config', methods=['GET'])
def api_get_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config = configparser.ConfigParser()
    config.optionxform = str  # preserve case
    config.read(config_path)
    # Read config as dict, including comments if possible
    config_dict = {}
    with open(config_path, encoding='utf-8') as f:
        lines = f.readlines()
    section = None
    comments = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[') and ']' in stripped:
            section = stripped[1:stripped.index(']')]
            config_dict[section] = {'__comments__': comments, '__options__': {}}
            comments = []
        elif stripped.startswith('#') or stripped.startswith(';'):
            comments.append(stripped.lstrip('#;').strip())
        elif '=' in line and section:
            option, value = line.split('=', 1)
            option = option.strip()
            value = value.strip()
            config_dict[section]['__options__'][option] = {'value': value, 'comments': comments}
            comments = []
        elif not stripped:
            comments = []
    return jsonify(config_dict)

@app.route('/api/config', methods=['POST'])
def api_update_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    config = configparser.ConfigParser()
    config.optionxform = str
    # Write config from posted data
    with open(config_path, 'w', encoding='utf-8') as f:
        for section, section_data in data.items():
            f.write(f'[{section}]\n')
            for comment in section_data.get('__comments__', []):
                f.write(f'# {comment}\n')
            for option, optdata in section_data.get('__options__', {}).items():
                for comment in optdata.get('comments', []):
                    f.write(f'# {comment}\n')
                f.write(f'{option} = {optdata["value"]}\n')
            f.write('\n')
    return jsonify({'success': True})

@app.route('/admin')
def admin_tab():
    return render_template('admin.html')

@app.route('/config')
def config_tab():
    return render_template('config.html')

@app.route('/csv')
def csv_tab():
    return render_template('csv.html')

@app.route('/log')
def log_tab():
    return render_template('log.html')

@app.route('/api/logs/list')
def api_logs_list():
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.isdir(logs_dir):
        return jsonify([])
    files = [os.path.basename(f) for f in glob.glob(os.path.join(logs_dir, '*.log'))]
    return jsonify(files)

@app.route('/api/logs/<logname>')
def api_logs_get(logname):
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    log_path = os.path.join(logs_dir, logname)
    if not os.path.isfile(log_path) or not logname.endswith('.log'):
        return jsonify({'error': 'Log file not found'}), 404
    try:
        with open(log_path, encoding='utf-8', errors='replace') as f:
            content = f.read()
        return jsonify({'log': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/log/<logname>')
def download_log_file(logname):
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    log_path = os.path.join(logs_dir, logname)
    if not os.path.isfile(log_path) or not logname.endswith('.log'):
        abort(404)
    return send_file(log_path, as_attachment=True, download_name=logname)

@app.route('/download/logs/all.zip')
def download_all_logs_zip():
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log') and os.path.isfile(os.path.join(logs_dir, f))]
    if not log_files:
        abort(404)
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for logname in log_files:
            log_path = os.path.join(logs_dir, logname)
            zf.write(log_path, arcname=logname)
    mem_zip.seek(0)
    return send_file(mem_zip, as_attachment=True, download_name='all_logs.zip', mimetype='application/zip')

@app.route('/api/start_bluesky_scan', methods=['POST'])
def api_start_bluesky_scan():
    global bluesky_scan_process
    if bluesky_scan_process and bluesky_scan_process.poll() is None:
        return jsonify({'success': False, 'error': 'Scan already running'})
    t = threading.Thread(target=run_bluesky_scan_subprocess, daemon=True)
    t.start()
    return jsonify({'success': True})

@app.route('/api/stop_bluesky_scan', methods=['POST'])
def api_stop_bluesky_scan():
    global bluesky_scan_process, bluesky_scan_status, bluesky_scan_status_color
    if bluesky_scan_process and bluesky_scan_process.poll() is None:
        try:
            bluesky_scan_process.terminate()
            bluesky_scan_status = 'Stopped'
            bluesky_scan_status_color = 'orange'
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
        return jsonify({'success': True})
    else:
        bluesky_scan_status = 'Idle'
        bluesky_scan_status_color = ''
        return jsonify({'success': False, 'error': 'No scan running'})

@app.route('/api/bluesky_scan_log')
def api_bluesky_scan_log():
    with bluesky_log_lock:
        log = '\n'.join(bluesky_scan_log)
    return jsonify({
        'log': log,
        'status': bluesky_scan_status,
        'status_color': bluesky_scan_status_color,
        'last_scan': bluesky_last_scan,
        'post_count': bluesky_post_count,
        'duplicate_count': bluesky_duplicate_count,
        'books_added': bluesky_books_added,
        'books_ignored': bluesky_books_ignored
    })

if __name__ == '__main__':
    # Read port from config.ini
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(config_path)
    try:
        port = int(config.get('general', 'web_gui_port', fallback='6000'))
    except Exception:
        port = 6000
    app.run(host="0.0.0.0", debug=True, port=port) 
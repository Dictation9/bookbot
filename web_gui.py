from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

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

if __name__ == '__main__':
    app.run(debug=True, port=6000) 
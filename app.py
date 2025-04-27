from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import sqlite3
from datetime import datetime
import os
from werkzeug.utils import secure_filename
#import ocr_utils

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Welcome Page
@app.route('/')
def welcome():
    return render_template('welcome.html')

# Dashboard Page
@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    metrics = conn.execute('SELECT * FROM metrics ORDER BY date DESC').fetchall()
    conn.close()

    avg_weight = sum(m['weight'] for m in metrics) / len(metrics) if metrics else 0
    avg_height = sum(m['height'] for m in metrics) / len(metrics) if metrics else 0

    # ✅ FIX: Ignore entries with height 0
    valid_metrics = [m for m in metrics if m['height'] > 0]

    top_user = None
    if valid_metrics:
        top_user = max(valid_metrics, key=lambda x: x['weight'] / (x['height']/100)**2)

    return render_template('dashboard.html', metrics=metrics, avg_weight=avg_weight, avg_height=avg_height, top_user=top_user)


# Add Metrics Manually
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        user = request.form['user']
        weight = request.form['weight']
        height = request.form['height']
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        conn.execute('''
    INSERT INTO metrics 
    (user, weight, height, date, body_fat, muscle_mass, water_percentage, bone_mass, visceral_fat, bmr, body_age, bmi) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (user, weight, height, date, body_fat, muscle_mass, water_percentage, bone_mass, visceral_fat, bmr, body_age, bmi))

        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('add.html')

# Upload BMI Screenshot
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return redirect(url_for('parse_upload', filename=filename))
    return render_template('upload.html')

# Parse Uploaded Image
@app.route('/parse_upload/<filename>')
def parse_upload(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    #extracted_data = ocr_utils.extract_metrics(filepath)
    extracted_data = read(filepath)
    
    if not extracted_data:
        return "Could not extract data from image. Please try manual entry."

    user = extracted_data.get('user', 'Unknown')
    weight = extracted_data.get('Weight', 0)
    height = extracted_data.get('Height', 0)
    body_fat = extracted_data.get('Body Fat', 0)
    muscle_mass = extracted_data.get('Muscle mass', 0)
    water_percentage = extracted_data.get('Body Water', 0)
    bone_mass = extracted_data.get('Bone Mass', 0)
    visceral_fat = extracted_data.get('Visceral Fat', 0)
    bmr = extracted_data.get('BMR', 0)
    body_age = extracted_data.get('Body age', 0)
    bmi = extracted_data.get('BMI', 0)

    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO metrics 
        (user, weight, height, date, body_fat, muscle_mass, water_percentage, bone_mass, visceral_fat, bmr, body_age, bmi) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user, weight, height, date, body_fat, muscle_mass, water_percentage, bone_mass, visceral_fat, bmr, body_age, bmi))
    conn.commit()
    conn.close()

    return redirect(url_for('progress', username=user))


# Manual Entry for Metrics
@app.route('/manual_entry', methods=['GET', 'POST'])
def manual_entry():
    if request.method == 'POST':
        user = request.form['user']
        weight = request.form['weight']
        height = request.form['height']
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db_connection()
        conn.execute('INSERT INTO metrics (user, weight, height, date) VALUES (?, ?, ?, ?)', (user, weight, height, date))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('manual_entry.html')

# View Progress Comparison
@app.route('/progress/<username>')
def progress(username):
    conn = get_db_connection()
    records = conn.execute('SELECT * FROM metrics WHERE user = ? ORDER BY date DESC', (username,)).fetchall()
    conn.close()

    if len(records) < 2:
        return render_template('progress_report.html', username=username, status="Not enough data yet for progress comparison.", improvements=[])

    latest = records[0]
    previous = records[1]

    improvements = []
    if latest['weight'] < previous['weight']:
        improvements.append('Weight decreased ✅')
    if latest['height'] != previous['height']:
        improvements.append('Height updated 🧬 (growing!)')

    return render_template('progress_report.html', username=username, status="Progress Analyzed!", improvements=improvements)

# User Profile Page
@app.route('/user/<username>')
def user_profile(username):
    conn = get_db_connection()
    metrics = conn.execute('SELECT * FROM metrics WHERE user = ? ORDER BY date DESC', (username,)).fetchall()
    conn.close()
    return render_template('user_profile.html', username=username, metrics=metrics)

if __name__ == '__main__':
    app.run(debug=True)

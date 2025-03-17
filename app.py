from flask import Flask, request, redirect, url_for, render_template, send_from_directory
import os
from werkzeug.utils import secure_filename
import subprocess
import logging

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['RESULT_FOLDER'] = 'results/'
app.config['ALLOWED_EXTENSIONS'] = {'zip', 'txt', 'py', 'js', 'java', 'cpp', 'cs', 'php'}

# Assurez-vous que les dossiers existent
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

# Configurer le logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files and 'url' not in request.form:
        return redirect(request.url)

    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # Analysez le fichier et générez le rapport
            analyze_and_generate_report(file_path)
            return redirect(url_for('results', filename=os.path.splitext(filename)[0]))

    if 'url' in request.form:
        url = request.form['url']
        # Téléchargez le fichier à partir de l'URL et analysez-le
        analyze_url(url)
        return redirect(url_for('results', filename='url_result'))

def analyze_and_generate_report(file_path):
    result_folder = os.path.join(app.config['RESULT_FOLDER'], os.path.splitext(os.path.basename(file_path))[0])
    os.makedirs(result_folder, exist_ok=True)
    logger.debug(f"Running analysis for {file_path} in {result_folder}")
    subprocess.run(['python', 'oasis.py', file_path, '--output-dir', result_folder], check=True)
    logger.debug(f"Analysis complete. Checking results in {result_folder}")

def analyze_url(url):
    result_folder = os.path.join(app.config['RESULT_FOLDER'], 'url_result')
    os.makedirs(result_folder, exist_ok=True)
    logger.debug(f"Running analysis for URL {url} in {result_folder}")
    subprocess.run(['python', 'oasis.py', url, '--output-dir', result_folder], check=True)
    logger.debug(f"Analysis complete. Checking results in {result_folder}")

@app.route('/results/<filename>')
def results(filename):
    result_folder = os.path.join(app.config['RESULT_FOLDER'], filename)
    files = os.listdir(result_folder)
    logger.debug(f"Files in result folder: {files}")
    return render_template('results.html', files=files, folder=filename)

@app.route('/download/<folder>/<filename>')
def download_file(folder, filename):
    result_folder = os.path.join(app.config['RESULT_FOLDER'], folder)
    return send_from_directory(result_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

import os
import requests
import json
from threading import Thread

from elastic import add_doc, process_query
from parse_pdf import parse_pdf_to_paragraphs
from configs import WORKING_DIR

app = Flask(__name__)

UPLOAD_FOLDER = 'pdfs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024



@app.route('/upload', methods=['POST'])
def upload_pdf():
    file = request.files.get('file')
    file_url = request.form.get('file_url')

    if not file and not file_url:
        return jsonify({"error": "No file or file URL provided"}), 400
    
    if file:
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if not file or not file.filename.endswith('.pdf'):
            return jsonify({"error": "Invalid file format, only PDF allowed"}), 400

        filename = secure_filename(file.filename)
        pdf_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_filepath)
    elif file_url:
        try:
            response = requests.get(file_url)
            response.raise_for_status()
            filename = file_url.split("/")[-1]
            pdf_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            with open(pdf_filepath, 'wb') as f:
                f.write(response.content)
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Failed to download the file: {str(e)}"}), 400

    with open(os.path.join(WORKING_DIR, 'tmp', 'last_task'), 'r') as f:
        task_id = int(f.readline()) + 1
    with open(os.path.join(WORKING_DIR, 'tmp', 'last_task'), 'w') as f:
        f.write(str(task_id))

    def generate_progress():
        tmp_filepath = os.path.join(WORKING_DIR, 'tmp', f"{task_id}.json")
        parse_pdf_gen = parse_pdf_to_paragraphs(pdf_filepath)
        for pdf_parsing_progress in parse_pdf_gen:
            with open(tmp_filepath, 'w') as f:
                f.write(json.dumps({'pdf_parsing_progress': pdf_parsing_progress, 'adding_doc_to_elastic_progress': 0}))
            if pdf_parsing_progress == 100: break
        json_filepath = next(parse_pdf_gen)

        last_adding_doc_to_elastic_progress = 0
        for adding_doc_to_elastic_progress in add_doc(json_filepath):
            if adding_doc_to_elastic_progress == last_adding_doc_to_elastic_progress:
                continue

            with open(tmp_filepath, 'w') as f:
                f.write(json.dumps({'pdf_parsing_progress': 100, 'adding_doc_to_elastic_progress': adding_doc_to_elastic_progress}))
        os.remove(tmp_filepath)
    
    thread = Thread(target=generate_progress)
    thread.start()

    return jsonify({"message": "File uploaded successfully, processing started", "task_id": task_id}), 200


@app.route('/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    progress_file_path = os.path.join(WORKING_DIR, 'tmp', f"{task_id}.json")

    if not os.path.exists(progress_file_path):
        with open(os.path.join(WORKING_DIR, 'tmp', 'last_task'), 'r') as f:
            last_task_id = int(f.readline())
        if int(task_id) < last_task_id:
            return jsonify(json.dumps({'pdf_parsing_progress': 100, 'adding_doc_to_elastic_progress': 100})), 200
        return jsonify({"error": "Task not found or not started yet"}), 404
    
    with open(progress_file_path, 'r', encoding='utf-8') as progress_file:
        progress_data = json.load(progress_file)
    return jsonify(progress_data)


@app.route('/search', methods=['POST'])
def search():
    user_query = request.json.get('query')
    
    if not (user_query):
        return jsonify({"error": "No query provided"}), 400
    
    results = process_query(user_query)
    
    return jsonify({"results": results}), 200


if __name__ == '__main__':
    app.run(debug=True)

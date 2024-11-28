import os
import json
from threading import Thread
import asyncio
import redis

import aiohttp
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from elastic import add_doc, process_query
from parse_pdf import parse_pdf_to_paragraphs


app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'pdfs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)


@app.route('/upload', methods=['POST'])
async def upload_pdf():
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
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url, timeout=60) as response:
                    response.raise_for_status()
                    filename = file_url.split("/")[-1]
                    pdf_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    with open(pdf_filepath, 'wb') as f:
                        f.write(await response.read())
        except asyncio.TimeoutError:
            return jsonify({"error": f"File download attempt timeout"}), 400
        except aiohttp.ClientError as e:
            return jsonify({"error": f"Failed to download the file: {str(e)}"}), 400

    task_id = redis_client.incr("last_task_id")
    redis_client.set(f"task:{task_id}:progress", json.dumps({
        'pdf_parsing_progress': 0,
        'adding_doc_to_elastic_progress': 0
    }))

    def generate_progress():
        parse_pdf_gen = parse_pdf_to_paragraphs(pdf_filepath)
        for pdf_parsing_progress in parse_pdf_gen:
            redis_client.set(f"task:{task_id}:progress", json.dumps({
                'pdf_parsing_progress': pdf_parsing_progress,
                'adding_doc_to_elastic_progress': 0
            }))

            if pdf_parsing_progress == 100: break
        documents = next(parse_pdf_gen)

        last_adding_doc_to_elastic_progress = 0
        for adding_doc_to_elastic_progress in add_doc(documents):
            if adding_doc_to_elastic_progress == last_adding_doc_to_elastic_progress:
                continue

            redis_client.set(f"task:{task_id}:progress", json.dumps({
                'pdf_parsing_progress': 100,
                'adding_doc_to_elastic_progress': adding_doc_to_elastic_progress
            }))
        redis_client.delete(f"task:{task_id}:progress")
    
    thread = Thread(target=generate_progress)
    thread.start()

    return jsonify({"message": "File uploaded successfully, processing started", "task_id": task_id}), 200


@app.route('/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    progress_data = redis_client.get(f"task:{task_id}:progress")
    if not progress_data:
        last_task_id = int(redis_client.get("last_task_id") or 0)
        if int(task_id) <= last_task_id:
            return jsonify({'pdf_parsing_progress': 100, 'adding_doc_to_elastic_progress': 100}), 200
        return jsonify({"error": "Task not found or not started yet"}), 404
    
    return jsonify(json.loads(progress_data))


@app.route('/search', methods=['POST'])
def search():
    user_query = request.json.get('query')
    
    if not (user_query):
        return jsonify({"error": "No query provided"}), 400
    
    results = process_query(user_query)
    
    return jsonify({"results": results}), 200


if __name__ == '__main__':
    app.run(debug=True)

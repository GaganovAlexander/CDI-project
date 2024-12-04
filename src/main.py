from quart import Quart, jsonify, request
from quart_cors import cors

from .elastic import wait_for_elastic, create_index, process_query
from .configs import UPLOAD_FOLDER, MAX_CONTENT_LENGTH
from .redis import get_task_progress
from .files_processing import process_file, process_file_url

import os


app = Quart(__name__)
cors(app)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


@app.before_serving
async def on_startup():
    await wait_for_elastic()
    await create_index()


@app.route("/upload", methods=["POST"])
async def upload_pdf():
    files = await request.files
    file = files.get("file")
    form = await request.form
    file_url = form.get("file_url")

    if not file and not file_url:
        return jsonify({"error": "No file or file URL provided"}), 400
    
    if file:
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if not file or not file.filename.endswith('.pdf'):
            return jsonify({"error": "Invalid file format, only PDF allowed"}), 400
        
        return await process_file(file)

    elif file_url:
        return await process_file_url(file_url)


@app.route("/progress/<int:task_id>", methods=["GET"])
async def get_progress(task_id):
    progress = await get_task_progress(task_id)
    if progress is None:
        return jsonify({"error": "Task not found or not started yet"}), 404
    return jsonify(progress), 200

@app.route("/search", methods=["POST"])
async def search():
    data = await request.json
    user_query = data.get("query")
    
    if not (user_query):
        return jsonify({"error": "No query provided"}), 400
    
    results = await process_query(user_query)
    return jsonify({"results": results}), 200

if __name__ == "__main__":
    app.run(debug=True)
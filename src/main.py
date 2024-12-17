from quart import Quart, jsonify, request
from quart_cors import cors

from .elastic import wait_for_elastic, create_index, process_query
from .configs import UPLOAD_FOLDER, MAX_CONTENT_LENGTH
from .redis import get_task_progress, close_connection
from .files_processing import process_file, process_file_url
from .utils import cache_response

import os


app = Quart(__name__)
cors(app)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


@app.before_serving
async def on_startup():
    await wait_for_elastic()
    await create_index()


@app.route("/api/upload", methods=["POST"])
async def upload_pdf():
    files = await request.files
    file = files.get("file")
    form = await request.form
    file_url = form.get("file_url")

    if not file and not file_url:
        return jsonify({"error": "No file or file URL provided"}), 400
    
    if file:
        return await process_file(file)

    elif file_url:
        return await process_file_url(file_url)


@app.route("/api/progress/<int:task_id>", methods=["GET"])
async def get_progress(task_id):
    progress = await get_task_progress(task_id)
    if progress is None:
        return jsonify({"error": "Task not found or not started yet"}), 404
    return jsonify(progress), 200


@app.route("/api/search", methods=["POST"])
@cache_response()
async def search():
    data = await request.json
    user_query = data.get("query")
    
    if not (user_query):
        return jsonify({"error": "No query provided"}), 400
    
    results = await process_query(user_query)
    return jsonify({"results": results}), 200


@app.after_serving
async def on_startup():
    await close_connection()


if __name__ == "__main__":
    app.run(debug=True)
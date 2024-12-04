import os
from hashlib import md5
import asyncio
import aiofiles

from werkzeug.datastructures import FileStorage
from quart import jsonify
import aiohttp

from .configs import UPLOAD_FOLDER
from .redis import check_file, set_task_progress, delete_task_progress, get_last_task_id
from .parse_pdf import parse_pdf_to_paragraphs
from .elastic import add_doc


async def process_file(file: FileStorage):
    if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

    if not file or not file.filename.endswith('.pdf'):
        return jsonify({"error": "Invalid file format, only PDF allowed"}), 400

    md5_hash = md5()
    file_chunks = []
    for chunk in file.stream:
        md5_hash.update(chunk)
        file_chunks.append(chunk)
    file_hash = md5_hash.hexdigest()

    filename_redis = await check_file(file_hash, file.filename)
    if filename_redis is not None: 
         return jsonify({"error": f"File has already been uploaded with name: {filename_redis}"}), 409
    
    pdf_filepath = os.path.join(UPLOAD_FOLDER, file.filename)

    async with aiofiles.open(pdf_filepath, 'wb') as f:
        for chunk in file_chunks:
            await f.write(chunk)

    task_id = await get_last_task_id(increment=True)
    asyncio.create_task(parse_pdf(task_id, pdf_filepath))

    return jsonify({"message": "File uploaded successfully, processing started", "task_id": task_id}), 200


async def process_file_url(file_url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url, timeout=60) as response:
                response.raise_for_status()
                filename = file_url.split("/")[-1]
                pdf_filepath = os.path.join(UPLOAD_FOLDER, filename)
                
                async with aiofiles.open(pdf_filepath, 'wb') as f:
                    await f.write(await response.read())
    except asyncio.TimeoutError:
        return jsonify({"error": f"File download attempt timeout"}), 400
    except aiohttp.ClientError as e:
        return jsonify({"error": f"Failed to download the file: {str(e)}"}), 400
    
    task_id = await get_last_task_id(increment=True)
    asyncio.create_task(parse_pdf(task_id, pdf_filepath))

    return jsonify({"message": "File uploaded successfully, processing started", "task_id": task_id}), 200


async def parse_pdf(task_id, pdf_filepath) -> None:
    parse_pdf_gen = parse_pdf_to_paragraphs(pdf_filepath)
    stop = False
    async for pdf_parsing_progress in parse_pdf_gen:
        if stop:
             documents = pdf_parsing_progress
             break
        await set_task_progress(task_id, pdf_parsing_progress=pdf_parsing_progress)
        stop = pdf_parsing_progress == 100

    last_adding_doc_to_elastic_progress = 0
    async for adding_doc_to_elastic_progress in add_doc(documents):
        if adding_doc_to_elastic_progress == last_adding_doc_to_elastic_progress:
            continue
        last_adding_doc_to_elastic_progress = adding_doc_to_elastic_progress
        await set_task_progress(task_id, pdf_parsing_progress=100, adding_doc_to_elastic_progress=adding_doc_to_elastic_progress)

    await delete_task_progress(task_id)



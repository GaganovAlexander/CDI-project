import json

import redis.asyncio as redis

from .configs import REDIS_PORT


redis_client = redis.Redis(host="redis", port=REDIS_PORT, decode_responses=True)


async def get_last_task_id(increment=False) -> int:
    if increment:
        return await redis_client.incr("last_task_id")
    return int(await redis_client.get("last_task_id") or 0)


async def set_task_progress(task_id: int, *, pdf_parsing_progress = 0, adding_doc_to_elastic_progress = 0) -> None:
    await redis_client.set(f"task:{task_id}:progress", json.dumps({
                "pdf_parsing_progress": pdf_parsing_progress,
                "adding_doc_to_elastic_progress": adding_doc_to_elastic_progress
            }))
    
async def get_task_progress(task_id: int):
    progress_data = await redis_client.get(f"task:{task_id}:progress")
    if progress_data:
        return json.loads(progress_data)
    
    last_task_id = await get_last_task_id()
    if task_id <= last_task_id:
        return {"pdf_parsing_progress": 100, "adding_doc_to_elastic_progress": 100}
    return None

async def delete_task_progress(task_id: int) -> None:
    await redis_client.delete(f"task:{task_id}:progress")

async def check_file(hash: str, filename: str) -> str:
    filename_redis = await redis_client.get(f"file:{hash}")
    if filename_redis:
        return filename_redis
    await redis_client.set(f"file:{hash}", filename)
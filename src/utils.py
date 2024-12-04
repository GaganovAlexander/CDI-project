import asyncio
from functools import wraps
import hashlib
import json

from quart import request, jsonify

from .redis import redis_client


def cache_response(expiration=60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):        
            request_data = f"{request.method}:{request.path}:{await request.get_data(as_text=True)}"
            cache_key = hashlib.sha256(request_data.encode()).hexdigest()
        
            cached_response = await redis_client.get(f"request:{cache_key}")
            if cached_response:            
                return jsonify(json.loads(cached_response)), 200
        
            response = await func(*args, **kwargs)

            if response[1] == 200:
                response_data = await response[0].get_json()
                await redis_client.setex(f"request:{cache_key}", expiration, json.dumps(response_data))

            return response
        return wrapper
    return decorator

def make_async(func):
    async def inner(*args):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, func, *args)
        return result
    return inner

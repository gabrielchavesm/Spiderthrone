import os
import json
from redis import Redis
from typing import List, Dict

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_session_history(session_id: str) -> List[Dict[str, str]]:
    key = f"chat_session:{session_id}"
    history_json = redis_client.get(key)
    if history_json:
        try:
            return json.loads(history_json)
        except json.JSONDecodeError:
            return []
    return []

def save_session_history(session_id: str, history: List[Dict[str, str]]):
    key = f"chat_session:{session_id}"
    redis_client.setex(
        name=key,
        time=86400,  # 24 horas
        value=json.dumps(history)
    )
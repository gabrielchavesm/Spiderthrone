import json
import os

from redis import Redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def get_session_history(session_id: str) -> list[dict[str, str]]:
    key = f"chat_session:{session_id}"
    history_json = redis_client.get(key)
    if history_json:
        try:
            return json.loads(history_json)
        except json.JSONDecodeError:
            return []
    return []


def save_session_history(session_id: str, history: list[dict[str, str]]):
    key = f"chat_session:{session_id}"
    redis_client.setex(
        name=key,
        time=86400,  # 24 horas
        value=json.dumps(history),
    )

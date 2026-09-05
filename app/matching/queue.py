import json
import logging
from datetime import datetime

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


async def enqueue_matching_job(incident_id: str) -> bool:
    """
    Safely enqueues a matching job for the given incident to Redis.
    Handles unavailability gracefully to prevent breaking the API.
    """
    try:
        redis = await get_redis()
        payload = {
            "incident_id": str(incident_id),
            "action": "match",
            "timestamp": datetime.utcnow().isoformat(),
        }
        await redis.lpush("matching_queue", json.dumps(payload))
        return True
    except Exception as e:
        logger.warning("[MATCHING_QUEUE] Redis unavailable, could not enqueue for %s: %s", incident_id, e)
        return False

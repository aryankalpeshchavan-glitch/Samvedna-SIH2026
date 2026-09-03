"""
Sensor Health Classification Service
====================================
Computes dynamic health status (ONLINE, STALE, OFFLINE) from sensor last_seen
timestamp using configurable threshold settings.
"""
from datetime import datetime
from typing import Optional

from app.core.config import settings


def compute_sensor_health(last_seen: Optional[datetime], now: Optional[datetime] = None) -> str:
    """
    Derives sensor health status from last_seen:
    - None -> OFFLINE
    - age <= SENSOR_STALE_TIMEOUT_SECONDS -> ONLINE
    - SENSOR_STALE_TIMEOUT_SECONDS < age <= SENSOR_OFFLINE_TIMEOUT_SECONDS -> STALE
    - age > SENSOR_OFFLINE_TIMEOUT_SECONDS -> OFFLINE
    """
    if not last_seen:
        return "OFFLINE"

    if now is None:
        now = datetime.utcnow()

    # Normalize to naive UTC for comparison
    now_naive = now.replace(tzinfo=None) if now.tzinfo is not None else now
    seen_naive = last_seen.replace(tzinfo=None) if last_seen.tzinfo is not None else last_seen

    age_seconds = (now_naive - seen_naive).total_seconds()
    if age_seconds < 0:
        age_seconds = 0.0

    if age_seconds <= settings.SENSOR_STALE_TIMEOUT_SECONDS:
        return "ONLINE"
    elif age_seconds <= settings.SENSOR_OFFLINE_TIMEOUT_SECONDS:
        return "STALE"
    else:
        return "OFFLINE"

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    checks = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {str(e)}"

    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    try:
        queue_len = await redis.llen("notification_queue")
        checks["notification_queue_depth"] = queue_len
    except Exception:
        checks["notification_queue_depth"] = "unknown"

    healthy = all(v == "ok" for k, v in checks.items() if k in ("db", "redis"))

    # Import here to avoid circular import; version is set on the FastAPI app instance.
    from app.main import app as _app
    return {
        "status": "healthy" if healthy else "degraded",
        "version": getattr(_app, "version", "0.1.0"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }

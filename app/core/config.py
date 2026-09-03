import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Settings:
    PROJECT_NAME: str = "CrisisCore"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'crisiscore.db')}",
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "crisiscore-dev-secret-change-in-prod")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    NOTIFICATION_PROVIDER: str = os.getenv("NOTIFICATION_PROVIDER", "console")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")
    FCM_SERVER_KEY: str = os.getenv("FCM_SERVER_KEY", "")

    RISK_API_URL: str = os.getenv("RISK_API_URL", "")

    AUTO_REASSIGN_MINUTES: int = int(os.getenv("AUTO_REASSIGN_MINUTES", "5"))
    ASSIGNMENT_ACK_TIMEOUT_SECONDS: int = int(
        os.getenv("ASSIGNMENT_ACK_TIMEOUT_SECONDS", str(int(os.getenv("AUTO_REASSIGN_MINUTES", "5")) * 60))
    )
    VOLUNTEER_HEARTBEAT_TIMEOUT_MINUTES: int = int(os.getenv("VOLUNTEER_HEARTBEAT_TIMEOUT_MINUTES", "30"))
    
    RISK_FRESHNESS_MINUTES: int = int(os.getenv("RISK_FRESHNESS_MINUTES", "60"))

    # Sensor health & liveness timeouts
    SENSOR_STALE_TIMEOUT_SECONDS: int = int(os.getenv("SENSOR_STALE_TIMEOUT_SECONDS", "300"))
    SENSOR_OFFLINE_TIMEOUT_SECONDS: int = int(os.getenv("SENSOR_OFFLINE_TIMEOUT_SECONDS", "1800"))
    SENSOR_CLOCK_SKEW_TOLERANCE_SECONDS: int = int(os.getenv("SENSOR_CLOCK_SKEW_TOLERANCE_SECONDS", "60"))

    # Operational Priority Engine weights — must sum to 1.0
    PRIORITY_W_RISK: float = float(os.getenv("PRIORITY_W_RISK", "0.35"))
    PRIORITY_W_EXPOSURE: float = float(os.getenv("PRIORITY_W_EXPOSURE", "0.30"))
    PRIORITY_W_VULNERABILITY: float = float(os.getenv("PRIORITY_W_VULNERABILITY", "0.20"))
    PRIORITY_W_RESPONSE_GAP: float = float(os.getenv("PRIORITY_W_RESPONSE_GAP", "0.15"))

    # CORS — comma-separated or JSON list of allowed origins.
    # Defaults to ["*"] for local development.
    # In production, set: CORS_ORIGINS='["https://your-domain.com"]'
    @property
    def CORS_ORIGINS(self) -> list[str]:
        raw = os.getenv("CORS_ORIGINS", "[\"*\"]")
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        # Fallback: treat as a plain string
        return [raw.strip()]


settings = Settings()

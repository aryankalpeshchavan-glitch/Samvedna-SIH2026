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


settings = Settings()

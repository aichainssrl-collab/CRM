from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Firebase / GCP
    FIREBASE_PROJECT_ID: str = "aichain-crm-dev"
    FIREBASE_STORAGE_BUCKET: str = "aichain-crm-dev.appspot.com"
    FIRESTORE_DATABASE_ID: str = "(default)"
    GOOGLE_APPLICATION_CREDENTIALS_JSON: Optional[str] = None

    # Cloud Tasks
    GCP_LOCATION: str = "europe-west1"
    CLOUD_TASKS_QUEUE: str = "crm-tasks"
    BACKEND_INTERNAL_URL: str = "http://localhost:8000"

    # Email
    RESEND_API_KEY: str = "re_fake_key"
    EMAIL_FROM: str = "noreply@aichainsolutions.net"

    # Security
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    RATE_LIMIT_PER_MINUTE: int = 60

    # Feature
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

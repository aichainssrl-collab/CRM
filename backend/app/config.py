from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "crm-aichain-db"

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

    # Company block for PDF proposals/invoices
    COMPANY_NAME: str = "AiChain Solutions"
    COMPANY_ADDRESS: str = "Catania, Italia"
    COMPANY_EMAIL: str = "info@aichainsolutions.net"
    COMPANY_VAT_ID: str = ""
    COMPANY_IBAN: str = ""

    # Documents (PDF snapshots)
    DEFAULT_TAX_RATE: float = 22.0

    # WhatsApp Cloud API (empty = mock mode)
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "aichain-wa-verify"
    WHATSAPP_API_VERSION: str = "v20.0"

    # Security
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    RATE_LIMIT_PER_MINUTE: int = 60

    # Meta Ads
    META_ACCESS_TOKEN: Optional[str] = None
    META_AD_ACCOUNT_ID: Optional[str] = None  # formato: act_XXXXXXXXX
    META_API_VERSION: str = "v19.0"

    # LLM Marketing Agent (multi-provider)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai"  # openai | anthropic | gemini | ollama | custom
    LLM_MODEL: str = "gpt-4o"  # gpt-4o | claude-sonnet-4-20250514 | gemini/gemini-2.0-flash | qwen3:4b | ecc.
    LLM_BASE_URL: Optional[str] = None  # per endpoint custom/OpenAI-compatible
    # Modello locale (Ollama) per task leggeri — risparmia token API
    LLM_LOCAL_PROVIDER: str = "ollama"
    LLM_LOCAL_MODEL: str = "qwen3:4b"  # modello per suggerimenti, task semplici
    LLM_LOCAL_BASE_URL: str = "http://localhost:11434"
    MARKETING_SKILLS_DIR: str = "/Users/fred/.claude/plugins/marketplaces/marketingskills/skills"

    # Feature
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

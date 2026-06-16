import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-2025-04-14")
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))
OPENAI_HISTORY_LIMIT = int(os.getenv("OPENAI_HISTORY_LIMIT", "20"))

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
_JWT_EXPIRY_DAYS = 30

AI_RATE_LIMIT = int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "20"))
_ai_rate_store: dict[str, list[float]] = {}

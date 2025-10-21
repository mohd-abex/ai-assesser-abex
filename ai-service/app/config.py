from functools import lru_cache
from typing import List, Optional
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load .env early
load_dotenv()


def _get_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def _get_list(value: Optional[str], default: List[str]) -> List[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    ai_env: str
    default_tier: str
    groq_api_key: Optional[str]
    edge_tts_enabled: bool
    allowed_origins: List[str]


@lru_cache()
def get_settings() -> Settings:
    return Settings(
        ai_env=os.getenv("AI_ENV", "development"),
        default_tier=os.getenv("DEFAULT_TIER", "essential"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        edge_tts_enabled=_get_bool(os.getenv("EDGE_TTS_ENABLED"), True),
        allowed_origins=_get_list(os.getenv("ALLOWED_ORIGINS"), ["http://localhost:3000"]),
    )


settings = get_settings()

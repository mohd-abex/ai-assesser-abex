"""
Configuration management for InterviewAI service.

This module handles all application configuration including environment variables,
API keys, feature flags, and logging setup. Configuration is loaded from environment
variables with sensible defaults and validation.
"""

from functools import lru_cache
from typing import List, Optional
from dataclasses import dataclass
import os
import logging
from dotenv import load_dotenv

# Load .env early to ensure environment variables are available
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


def _get_bool(value: Optional[str], default: bool) -> bool:
    """
    Convert a string environment variable to boolean.
    
    Args:
        value: String value from environment variable
        default: Default boolean value if not set
        
    Returns:
        Boolean representation of the value
        
    Examples:
        >>> _get_bool("true", False)
        True
        >>> _get_bool("0", True)
        False
        >>> _get_bool(None, True)
        True
    """
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def _get_list(value: Optional[str], default: List[str]) -> List[str]:
    """
    Convert a comma-separated string to a list of strings.
    
    Args:
        value: Comma-separated string from environment variable
        default: Default list if value is empty or None
        
    Returns:
        List of trimmed non-empty strings
        
    Examples:
        >>> _get_list("a,b,c", [])
        ['a', 'b', 'c']
        >>> _get_list("a, , b", [])
        ['a', 'b']
        >>> _get_list(None, ["default"])
        ['default']
    """
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def _validate_environment(env: str) -> str:
    """
    Validate the AI_ENV environment variable.
    
    Args:
        env: Environment name
        
    Returns:
        Validated environment name
        
    Raises:
        ConfigurationError: If environment is not in allowed values
    """
    allowed_envs = ["development", "staging", "production", "test"]
    if env not in allowed_envs:
        raise ConfigurationError(
            f"Invalid AI_ENV '{env}'. Must be one of: {', '.join(allowed_envs)}"
        )
    return env


def _validate_tier(tier: str) -> str:
    """
    Validate the DEFAULT_TIER configuration.
    
    Args:
        tier: Tier name
        
    Returns:
        Validated tier name
        
    Raises:
        ConfigurationError: If tier is not in allowed values
    """
    allowed_tiers = ["essential", "professional", "enterprise"]
    if tier not in allowed_tiers:
        raise ConfigurationError(
            f"Invalid DEFAULT_TIER '{tier}'. Must be one of: {', '.join(allowed_tiers)}"
        )
    return tier


def _validate_api_key(key: Optional[str], key_name: str) -> Optional[str]:
    """
    Validate API key format and presence.
    
    Args:
        key: API key value
        key_name: Name of the API key for error messages
        
    Returns:
        Validated API key or None
        
    Note:
        BUG #1: This function accepts empty strings as valid API keys.
        Empty strings should be treated as None/missing, but currently
        they pass validation. This could cause runtime errors when the
        API key is actually used.
    """
    if key is not None:
        # BUG: Should check if key.strip() is empty and treat as None
        # Currently accepts "" as a valid key
        if len(key) < 10 and key != "":
            logger.warning(
                f"{key_name} appears to be too short. "
                f"Expected at least 10 characters, got {len(key)}."
            )
        return key
    return None


@dataclass
class Settings:
    """
    Application settings loaded from environment variables.
    
    Attributes:
        ai_env: Current environment (development, staging, production, test)
        default_tier: Default service tier for new users
        groq_api_key: API key for Groq AI service
        edge_tts_enabled: Whether Edge TTS is enabled
        allowed_origins: List of allowed CORS origins
    """
    ai_env: str
    default_tier: str
    groq_api_key: Optional[str]
    edge_tts_enabled: bool
    allowed_origins: List[str]
    
    def __post_init__(self):
        """Validate settings after initialization."""
        logger.info(f"Initialized settings for environment: {self.ai_env}")
        logger.info(f"Default tier: {self.default_tier}")
        logger.info(f"Edge TTS enabled: {self.edge_tts_enabled}")
        logger.info(f"Allowed origins: {len(self.allowed_origins)} configured")
        
        if self.groq_api_key:
            logger.info("Groq API key: configured")
        else:
            logger.warning("Groq API key: NOT configured")


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Settings are loaded once and cached for the lifetime of the application.
    This function validates all configuration values and raises ConfigurationError
    if any validation fails.
    
    Returns:
        Settings instance with validated configuration
        
    Raises:
        ConfigurationError: If any configuration validation fails
    """
    logger.info("Loading application settings...")
    
    try:
        ai_env = _validate_environment(os.getenv("AI_ENV", "development"))
        default_tier = _validate_tier(os.getenv("DEFAULT_TIER", "essential"))
        groq_api_key = _validate_api_key(os.getenv("GROQ_API_KEY"), "GROQ_API_KEY")
        edge_tts_enabled = _get_bool(os.getenv("EDGE_TTS_ENABLED"), True)
        allowed_origins = _get_list(
            os.getenv("ALLOWED_ORIGINS"), 
            ["http://localhost:3000"]
        )
        
        return Settings(
            ai_env=ai_env,
            default_tier=default_tier,
            groq_api_key=groq_api_key,
            edge_tts_enabled=edge_tts_enabled,
            allowed_origins=allowed_origins,
        )
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading settings: {e}")
        raise ConfigurationError(f"Failed to load settings: {e}") from e


# Global settings instance
settings = get_settings()

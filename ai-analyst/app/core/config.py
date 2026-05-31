from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env-ai-analyst",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ADK / Gemini — read by google-adk automatically from env
    google_api_key: str = ""
    google_genai_use_vertexai: str = "FALSE"
    gemini_model: str = "gemini-2.0-flash"

    # Service
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    cors_origins: str = "http://localhost:3000,http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()

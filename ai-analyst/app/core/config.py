from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv(".env-ai-analyst", override=True)


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
    gemini_model: str = "gemini-2.5-flash-lite"

    # CubeJS
    cubejs_url: str = "http://cubejs.pm.comsatel.com.pe:4000/cubejs-api/v1/load" # "http://cube_api:4000/v1/load"
    cubejs_api_secret: str = "welcome1"

    # Skills
    skills_catalog_url: str = "https://raw.githubusercontent.com/ianache/skills-catalog/main/catalog.yaml"

    # Service
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    cors_origins: str = "http://localhost:3000,http://localhost:5173"


import os

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.google_api_key:
        os.environ["GOOGLE_API_KEY"] = settings.google_api_key
    return settings

# Trigger reload for API key update

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "biportal"
    postgres_password: str = "biportal"
    postgres_db: str = "biportal"
    postgres_schema: str = "biportal"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Keycloak
    keycloak_url: str = "https://oauth2.qa.comsatel.com.pe"
    keycloak_realm: str = "Apps"
    keycloak_client_id: str = "bi-backend"
    keycloak_client_secret: str = ""

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"

    @property
    def keycloak_token_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/token"

    @property
    def keycloak_userinfo_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/userinfo"

    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # CORS — keep as str so pydantic-settings never tries to JSON-decode it
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:9000"

    @classmethod
    def assemble_cors_origins(cls, v: str) -> list[str]:
        """Convert a raw CORS_ORIGINS string to a list of origins."""
        if not v or not v.strip():
            return []
        v = v.strip()
        if v.startswith("["):
            import json
            try:
                parsed = json.loads(v.replace("'", '"'))
                if isinstance(parsed, list):
                    return [str(o) for o in parsed]
            except Exception:
                pass
        return [o.strip() for o in v.split(",") if o.strip()]

    # Encryption for sensitive data (API tokens, etc.)
    encryption_key: str = "your-secret-encryption-key-change-in-production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
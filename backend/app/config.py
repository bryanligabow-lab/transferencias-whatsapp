from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de datos
    database_url: str = "sqlite:///./data/app.db"

    # Seguridad
    encryption_key: str = ""
    jwt_secret: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 60 * 12
    admin_username: str = "admin"
    admin_password: str = "admin"

    # Zona horaria para el corte diario
    timezone: str = "America/Guayaquil"

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    # URL pública del backend (para webhooks)
    public_base_url: str = "http://localhost:8000"

    # OCR / LLM
    tesseract_cmd: str = "tesseract"
    tesseract_lang: str = "spa+eng"
    parse_mode: str = "rules"  # "rules" | "hybrid"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    media_dir: str = "./data/media"

    @property
    def media_path(self) -> Path:
        p = Path(self.media_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # Asegura carpeta de datos para SQLite
    if settings.database_url.startswith("sqlite"):
        db_file = settings.database_url.split("///")[-1]
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()

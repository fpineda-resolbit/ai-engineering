"""Configuración de la aplicación cargada desde variables de entorno / .env."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Provider = Literal["openai", "anthropic"]

DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    LLM_PROVIDER: Provider = "openai"
    LLM_MODEL: str = ""
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 8000

    # SecretStr evita que las claves aparezcan en logs o en el repr de Settings.
    OPENAI_API_KEY: SecretStr | None = None
    ANTHROPIC_API_KEY: SecretStr | None = None

    APP_ENV: Literal["development", "staging", "production"] = "development"

    @property
    def model(self) -> str:
        """Modelo efectivo: el configurado o el económico por defecto del proveedor."""
        return self.LLM_MODEL or DEFAULT_MODELS[self.LLM_PROVIDER]

    def api_key(self) -> str | None:
        """API key del proveedor seleccionado (None si no está configurada)."""
        key = self.OPENAI_API_KEY if self.LLM_PROVIDER == "openai" else self.ANTHROPIC_API_KEY
        value = key.get_secret_value().strip() if key else ""
        return value or None


@lru_cache
def get_settings() -> Settings:
    return Settings()

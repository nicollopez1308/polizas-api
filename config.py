"""Configuración del servicio.

Los valores se leen de variables de entorno o, si no están definidas, del
archivo .env (que nunca se sube al repositorio). La plantilla con valores de
ejemplo es .env.example.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///app.db"
    secreto_firma: str
    clave_api_reaseguro: str
    ruta_modelo: str = "modelo.pkl"
    umbral_alto_riesgo: float = 0.6


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración; se construye una sola vez y queda en caché."""
    return Settings()
"""Configuración central (pydantic-settings). Espejo del patrón de Arc One.

Todo se lee de variables de entorno (`.env` en local, Secret Manager en Cloud Run).
Un solo lugar para tocar la config; nada hardcodeado en el código.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MINDFUL_", extra="ignore")

    env: str = "development"

    # Base de datos (local Postgres por defecto; Cloud SQL en prod vía Secret Manager).
    database_url: str = "postgresql+psycopg://mindful:mindful@localhost:5432/mindful"

    # Auth: dev = sin token (local) | firebase = valida Firebase ID token.
    auth_mode: str = "dev"
    google_cloud_project: str = ""

    # CORS para la PWA / app (Expo dev server).
    cors_origins: str = "http://localhost:8081,http://localhost:19006,http://127.0.0.1:8081"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

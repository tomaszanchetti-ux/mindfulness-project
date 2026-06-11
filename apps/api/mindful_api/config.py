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

    # Fotos (M3/M4): local = disco (dev/tests) | gcs = bucket privado Cloud Storage.
    storage_mode: str = "local"
    storage_dir: str = "var/fotos"  # raíz del modo local (relativa a apps/api)
    fotos_bucket: str = ""  # nombre del bucket en modo gcs

    # Aviso diario por email (WS20). off = no manda (dev/tests) | log = imprime
    # a stdout (debug) | smtp = envío real (SendGrid u otro relay SMTP).
    email_mode: str = "off"
    smtp_host: str = "smtp.sendgrid.net"
    smtp_port: int = 587
    smtp_user: str = "apikey"  # literal "apikey" en SendGrid; la key va en smtp_pass
    smtp_pass: str = ""
    email_from: str = ""  # remitente verificado, ej. "Dwellia <correo@dominio>"
    app_url: str = "https://dwellia-app.web.app"  # destino del CTA del email
    # Secreto compartido con Cloud Scheduler (header X-Aviso-Secret). Vacío = endpoint apagado.
    aviso_secret: str = ""

    # CORS para la PWA / app (Expo dev server).
    cors_origins: str = "http://localhost:8081,http://localhost:19006,http://127.0.0.1:8081"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

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

    # Aviso diario (WS20/WS21). El canal es PUSH WEB (decisión Tomás WS21);
    # el email queda escrito pero dormido (email_mode=off) por si vuelve como respaldo.
    email_mode: str = "off"
    smtp_host: str = "smtp.sendgrid.net"
    smtp_port: int = 587
    smtp_user: str = "apikey"  # literal "apikey" en SendGrid; la key va en smtp_pass
    smtp_pass: str = ""
    email_from: str = ""  # remitente verificado, ej. "Dwellia <correo@dominio>"
    app_url: str = "https://dwellia-app.web.app"  # destino al tocar la notificación
    # Secreto compartido con Cloud Scheduler (header X-Aviso-Secret). Vacío = endpoint apagado.
    aviso_secret: str = ""
    # Push web (WS21): llave VAPID privada (base64url, EC P-256). Vacía = push apagado.
    # La pública (derivada de esta) vive en el front (lib/push.ts) — es pública por diseño.
    vapid_private_key: str = ""
    vapid_sub: str = "mailto:tomaszanchetti@gmail.com"  # contacto VAPID requerido por el estándar

    # Pagos premium (WS24 · A1.2). Se cobra por web con Stripe Checkout, sin tiendas.
    # Sin `stripe_secret_key` los pagos están APAGADOS (dev/tests): checkout y portal
    # devuelven 503 y el front no muestra el botón (lo dice /api/pagos/estado).
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""  # "whsec_…" — firma del webhook; vacío = webhook cerrado
    stripe_price_id: str = ""  # Price de la suscripción ANUAL de 8,99 € ("Dwellia premium")

    # CORS para la PWA / app (Expo dev server).
    cors_origins: str = "http://localhost:8081,http://localhost:19006,http://127.0.0.1:8081"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

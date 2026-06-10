"""Dónde viven los archivos de las fotos (la DB guarda solo `storage_path`).

Dos modos, espejo del patrón auth dev/firebase:
- local (default): disco, bajo MINDFUL_STORAGE_DIR. Para dev y tests.
- gcs: bucket PRIVADO de Cloud Storage (MINDFUL_FOTOS_BUCKET). El cliente viene
  con firebase-admin; las credenciales son la service account de Cloud Run.

`storage_path` canónico, igual en ambos modos:
    fotos/{usuario_id}/{entrega_id}/{foto_id}.{ext}
— carpeta por usuario, como canonizó M4: el aislamiento también vive en Storage.
Las fotos NUNCA son públicas: siempre se sirven a través de la API (con login).
"""

from __future__ import annotations

from pathlib import Path

from ..config import settings

# Formatos que aceptamos (lo que producen los file inputs móviles/desktop).
_EXT = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/heic": "heic",
    "image/heif": "heif",
}
_MIME = {ext: mime for mime, ext in _EXT.items()}
_MIME["jpeg"] = "image/jpeg"


def extension_para(content_type: str | None) -> str | None:
    """La extensión canónica para un content-type, o None si no es imagen soportada."""
    return _EXT.get((content_type or "").lower())


def mime_de(storage_path: str) -> str:
    """El content-type al servir, derivado de la extensión guardada."""
    ext = storage_path.rsplit(".", 1)[-1].lower()
    return _MIME.get(ext, "application/octet-stream")


def ruta_canonica(usuario_id: str, entrega_id: str, foto_id: str, ext: str) -> str:
    return f"fotos/{usuario_id}/{entrega_id}/{foto_id}.{ext}"


def _bucket():
    from google.cloud import storage as gcs  # viene con firebase-admin

    return gcs.Client().bucket(settings.fotos_bucket)


def guardar(storage_path: str, contenido: bytes, content_type: str) -> None:
    if settings.storage_mode == "gcs":
        _bucket().blob(storage_path).upload_from_string(
            contenido, content_type=content_type
        )
        return
    p = Path(settings.storage_dir) / storage_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(contenido)


def leer(storage_path: str) -> bytes | None:
    """El contenido del archivo, o None si ya no existe."""
    if settings.storage_mode == "gcs":
        try:
            return _bucket().blob(storage_path).download_as_bytes()
        except Exception:
            return None
    p = Path(settings.storage_dir) / storage_path
    return p.read_bytes() if p.exists() else None


def borrar(storage_paths: list[str]) -> None:
    """Best effort: un archivo que ya no está no debe frenar el borrado de la fila."""
    for sp in storage_paths:
        try:
            if settings.storage_mode == "gcs":
                _bucket().blob(sp).delete()
            else:
                (Path(settings.storage_dir) / sp).unlink(missing_ok=True)
        except Exception:
            pass

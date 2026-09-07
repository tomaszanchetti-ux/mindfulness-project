"""Autenticación. Dos modos (espejo del patrón de Arc One):

  dev      → sin token. Simula un usuario con headers X-Debug-* (default dev|user).
             Para construir y testear local sin Firebase.
  firebase → valida el Firebase ID token del header Authorization: Bearer <token>.
             Extrae uid (sub) + email. Se activa con MINDFUL_AUTH_MODE=firebase.

EL AISLAMIENTO EMPIEZA ACÁ: toda request resuelve UN usuario, y el resto de la API
filtra por su id. El cliente nunca elige de quién son los datos.

Auto-provisión: la primera vez que un uid de Firebase entra, se crea su fila
`usuarios`. El onboarding (M1) después completa categorías + horario + términos.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db.base import get_session
from .db.models import Usuario

# Identidad por defecto en modo dev (espejo de ARC_ONE_SEED_ADMIN_SUB=dev|user).
DEV_SUB = "dev|user"
DEV_EMAIL = "dev@mindful.local"


class Identidad:
    """Lo que un IdP (o el modo dev) afirma sobre quién hace la request."""

    def __init__(self, sub: str, email: str):
        self.sub = sub
        self.email = email


# ── Resolver la identidad según el modo ──────────────────────────────────────
_firebase_ready = False


def _ensure_firebase():
    global _firebase_ready
    if _firebase_ready:
        return
    import firebase_admin
    from firebase_admin import credentials  # noqa: F401

    if not firebase_admin._apps:
        # En Cloud Run usa las credenciales del entorno (ADC). Sin args = default.
        firebase_admin.initialize_app()
    _firebase_ready = True


def _identidad_dev(x_debug_sub: Optional[str], x_debug_email: Optional[str]) -> Identidad:
    return Identidad(sub=x_debug_sub or DEV_SUB, email=x_debug_email or DEV_EMAIL)


def _identidad_firebase(authorization: Optional[str]) -> Identidad:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token de Firebase")
    token = authorization.split(" ", 1)[1].strip()
    _ensure_firebase()
    from firebase_admin import auth as fb_auth

    try:
        decoded = fb_auth.verify_id_token(token)
    except Exception as exc:  # token inválido / expirado
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido") from exc
    return Identidad(sub=decoded["uid"], email=decoded.get("email", ""))


def get_current_user(
    s: Session = Depends(get_session),
    authorization: Optional[str] = Header(default=None),
    x_debug_sub: Optional[str] = Header(default=None),
    x_debug_email: Optional[str] = Header(default=None),
) -> Usuario:
    """Dependency principal: devuelve el `Usuario` de esta request (auto-provisión)."""
    if settings.auth_mode == "firebase":
        ident = _identidad_firebase(authorization)
    else:
        ident = _identidad_dev(x_debug_sub, x_debug_email)

    usuario = s.scalar(select(Usuario).where(Usuario.firebase_uid == ident.sub))
    if usuario is None:
        usuario = Usuario(firebase_uid=ident.sub, email=ident.email)
        s.add(usuario)
        s.commit()
        s.refresh(usuario)
    return usuario


def get_admin(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """WS27 · B1.3 · Dependency de administración (/api/admin).

    Admin = el `firebase_uid` está en `MINDFUL_ADMIN_UIDS` (CSV). La lista se lee
    EN CADA REQUEST (`settings.admin_uids_list`), nunca al importar: así cambiarla
    en Cloud Run (o en un test) tiene efecto sin reiniciar nada. Lista vacía =
    NADIE es admin, que es el default seguro: /api/admin nace cerrado.

    Parte de `get_current_user`, o sea que primero resuelve la identidad como
    cualquier otra request (dev o Firebase) y recién después decide el permiso.
    """
    if usuario.firebase_uid not in settings.admin_uids_list:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo administración")
    return usuario

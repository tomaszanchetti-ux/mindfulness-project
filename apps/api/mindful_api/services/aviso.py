"""Aviso diario por email (WS20): "tu carta de hoy te espera".

Cloud Scheduler golpea el endpoint interno cada 15 minutos; este barrido decide
a quién le toca. Regla por usuario (todo en SU hora local, zoneinfo):

  manda si  aviso_activo
        y   onboarding completo (términos aceptados)
        y   su hora local ya pasó la hora elegida (hora_aviso)
        y   hoy todavía no se le mandó (ultimo_aviso_fecha != fecha local)
        y   hoy todavía no guardó su pausa (si ya la vivió, no hay nada que avisar)

Comparar ">= hora_aviso" (y no una ventana exacta de 15') hace el barrido
auto-reparable: si una corrida se pierde, la siguiente del día lo cubre.
El email NO crea la entrega (canon WS15: la carta se revela al abrir la app).
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db.models import Entrega, Usuario
from .email import enviar_email

_TZ_FALLBACK = ZoneInfo("Europe/Madrid")


def _minutos(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _pausa_guardada_hoy(s: Session, usuario: Usuario, tz: ZoneInfo, hoy_local) -> bool:
    entregas = s.scalars(
        select(Entrega).where(Entrega.usuario_id == usuario.id, Entrega.completada.is_(True))
    ).all()
    return any(e.fecha.astimezone(tz).date() == hoy_local for e in entregas)


def _contenido(apodo: str | None) -> tuple[str, str, str]:
    """(asunto, texto plano, html). Simple y cálido; el CTA lleva a la app."""
    nombre = apodo or ""
    saludo = f"Hola, {nombre}." if nombre else "Hola."
    asunto = "Tu carta de hoy te espera"
    url = settings.app_url + "/hoy"
    texto = (
        f"{saludo}\n\n"
        "Tu carta de hoy ya está lista. Ábrela, vive tu pausa lejos del teléfono "
        "y escribe en tu diario lo que sentiste.\n\n"
        f"Abrir mi carta: {url}\n\n"
        "— Dwellia · One quiet pause a day\n"
        "Recibes este aviso porque lo activaste. Puedes apagarlo en tu Perfil."
    )
    html = f"""\
<div style="background:#f7f1e7;padding:32px 16px;font-family:Georgia,'Times New Roman',serif;color:#2f2923">
  <div style="max-width:440px;margin:0 auto;background:#fff8ea;border-radius:24px;padding:32px 28px;text-align:center">
    <p style="font-size:13px;letter-spacing:2px;text-transform:uppercase;color:#756b5e;margin:0 0 18px">Dwellia</p>
    <h1 style="font-size:24px;font-weight:500;font-style:italic;margin:0 0 12px">Tu carta de hoy te espera</h1>
    <p style="font-size:15px;line-height:1.6;color:#756b5e;margin:0 0 24px">
      {saludo} Ábrela, vive tu pausa lejos del teléfono y escribe en tu diario lo que sentiste.
    </p>
    <a href="{url}"
       style="display:inline-block;background:#8fa58a;color:#fff8ea;text-decoration:none;border-radius:999px;padding:14px 30px;font-family:Inter,-apple-system,sans-serif;font-size:15px">
      Abrir mi carta
    </a>
    <p style="font-size:12px;color:#9a8f80;margin:26px 0 0">One quiet pause a day</p>
  </div>
  <p style="max-width:440px;margin:14px auto 0;font-size:11px;color:#9a8f80;text-align:center;font-family:Inter,-apple-system,sans-serif">
    Recibes este aviso porque lo activaste. Puedes apagarlo en tu Perfil.
  </p>
</div>"""
    return asunto, texto, html


def enviar_avisos(s: Session, ahora_utc: datetime | None = None) -> dict:
    """Un barrido. Devuelve conteos (para el log del Scheduler)."""
    ahora = ahora_utc or datetime.now(timezone.utc)
    usuarios = s.scalars(
        select(Usuario).where(
            Usuario.aviso_activo.is_(True),
            Usuario.terminos_aceptados_at.is_not(None),
        )
    ).all()

    enviados = 0
    saltados = 0
    for u in usuarios:
        try:
            tz = ZoneInfo(u.tz)
        except Exception:  # noqa: BLE001 — TZ corrupta no frena el barrido
            tz = _TZ_FALLBACK
        local = ahora.astimezone(tz)
        hoy_local = local.date()

        if u.ultimo_aviso_fecha == hoy_local:
            saltados += 1
            continue
        if local.hour * 60 + local.minute < _minutos(u.hora_aviso):
            saltados += 1
            continue
        if _pausa_guardada_hoy(s, u, tz, hoy_local):
            # Ya vivió su pausa: no hay nada que avisar. Se estampa igual para
            # no re-evaluar al usuario en cada tick del resto del día.
            u.ultimo_aviso_fecha = hoy_local
            saltados += 1
            continue

        asunto, texto, html = _contenido(u.apodo)
        if enviar_email(u.email, asunto, texto, html):
            u.ultimo_aviso_fecha = hoy_local
            enviados += 1
        else:
            saltados += 1

    s.commit()
    return {"candidatos": len(usuarios), "enviados": enviados, "saltados": saltados}

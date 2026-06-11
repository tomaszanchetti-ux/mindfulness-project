"""Aviso diario (WS20/WS21): "tu carta de hoy te espera", por PUSH WEB.

Cloud Scheduler golpea el endpoint interno cada 15 minutos; este barrido decide
a quién le toca. Regla por usuario (todo en SU hora local, zoneinfo):

  manda si  aviso_activo
        y   onboarding completo (términos aceptados)
        y   su hora local ya pasó la hora elegida (hora_aviso)
        y   hoy todavía no se le mandó (ultimo_aviso_fecha != fecha local)
        y   hoy todavía no guardó su pausa (si ya la vivió, no hay nada que avisar)
        y   tiene al menos un dispositivo suscripto (push: hay que instalar+aceptar)

Comparar ">= hora_aviso" (y no una ventana exacta de 15') hace el barrido
auto-reparable: si una corrida se pierde, la siguiente del día lo cubre. Sin
dispositivos suscriptos NO se estampa la fecha: si la persona activa las
notificaciones más tarde ese mismo día, el aviso del día le llega igual.
El push NO crea la entrega (canon WS15: la carta se revela al abrir la app).

Canal (decisión Tomás WS21): SOLO push. El email (services/email.py) queda
escrito pero dormido por si algún día vuelve como respaldo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Entrega, PushSuscripcion, Usuario
from .push import enviar_push

_TZ_FALLBACK = ZoneInfo("Europe/Madrid")

TITULO = "Tu carta de hoy te espera"
CUERPO = "Ábrela, vive tu pausa lejos del teléfono y escribe lo que sentiste."
URL = "/hoy"


def _minutos(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _pausa_guardada_hoy(s: Session, usuario: Usuario, tz: ZoneInfo, hoy_local) -> bool:
    entregas = s.scalars(
        select(Entrega).where(Entrega.usuario_id == usuario.id, Entrega.completada.is_(True))
    ).all()
    return any(e.fecha.astimezone(tz).date() == hoy_local for e in entregas)


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

        subs = s.scalars(
            select(PushSuscripcion).where(PushSuscripcion.usuario_id == u.id)
        ).all()
        ok = False
        for sub in subs:
            resultado = enviar_push(sub, TITULO, CUERPO, URL)
            if resultado == "ok":
                ok = True
            elif resultado == "gone":
                s.delete(sub)
        if ok:
            u.ultimo_aviso_fecha = hoy_local
            enviados += 1
        else:
            # Sin dispositivos (o todos fallaron): sin estampa → se reintenta
            # en el próximo tick; si se suscribe hoy más tarde, le llega hoy.
            saltados += 1

    s.commit()
    return {"candidatos": len(usuarios), "enviados": enviados, "saltados": saltados}

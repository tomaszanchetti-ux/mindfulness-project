"""Aislamiento de tests: limpia el Mundo 2 (datos de usuario) antes de la suite.

La DB local persiste entre corridas (volumen docker). Para que los tests sean
determinísticos, borramos los usuarios de prueba al arrancar — el borrado cascada
(FK ondelete=CASCADE) limpia categorías/entregas/fotos/compartidos. El contenido
global (Mundo 1) NO se toca.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import Usuario


@pytest.fixture(scope="session", autouse=True)
def _limpiar_mundo_2():
    with SessionLocal() as s:
        # WS24: los usuarios "demo|…" son los del navegador local (Q/A visual de
        # Tomás): no se tocan, para que una corrida de tests no le borre la sesión.
        s.execute(delete(Usuario).where(~Usuario.firebase_uid.like("demo|%")))
        s.commit()
    yield

# M2 — Entrega del Día

El motor que cada día elige **una** carta y te la entrega. El "mixer".

| Archivo | Qué es |
|---------|--------|
| [`Madre_del_Motor.md`](Madre_del_Motor.md) | La lógica completa, en cristiano. **Fuente de verdad.** |
| [`entrega.py`](entrega.py) | El script ejecutable. Hoy corre contra el seed de M0; al construir se enchufa a Postgres. |

**Probarlo:** `python3 entrega.py` (simula 21 días de un usuario en modo v1 y v2).

**En una línea:** dos capas — la **categoría** la elegís vos (filtro duro), la **acción**
la aprende la app de tus estrellas (preferencia blanda). No repite lo de la última
semana, la primera carta es random, y el azar siempre tiene la última palabra.

Se rige por el [`Documento Madre`](../00_Documento_Madre.md). Toma de
[M0](../M0_Motor_de_Contenido/) las cartas y de [M1](../M1_Onboarding_y_Perfil/) el
perfil; entrega a M3 (ritual) y M4 (Baúl).

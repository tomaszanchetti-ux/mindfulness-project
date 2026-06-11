# M2 — Entrega del Día

El motor que cada día elige **una** carta y te la entrega.

| Archivo | Qué es |
|---------|--------|
| [`Madre_del_Motor.md`](Madre_del_Motor.md) | La lógica completa, en cristiano. **Fuente de verdad de la lógica.** |

**La implementación** vive en [`apps/api/mindful_api/services/seleccion.py`](../apps/api/mindful_api/services/seleccion.py)
(tests: `apps/api/tests/test_seleccion.py`). *(El sandbox `entrega.py` de la v1 se
eliminó en WS18; está en el historial de git.)*

**En una línea:** la **rotación 6+1** recorre los 6 pilares cada semana (en orden
mezclado + día comodín); dentro del pilar del día entran tus **actividades de
desconexión** elegidas (la escritura pura siempre); no se repite **ni carta ni
concepto** en 7 días; tus ⭐ inclinan la balanza y el azar decide.

Se rige por el [`Documento Madre`](../00_Documento_Madre.md) y el
[`canon de cartas`](../M0_Motor_de_Contenido/canon_cartas.md). Toma de
[M0](../M0_Motor_de_Contenido/) las cartas y de [M1](../M1_Onboarding_y_Perfil/) el
perfil; entrega a M3 (ritual) y M4 (Baúl).

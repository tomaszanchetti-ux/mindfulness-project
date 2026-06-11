# Roadmap v2 · Premium — Dwellia

> Lista viva de funcionalidades v2 (acordada WS17 · 11/06/2026). La v1 free queda
> cerrada con: rotación 6+1 · concepto/dedup · validador de cartas · onboarding sin
> elección de pilares. Todo lo de abajo se encara **después**, como segunda ola.

## Principio rector

**"Sin feed ni likes" es promesa de marca y gobierna el premium.** Ninguna métrica
social pública: el reconocimiento es privado, un regalo que recibes, no un marcador
que persigues.

## Ola 1 — Mejoras de capacidad (rápidas, ya canonizadas en parte)

| Feature | Detalle | Estado canon |
|---|---|---|
| Reflexión larga | Subir el límite de 250 caracteres | nuevo |
| Hasta 3-5 fotos por pausa | Free quedó en 1 (WS16); premium vuelve a 3 (canon M3) o sube a 5 | parcial (back ya soporta 3) |
| Compartir el ejercicio completo | Modo `ejercicio` ya soportado en backend M5; free solo `carta_sola` | listo en back |
| Cambiar la carta del día (1 vez/día) | Te llega, no te va hoy → la cambias UNA vez; el motor sirve otra (respetando rotación+concepto) | nuevo (WS17) |
| Comodín aprendido | El día 7 deja de ser azar: pondera por las ⭐ del usuario (afinidad por pilar, espejo de la capa de actividades) | nuevo (WS17) |
| Fotos en el regalo (M5) | Compartir con fotos | canon WS16 |

## Ola 2 — Creación de cartas por usuarios (UGC curado)

La feature insignia del premium. El pipeline ya existe desde v1:

1. **El usuario crea** frase + prompt (+ pilar y actividad) en la app.
2. **Capa 1 determinística** (`scripts/validar_cartas.py`): feedback inmediato
   (estructura, diario, localismos, similitud con el mazo).
3. **Capa 2 LLM-judge** (mismo script, `--judge`): evalúa contra
   [`canon_cartas.md`](M0_Motor_de_Contenido/canon_cartas.md) → `aprueba /
   requiere_revision (con fix sugerido) / rechaza` + concepto sugerido + safety (S1-S3).
   El judge **sugiere cambios** para mantener la carta dentro del canon.
4. **Capa 3 humana:** Dwellia decide. El script recomienda, la marca cura.

Diseño acordado (WS17):
- Las cartas aprobadas entran a un pool aparte: **"Cartas de la comunidad"**,
  opt-in del receptor. El mazo core curado no se toca.
- **Apodo del autor discreto en el dorso** de la carta.
- **Impacto = mensaje interno privado** ("tu carta acompañó a N personas"),
  ocasional. Nunca contadores públicos ni rankings.
- El campo `concepto` mantiene la trazabilidad: el judge etiqueta cada carta nueva
  y el motor de distribución garantiza que la comunidad tampoco repita experiencia
  en la semana.
- Legal: términos de cesión de contenido + moderación (capa S del canon obligatoria).

## Ya en el canon para v2 (de sesiones previas)

- Email branded con dominio propio (aviso diario) · WS09/WS13.
- Aviso diario (worker + Scheduler + email) · pendiente de v1 también.
- OG dinámico por token compartido · WS09.
- Baúl: orden compuesto y edición de entradas · canon M4.
- Compresión de imágenes + limpieza de huérfanas · WS16.
- Atenuar un pilar (rotación quincenal de 1 pilar elegido) — válvula de
  escape descartada para v1, reconsiderar con feedback real · WS17.

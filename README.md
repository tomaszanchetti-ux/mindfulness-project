# Mindfulness App

Micro-rituales diarios de presencia, gratitud y conexión. El ritual vive **fuera
del teléfono**; el teléfono es guía + baúl.

> Repo: `git@github.com:tomaszanchetti-ux/mindfulness-project.git` ·
> Stack objetivo: Google Cloud + DB relacional + buen front (nivel Arc One).

---

## Índice

| | Qué es |
|---|--------|
| 📜 [`00_Documento_Madre.md`](00_Documento_Madre.md) | **Empezá por acá.** La idea, los principios rectores y los componentes de v2. |
| 🗂️ [`WS/`](WS/) | Bitácoras de trabajo — qué se hizo y qué sigue, sesión por sesión. |
| ⚙️ [`M0_Motor_de_Contenido/`](M0_Motor_de_Contenido/) | **Motor de contenido:** pilares, cartas, estética + la teoría ([`fundamentos_pilares.md`](M0_Motor_de_Contenido/fundamentos_pilares.md)) y el [`canon`](M0_Motor_de_Contenido/canon_cartas.md) (SoT del validador/judge). 🟡 refundado WS22 — triage del mazo pendiente. |
| 🚪 [`M1_Onboarding_y_Perfil/`](M1_Onboarding_y_Perfil/) | **Motor de onboarding y perfil:** login, storytelling (la pausa de dos tiempos + pilares en anillos), horario y aviso. ✅ lógica cerrada. |
| 🎴 [`M2_Entrega_del_Dia/`](M2_Entrega_del_Dia/) | **Motor de entrega del día:** rotación 6+1 de pilares sobre todo el pool del pilar (nada se elige — WS22); sin repetir carta ni concepto en la semana. ✅ lógica cerrada. |
| 🕯️ [`M3_Ritual/`](M3_Ritual/) | **Motor del ritual:** recibir/girar la carta, hacer la pausa afuera, cerrar con reflexión + 1 foto + estrellas. ✅ lógica cerrada v1. |
| 🧰 [`M4_Baul/`](M4_Baul/) | **Baúl de Crecimiento Personal:** historial ordenable (Reciente / Más valoradas), borrado para siempre con modal. ✅ lógica cerrada v1. |
| 🔗 [`M5_Compartir/`](M5_Compartir/) | **Compartir:** link público (carta sola / ejercicio completo), el receptor lo abre sin instalar. ✅ lógica cerrada v1. |

## Estado

- **v1 EN PRODUCCIÓN** → https://dwellia-app.web.app — funnel completo M1→M5
  (Firebase Hosting + Cloud Run + Cloud SQL · auth Firebase · push web diario ·
  TyC RGPD). Marca **Dwellia**. Bitácoras WS09–WS21. Stack:
  [`01_Stack_Arquitectura_Infraestructura.md`](01_Stack_Arquitectura_Infraestructura.md).
- **WS22 — Refundación conceptual de las cartas (canon nuevo):** la pausa de dos
  tiempos `acción inicial → calma → escribir` · pilar **Sentido** reemplaza a Calma
  (que asciende a vehículo del método) · ni pilares ni acciones se eligen ·
  "pasear". SoT: [`fundamentos_pilares.md`](M0_Motor_de_Contenido/fundamentos_pilares.md)
  + [`canon_cartas.md`](M0_Motor_de_Contenido/canon_cartas.md).
- **Pendiente (plan WS22):** paso 2 = triage del mazo (las 69 al canon nuevo) ·
  paso 3 = bajada a código (seeds, migración, motor — canon §Transición) ·
  paso 4 = UX (onboarding anillos, teoría in-app, re-layout carta).

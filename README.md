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
| ⚙️ [`M0_Motor_de_Contenido/`](M0_Motor_de_Contenido/) | **Motor de contenido:** categorías, cartas y estética. ✅ cerrado v1 (69 cartas). |
| 🚪 [`M1_Onboarding_y_Perfil/`](M1_Onboarding_y_Perfil/) | **Motor de onboarding y perfil:** login, configuración, explicación y compromiso. ✅ lógica cerrada v1. |
| 🎴 [`M2_Entrega_del_Dia/`](M2_Entrega_del_Dia/) | **Motor de entrega del día:** elige la carta de cada día y avisa. ✅ lógica cerrada v1 (+ script). |
| 🕯️ [`M3_Ritual/`](M3_Ritual/) | **Motor del ritual:** recibir/girar la carta, hacer el ejercicio afuera, cerrar con reflexión + fotos + estrellas. ✅ lógica cerrada v1. |
| 🧰 [`M4_Baul/`](M4_Baul/) | **Baúl de Crecimiento Personal:** historial ordenable (Reciente / Más valoradas), borrado para siempre con modal. ✅ lógica cerrada v1. |
| 🔗 [`M5_Compartir/`](M5_Compartir/) | **Compartir:** link público (carta sola / ejercicio completo), el receptor lo abre sin instalar. ✅ lógica cerrada v1. |

## Estado

- **N0 — Identidad y principios:** ✅
- **M0 — Motor de contenido:** ✅ cerrado v1 (69 cartas + seed + estética).
- **M1 — Onboarding y perfil:** ✅ lógica conceptual cerrada v1.
- **M2 — Entrega del día:** ✅ lógica cerrada v1 + script de referencia.
- **M3 — Ritual:** ✅ lógica conceptual cerrada v1.
- **M4 — Baúl:** ✅ lógica conceptual cerrada v1.
- **M5 — Compartir:** ✅ lógica conceptual cerrada v1.
- **Funnel de uso completo (M1→M5).**
- **N4 — Stack confirmado vs Arc One:** ✅ doc [`01_Stack_Arquitectura_Infraestructura.md`](01_Stack_Arquitectura_Infraestructura.md).
- **N4 — Backend M1→M5:** ✅ en [`apps/api/`](apps/api/) — funnel lógico completo, dos mundos, en Postgres (modo dev).
- **N4 — Front prototipo (web):** ✅ en [`apps/web/`](apps/web/) — Vite + React, 10 pantallas (funnel M1→M5), cableado al backend, mobile-first. Marca **Dwellia · "One quiet pause a day"**. (El front de producción será **Expo**.) Próximo: **Firebase + infra para desplegar**.

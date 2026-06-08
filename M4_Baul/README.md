# M4 — Baúl de Crecimiento Personal

El lugar para mirar atrás: todo lo que el usuario fue dejando — cada carta cerrada, con su
reflexión, sus fotos y sus estrellas.

| Archivo | Qué es |
|---------|--------|
| [`Madre_del_Motor.md`](Madre_del_Motor.md) | La lógica completa del Baúl, en cristiano. **Fuente de verdad.** |

**En una línea:** M4 **lee, ordena, muestra** (no captura — eso es M3). Dos modos de orden que
el usuario alterna: **Reciente** (default) y **Más valoradas**. Se puede **borrar** una entrada
**para siempre** (modal claro + botón rojo; limpia DB + fotos en Cloud Storage + link
compartido). Aislamiento por fila (`user_id` filtrado en el backend), **no** una base por usuario.

Se rige por el [`Documento Madre`](../00_Documento_Madre.md). Lee lo que escribe
[M3](../M3_Ritual/) (reflexión + fotos + ⭐), joinea la carta de [M0](../M0_Motor_de_Contenido/),
y ofrece el botón Compartir de [M5](../M5_Compartir/). Todavía es **lógica**, sin codear.

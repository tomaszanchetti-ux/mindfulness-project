# Lectura del Q/A visual de la WS24 (Tomás · 04/09/2026)

> Fuente: `Pivot/Q_A Visual WS24.pdf` (6 capturas, 4 pantallas). Esta lectura ordena
> cada comentario en tres grupos según lo que le pasa al plan: **retoque** (se hace
> sobre lo ya construido), **cambio de modelo** (invalida algo del Bloque A) y
> **nuevo** (reescribe los Bloques B y C). Las preguntas abiertas están al final.

## 1. Retoques directos (sobre lo construido en la WS24)

| # | Pantalla | Comentario | Qué se hace |
|---|---|---|---|
| R1 | Onboarding · círculos | Los 6 pilares simétricos "como un reloj": 12 amor propio · 2 gratitud · 4 vínculos · 6 sentido · 8 perspectiva · 10 resiliencia. Equidistantes aunque los tres anillos punteados sigan. | Hoy los ángulos ya coinciden con ese reloj, pero cada pilar está en un radio distinto (56/82/106) y por eso se ve desparejo. Se ponen los 6 nodos a un mismo radio, con el ángulo fijado por slug (no por orden alfabético), y los 3 anillos quedan de fondo. |
| R2 | Onboarding · cierre | Quitar "Sin feed ni likes. Solo una Pausa al día." | Se borra la línea. |
| R3 | Premium · porqué | Texto nuevo, más cercano: sin anuncios, sin uso económico de datos, comunidad que aprecia la Pausa diaria, la sostienen las personas que quieren más conexión consigo mismas. | Se reemplaza el bloque con el texto de Tomás, pulido. |
| R4 | Premium · lista | "Reflexiones más largas" → "Hasta 500 caracteres, para esos momentos donde sientes que quieres compartir más." · "Escribir cartas": Pausa con mayúscula, sin "pronto" · quitar "Recomendaciones en tu perfil" y convertir "Compartir el ejercicio completo" en **"Compartir más contenido"** = "Recomendaciones en tu perfil de libros, videos, podcasts que te hicieron bien, para aportar a la comunidad". Sin píldoras "pronto" en ninguna. | Lista final: Cambiar la carta · Reflexiones más largas · Tres fotos por Pausa · Compartir más contenido · Escribir cartas para la comunidad. |
| R5 | Premium · CTA | El botón dice **"Quiero ser parte"**. Sacar "Muy pronto podrás apoyar Dwellia desde aquí". | Un solo texto de botón. Sin Stripe configurado (solo local) el botón queda apagado sin nota. |
| R6 | Perfil | Muy ruidoso. Orden nuevo: **Apodo** grande + botón de edición elegante (abre apodo, nombre, apellido opcional; el email no se cambia; se aclara que te encuentran por email, apodo, nombre y apellido) → **Horario** con el toggle de notificaciones → **Instalar la app** si no está instalada → **Plan** (píldora "Gratis" + CTA "Quiero ser parte"; premium: píldora + "Quiero dejar la comunidad") → **El método Dwellia** → **T&C**. Fuera: zona horaria (queda autodetectada por dentro) y los pilares. | Se rehace `Profile.tsx` con ese orden. "Quiero dejar la comunidad" abre el portal de Stripe (donde se cancela). |
| R7 | Baúl · orden | Default fecha descendente · alternativa "Mejor valoradas" (desc., empatando por la más nueva). | Ya funciona así en la API; solo cambia el rótulo a "Mejor valoradas". |

## 2. Cambio de modelo: compartir es TODO o NADA (invalida parte del Bloque A)

Decisión de Tomás (PDF + mensaje del 04/09): **todos** los usuarios, free o premium,
comparten su ejercicio completo (carta + reflexión + foto) como una unidad. No existe
"solo la carta". Lo único que se elige es compartir o no compartir.

Consecuencias sobre lo construido:
- Desaparece la compuerta `compartir_ejercicio` (A1.1) y el selector de modo en
  `Share.tsx` (A2.2). El beneficio premium "compartir el ejercicio completo" se
  reemplaza por "Compartir más contenido" (= recomendaciones). `services/plan.py`
  deja de tener ese campo.
- Nace la **ficha** de cada Pausa: carta + reflexión + fotos, con **visibilidad**
  `privada` (default) o `compartida`. La ficha compartida es lo que ven los demás
  en tu perfil y lo que viaja por WhatsApp (el link público `/c/{token}` sigue,
  pero siempre muestra la ficha entera).
- Sin likes ni comentarios. La única acción sobre una ficha ajena es **reenviarla**
  a alguien de tu comunidad (dentro de la app) o por WhatsApp.
- Los filtros del Baúl pasan a ser: Con reflexión · Compartidas · Privadas.
- Cada ficha lleva una **píldora "Pausa"** en el verde Dwellia. Las fichas premium
  de tipo **"Recomendación"** (texto libre: libros, canales de YouTube, documentales,
  podcasts) conviven en el mismo Baúl con su píldora, un CTA "Agregar recomendación"
  y su wizard. Reemplazan a la tabla `recomendaciones` con allowlist de dominios del
  Bloque C.
- Regla que esto impone: el Baúl del usuario y su perfil visto por otros son **la
  misma vista** (menos las fichas privadas). Se diseña una sola vez.

## 3. Nuevo: Comunidad y Crear (reescriben los Bloques B y C)

**Barra inferior de 5:** Hoy · Baúl · Comunidad · Crear · Perfil.

- **Comunidad:** la lista de personas que tienes, buscador entre ellas y buscador
  de otros usuarios de Dwellia (por email registrado, apodo, nombre y apellido).
  Perfiles **privados por defecto**, ajustable desde Perfil. Un perfil privado se
  encuentra en la búsqueda, pero para ver sus fichas hay que mandar una **solicitud**
  y que la acepte (modelo Instagram). Un perfil público muestra sus fichas
  compartidas a cualquier usuario de Dwellia.
- **Crear:** escribir cartas para la comunidad (solo premium). Free que toca la
  pestaña → pop-up explicativo + CTA "Quiero ser parte". Tras enviar una carta se ve
  el **estado del proceso** como lista prolija con miniatura de la carta:
  1. "En proceso de evaluación" (gris) → 2. aviso + "En proceso de carga" (aprobada
  por Tomás) → 3. aviso + "Cargado a la comunidad" (ya en el mazo).
  Esto mapea al pipeline del roadmap (juez Sonnet 5 + aprobación de Tomás) y suma
  un paso explícito de "publicar" en admin para que el estado 2 exista.
- El "perfil público por handle sin login" (`/u/{handle}`) del Bloque C queda
  reemplazado por la comunidad dentro de la app: todo con login, salvo el link
  de WhatsApp de una ficha.

## 4. Preguntas abiertas para Tomás (cambian el diseño)

1. **Estrellas en la ficha:** ¿las ve la comunidad o quedan privadas? Propuesta:
   privadas (alimentan el motor; lo público es carta + reflexión + fotos).
2. **Compartir antes de guardar** (camino B de la WS14: enviar la carta del día
   antes de reflexionar). Con "todo o nada" la ficha estaría incompleta. Propuesta:
   se comparte solo una Pausa guardada; el botón de compartir del ritual se mueve
   al cierre.
3. **Perfil público:** ¿visible solo para usuarios logueados en Dwellia (propuesta)
   o también por link abierto en la web?
4. **Reenviar dentro de la app:** ¿qué recibe la otra persona? Propuesta mínima:
   una fila "X te compartió una Pausa" en su pestaña Comunidad, sin chat.
5. **Estado "En proceso de carga":** ¿lo dispara la aprobación de Tomás y el
   "Cargado" un segundo botón de publicar (propuesta), o basta con aprobar = cargado?

## 5. Orden propuesto (WS25 en adelante)

1. **A3 · retoques del Q/A visual** (grupo 1 + el cambio de compartir del grupo 2
   en su parte mínima: quitar modos, ficha entera, visibilidad por Pausa, filtros y
   píldora "Pausa" en el Baúl). Suite verde + `make demo-seed` con Pausas,
   reflexiones, fotos y fichas compartidas/privadas para el Q/A visual completo.
2. Reescritura de `ROADMAP_v2_PREMIUM.md`: Bloque B = Crear (con los 3 estados) ·
   Bloque C = Comunidad (fichas, perfiles, solicitudes, búsqueda, reenviar,
   recomendaciones como fichas) · TyC v3.
3. Q/A visual de Tomás sobre A3 → Stripe → deploy del Bloque A.
4. Bloque B, luego Bloque C, con el seed creciendo en cada bloque (cartas en cada
   estado, recomendaciones, solicitudes pendientes y aceptadas).

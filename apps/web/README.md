# apps/web — Prototipo del front (Vite + React)

Prototipo web para **ver y sentir la UX** del funnel completo (M1→M5), cableado a
la API real en modo `dev`. Implementa fielmente el
[`Sistema UX/UI`](../../../NewCo%20-%20Proyectos/Mindfulness%20App/) y reusa la
estética exacta de las cartas (`M0_Motor_de_Contenido/molde_carta.html`).

> **Nota de stack:** el front de **producción** será **React Native + Expo** (ver
> [`01_Stack_Arquitectura_Infraestructura.md`](../../01_Stack_Arquitectura_Infraestructura.md)).
> Este Vite es un prototipo de validación de UX, no el front final. El sistema de
> diseño (`theme.css`) y los contratos de API (`lib/api.ts`, `lib/types.ts`) se
> portan tal cual a Expo.

## Correr en local

Necesita la API y Postgres arriba (desde la raíz del repo):

```bash
make db-up && make api-migrate && make api-seed && make api-dev   # API en :8000
```

Luego, en `apps/web`:

```bash
npm install
npm run dev        # Vite en :8081 (proxy /api → :8000, sin CORS)
```

Abrí http://localhost:8081 — entra como el usuario `dev|user` (sin Firebase).

## Pantallas (las 10 de v1)

Login · Onboarding (4 pasos) · Hoy (carta del día, frente→dorso) · Reflexionar ·
Cierre del ritual · Baúl · Detalle de entrada · Compartir · Página pública del
regalo (`/c/:token`, sin login) · Perfil.

## Estructura

- `src/theme.css` — tokens del sistema de diseño (color §7, tipografía §8, layout §9).
- `src/app.css` — estilos de componentes y pantallas.
- `src/components/Card.tsx` — la carta frente/dorso (glifo tintado vía CSS mask).
- `src/lib/api.ts` + `types.ts` — cliente y contratos (espejo del backend).
- `src/screens/` — una pantalla por archivo.

## Gaps conocidos (a resolver cuando toque)

- **Foto en el ritual:** se ve preview local pero **no se persiste** — falta el
  endpoint de subida a Cloud Storage en la API (la tabla `fotos` ya existe).
- **Filtro "Enviadas" del Baúl:** omitido — la API no expone aún si una entrada
  tiene link activo.
- **Login:** passwordless simulado (modo dev). Con Expo será Google + magic-link
  de Firebase Auth (mismo contrato, sin password).

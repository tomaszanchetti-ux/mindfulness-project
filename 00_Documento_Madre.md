# Documento Madre — Mindfulness App

> **Documento rector. Se lee primero, siempre.** Corto a propósito: la idea, los
> principios y lo que vendrá después. Todo lo demás se rige por esto.

---

## 1. La idea

Una app de **micro-rituales diarios de presencia, gratitud y conexión humana**. El
usuario logra, al menos una vez por día, una actividad real de desconexión
**fuera del teléfono**. El teléfono es **guía** (le trae la consigna) y **baúl**
(guarda el rastro), nunca el destino.

La unidad de contenido es la **carta del día**: una **frase** breve que invita a
frenar + un **micro-prompt** que la vuelve acción concreta ("salí, mirá la luna,
guardá lo que viste"). Frase + micro-prompt, inseparables.

**Qué es / qué no es**

| Sí es | No es |
|-------|-------|
| Un ritual diario corto, fuera de la pantalla | Una red social / un feed infinito |
| Un espacio íntimo y privado | Una plataforma de likes y followers |
| Un gesto hacia personas concretas | Una app de productividad o fitness |

**Alcance v1:** ritual individual + compartir por link.
- **Entra:** onboarding-compromiso · carta del día · foto y reflexión opcionales · Baúl de Crecimiento Personal · compartir por link · perfil.
- **Queda para después:** círculos, IA generativa, dos rituales por día, packs.

**Stack:** Google Cloud + base de datos relacional + buen front, nivel Arc One
(NO Vercel/Supabase). Plataforma v1: Web / PWA. *Simple = la ingeniería, no el stack.*

---

## 2. Cómo funciona la app

El usuario hace el **onboarding una sola vez**. Después, **cada día a su hora**
recibe una **carta** (con un aviso opcional). La abre cerrada, la **gira**, lee la
frase y el micro-prompt, **hace el ejercicio afuera del teléfono** y, si quiere,
vuelve y sube una **foto + una reflexión ≤250**. Todo se guarda en el **Baúl**.
Puede compartir la carta por link si le nace. Y la app **se apaga**.

**Los tres loops**
1. **Diario:** aviso → carta del día → se ejecuta afuera → (opcional) foto + reflexión → al Baúl → la app se apaga.
2. **Gesto (secundario, latente):** compartir una carta por link con una nota; el receptor la abre sin instalar nada. Único canal de crecimiento, pero **no se empuja**.
3. **Baúl:** mirar atrás lo vivido. Es la retención.

**Los motores de la app** (cada uno puede volverse su propia carpeta, como M0)

| Motor | Qué hace | Estado |
|-------|----------|--------|
| **M0 · Contenido** | La materia prima: las 6 categorías y las cartas (frase + micro-prompt + dibujo). | 🔨 en construcción |
| **M1 · Onboarding y Perfil** | La entrada y las preferencias: elegir categorías (2-6), tono y horario; activar (o no) el aviso; aceptar el compromiso (diario a mano, lugar tranquilo, 10 min). Editable después. | por definir |
| **M2 · Entrega del día** | Elige la carta del día (azar ponderado por tus categorías y tono, sin repetir ~60 días, balanceando la modalidad) y avisa (push/email opcional). Vigencia 24h o hasta completarla. | por definir |
| **M3 · Ritual** | El momento: recibís la carta, la girás, hacés el ejercicio afuera y —opcional— subís foto + reflexión. | por definir |
| **M4 · Baúl de Crecimiento Personal** | El historial de todo lo vivido (carta + foto + reflexión), para mirar atrás. | por definir |
| **M5 · Compartir** | Link público con una nota personal. Secundario y latente: se ofrece, no se empuja. | por definir |

---

## 3. Principios rectores

**El Norte: _menos consumo, más presencia._**

### 🤝 Cómo trabajamos (nuestros)
1. **Simpleza** — claro, corto, sin jerga (Tomás no es técnico). Soluciones simples en la ingeniería, pero realizables y escalables. *Simple ≠ barato.*
2. **Eficacia** — decidir en pocas interacciones; y que todo funcione, escale (100.000 usuarios), sea seguro (datos de un usuario jamás se mezclan) y perfectamente usable.
3. **Integralidad con Claude** — usar todo el arsenal de Claude con lógica única (ej.: Claude Design para las cartas, con un prompt maestro consistente).

### 📿 Cómo se comporta la app
1. **El ritual vive fuera de la pantalla** — el teléfono manda a hacer algo afuera y guarda el rastro.
2. **Simpleza con apagado** — interacción mínima; la mejor sesión es la que termina y te devuelve a tu vida.
3. **Intimidad como producto** — 100% tuyo, privado por defecto; no estás obligado a cargar nada; compartir es decisión explícita.
4. **Invitar, nunca exigir** — sin push de nada salvo el aviso (opcional) de la carta del día. Sin rachas ni métricas de vanidad.

> **El gesto de compartir es secundario y latente:** se ofrece, nunca se empuja. No es lo que validamos.

---

## 4. Posibles componentes v2 (más adelante)

No entran en la v1; son la zanahoria del roadmap.

- **Círculos privados** — compartir recurrente con un grupo chico + reacciones emocionales (no likes).
- **IA creativa** — reescritura de tono, transformar la reflexión en tarjeta visual, resumen semanal, recomendaciones suaves.
- **Dos rituales por día** — mañana y noche, estilo diario guiado (palanca premium).
- **Cartas propias por el usuario** — armar cartas vía integración con Claude Design (API).
- **Carta sorpresa semanal** — una frase de motivación que llega de sorpresa (engagement suave, a evaluar).
- **Freemium completo** — más categorías, almacenamiento de fotos, personalización, packs temáticos.

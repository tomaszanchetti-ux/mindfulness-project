# Principios Rectores — App de Mindfulness

> Biblia conceptual del proyecto. Es la vara contra la que se mide toda decisión
> que tomemos de acá en adelante: producto, contenido, diseño, ingeniería y la
> forma en que trabajamos. Si algo contradice estos principios, no entra.

---

## El Norte

**Menos consumo, más presencia.**

El objetivo es que el usuario logre, **al menos una vez por día**, una actividad
real de desconexión, agradecimiento o mindfulness **fuera del teléfono**. El
teléfono es la **guía** (le trae la consigna) y el **baúl** (guarda el rastro),
nunca el destino.

---

## 🤝 Cómo trabajamos (nuestros)

### 1. Simpleza
Hablamos claro, corto, preciso y **sin jerga**. Tomás no es técnico: todo término
técnico se explica primero en cristiano. Las soluciones de desarrollo son
**simples en la ingeniería, pero realizables y escalables**.

> **Simple ≠ barato.** El stack es serio y de calidad (Google Cloud, base de datos
> relacional, buen front), al nivel de Arc One. Lo que se mantiene simple es la
> lógica de construcción, no las herramientas.

### 2. Eficacia
Mensajes concretos que nos dejen **decidir en pocas interacciones**. Y todo lo que
construimos tiene que:
- **funcionar** de verdad,
- **escalar** (objetivo: 100.000 usuarios),
- **ser seguro** — los datos de un usuario **jamás** se mezclan con los de otro,
- **ser perfectamente usable**.

### 3. Integralidad con Claude
Aprovechamos todo el arsenal de Claude con una **lógica única y consistente**.
Ejemplo canónico: **Claude Design** genera cada día una *carta* con estructura
fija (categoría + color + dibujo propio; se da vuelta y muestra frase + consigna).
Un **prompt maestro** garantiza que todas las cartas respeten el mismo sistema.

---

## 📿 Cómo se comporta la app

### 1. El ritual vive fuera de la pantalla
La consigna se ejecuta **afuera**: en tu diario, mirando la luna, saliendo a
caminar. La app no es el lugar donde pasa la cosa; es el lugar que **te manda a
hacerla** y **guarda el rastro**.

### 2. Simpleza con apagado
Interacción mínima: onboarding una vez → cada día llega la carta → la hacés
afuera → (opcional) subís foto + reflexión ≤250 caracteres → al baúl.
**La mejor sesión es la que termina y te devuelve a tu vida.**

### 3. Intimidad como producto
**100% tuyo.** Nadie ve lo que guardás. No estás obligado a cargar nada (podés
guardar solo la carta, sin foto ni reflexión). Lo que sale al mundo es **decisión
explícita** tuya. No es una red social.

### 4. Invitar, nunca exigir
**Sin push de nada**, salvo el aviso —opcional— de que llegó tu carta del día.
Sin rachas, sin métricas de vanidad, sin presión. El lenguaje ofrece una pausa,
nunca reclama una tarea.

---

## Nota estratégica: el gesto de compartir

Compartir una carta por link ("vi esto y pensé en vos") es una funcionalidad
**secundaria y latente**: se explica en el onboarding y se ofrece, pero **nunca se
empuja**. El foco de la v1 es el crecimiento personal del usuario en sus 10
minutos, no la viralidad. No es lo que validamos.

---

*Documento vivo. Cualquier cambio de rumbo se discute contra estos principios y se
registra acá.*

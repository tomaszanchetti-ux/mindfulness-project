# M1 — Motor de Onboarding y Perfil · Madre del Motor

> **La entrada a la app.** Define cómo la persona crea su cuenta, configura sus
> preferencias, entiende de qué se trata y queda lista para recibir su carta diaria.
> Toma de M0 las categorías; entrega a M2 (entrega) y M3 (ritual) un usuario
> configurado. Se rige por el [`Documento Madre`](../00_Documento_Madre.md).

---

## 1. Qué hace M1 (y qué no)

| Sí hace | No hace |
|---------|---------|
| Login sin contraseña (Google + magic link) | Manejar pagos / planes (eso es v2) |
| Configurar el perfil: nombre, apodo, categorías, horario, aviso | Elegir la carta del día (eso es M2) |
| Explicar la app y pedir el compromiso | El ritual en sí (girar/foto/reflexión real es M3) |
| Dejar el perfil **editable** después | Mezclar datos de un usuario con otro (aislamiento) |

**El norte de M1:** que en pocos toques la persona pase de "no tengo cuenta" a
"mañana a mi hora me llega mi primera carta", entendiendo qué es y qué no es la app.

---

## 2. El embudo (4 pasos)

```
1. Bienvenida + Login    →  Google  /  Magic link
2. Slideshow explicativo →  registro · acción diaria · baúl · compartir · compromiso · privacidad
3. Configurar la cuenta  →  nombre · apodo · categorías (2-6) · horario · aviso → check de términos al cerrar
4. Carta de prueba       →  tutorial guiado con pop-ups (girar · reflexión · foto · guardar)
                            └─ luego la carta REAL llega a su horario (la entrega M2)
```

Todo esto es la primera vez. El **slideshow va antes de configurar** a propósito: la
pantalla de compromiso ("elegí una hora con 10-15 min") enmarca el horario que elige
justo después. El slideshow se construye **al final del proyecto**, con ejemplos reales.
La carta de prueba (paso 4) es práctica, **no ensucia el Baúl**.

---

## 3. Login — passwordless prolijo

Dos vías, las dos **sin contraseña** y con el mail ya verificado (Firebase Auth):

- **Google** — un toque; trae su propio 2FA. Vuelve logueado.
- **Magic link** — escribe su mail → pantalla *"te mandamos un link a tu correo"* →
  toca el link → vuelve logueado. **El link es la verificación**, no hay paso extra.

**La regla de oro (aprendizaje del prode):** el mail tiene que **llegar siempre y
verse real**. Por eso el correo es **branded, desde dominio propio y por buen
proveedor de envío** (no el mail por defecto de Firebase, que es feo y cae en spam).
Eso es lo que hace que "se sienta seguro y real" — no un paso de seguridad extra.

> Sin verificación adicional tipo código: agregaría fricción y rompe *Simpleza con
> apagado*. Lo passwordless, bien hecho, ya es la seguridad.

---

## 4. Configurar la cuenta (el wizard, sólo la 1ª vez)

| Campo | Detalle |
|-------|---------|
| **Nombre y apellido** | Identificación básica. |
| **Apodo** | Cómo lo llama la app ("Hola, {apodo}"). |
| **Categorías** | Elige **2 a 6** de las 6 de M0, mostradas con sus dibujos. Mínimo 2 para que M2 tenga pool. |
| **Horario de la carta** | Hora local a la que quiere recibir la carta. *(Guarda también su zona horaria — M2 entrega en hora local.)* |
| **Aviso** | Un solo interruptor **sí/no**. Si **sí**: email siempre + push donde se pueda. Si **no**: la carta aparece en silencio al abrir la app. |

**Al cerrar la configuración, el check de términos/privacidad** — un paso final para
aceptar: explica que **no es red social**, que **el contenido es 100% suyo** y que
**compartir depende sólo de él**. Recién con esto aceptado se completa el perfil.

Es el handoff a M2: categorías + horario + aviso son justo lo que el mixer necesita.

---

## 5. Slideshow explicativo + compromiso + privacidad

Estilo carrusel de mercado, **muy simple**, una idea por pantalla. **Se desarrolla
al final**, con capturas reales:

1. **Registro / la carta** — cada día recibís una carta con una consigna.
2. **Acción diaria** — el ritual se hace **afuera del teléfono**. *(Línea suave al pie:
   "al final podés ponerle estrellas — es opcional y ayuda a que la app te conozca".)*
3. **Baúl** — todo lo que vivís queda guardado para mirar atrás.
4. **Compartir** — si te nace, podés compartir una carta por link. Opcional.
5. **Compromiso** — *elegí una hora en la que sepas que tenés **10-15 min** para vos*
   + *intentá tener un **diario a mano** para escribir*. (Refuerza el horario que ya eligió.)
6. **Privacidad (mención expresa)** — *no somos una red social · tu contenido es
   tuyo · compartir cartas o tareas depende 100% de vos*.

> La privacidad aparece **dos veces**: esta pantalla expresa al cierre del slideshow y
> el check de términos al **cerrar la configuración** (paso 3). Coherente con *intimidad
> como producto*.

---

## 6. La carta de prueba (tutorial guiado) → handoff a M2/M3

Al terminar la configuración mostramos **una carta real en modo práctica**, con pop-ups
que enseñan el ritual paso a paso:

1. **Girá la carta** → frase + micro-prompt.
2. **Escribí tu reflexión** (≤250).
3. **Subí una foto** (opcional).
4. **Ponele estrellas** (1-5, opcional) → con la frasecita *"ayuda a que la app te
   conozca"*. Lo **practica en vivo** acá; lo usa de verdad en cada ritual (M3) y lo
   aprovecha M2.
5. **Guardá.**

Es un **ensayo**: enseña la mecánica de **M3 (Ritual)** sin guardar nada en el Baúl.
La **primera carta real** llega después, **a su horario**, vía **M2 (Entrega)** — así
el Baúl arranca limpio con algo que sí vivió.

---

## 7. Notificaciones y "descargar como App" (arranque PWA)

Arrancamos como **PWA instalable** (Expo for Web, mismo código que el futuro nativo).
El aviso diario es el corazón, así que lo cubrimos en capas:

- **Email = aviso principal** — llega a cualquier teléfono (reusa la infra del magic link).
- **Push web = bonus** — Android/Chrome anda bien; **en iPhone sólo si instalan la app
  al inicio** (iOS 16.4+).
- Por eso el botón **"descargar como App"** y el aviso trabajan juntos: *"instalá la app
  en tu inicio para recibir el aviso en el celular"*. **Instalar = desbloquear el push.**
  En Android es un toque (prompt nativo); en iPhone, instrucción corta (*Compartir →
  Agregar a inicio*).

> **Pivot de secuencia (no de stack):** el canon es React Native + Expo. Sale **primero
> la web/PWA** y después el **nativo a las stores**, desde el **mismo proyecto Expo**.
> El stack N3 queda intacto.

---

## 8. Perfil editable (Ajustes)

Todo lo del paso 2 queda **editable** después en una pantalla de Ajustes: apodo,
categorías, horario, aviso. (Nombre/apellido también.)

- **Cambiar categorías** acá **cambia el pool de M2** en el acto (sacar una = sale del
  pool, el Baúl queda intacto; sumar una = entra ya).
- **Cambiar horario/aviso** redefine cuándo y cómo avisa M2.

---

## 9. Datos que escribe M1 (handoff al stack §5)

Tablas **privadas** (cada fila con `user_id`, jamás se cruzan entre usuarios):

```
usuarios
  user_id (= Firebase UID, PK)
  email · nombre · apellido · apodo
  horario_carta · zona_horaria
  aviso_on (bool)
  terminos_aceptados_en · terminos_version
  onboarding_completo (bool)
  creado_en

usuario_categorias        (2 a 6 filas por usuario)
  user_id · categoria_id   → FK a la tabla GLOBAL categorias (M0)
```

Las fotos del Baúl (M3/M4) van a Cloud Storage; M1 sólo crea al usuario.

---

## 10. Decisiones canónicas / pivots

- **Login passwordless** (Google + magic link), sin paso de verificación extra.
- **Email branded por dominio propio + buen proveedor** (aprendizaje del prode).
- **PWA primero, nativo después** desde el mismo Expo (pivot de secuencia, no de stack).
- **Aviso = un solo interruptor**; si está off, la carta aparece en silencio.
- **Carta de prueba** es tutorial, **no** guarda en el Baúl; la real respeta el horario.
- **Orden del embudo:** login → slideshow → configuración → demo (el slideshow precede a la config para que el compromiso enmarque el horario).
- **Privacidad en dos toques**: pantalla expresa de cierre del slideshow + check de términos al cerrar la configuración.
- **"Tono" se elimina del onboarding** — M0 canonizó español neutro único (ya no hay selector).

---

## 11. Diferido a v2

- Planes / pagos / freemium.
- Verificación de identidad más fuerte (si algún día hiciera falta).
- Más de un horario / dos rituales por día.
- Login con Apple (lo agrega Firebase fácil cuando salga el nativo a la App Store).

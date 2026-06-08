# M0 — Motor de Contenido · Plan de trabajo

El Módulo 0 es el **motor del producto**: las categorías y las cartas. Todo lo
demás se construye encima. Este README es la guía para retomar el trabajo.

> Referencias: `../00_Principios_Rectores.md` (biblia) ·
> `../00. Documento Madre v2 — App de Mindfulness (MVP).md` (SSOT documental).

---

## Modelo de contenido (lo ya decidido)

- **6 categorías:** Gratitud · Calma · Perspectiva · Resiliencia · Amor propio · Vínculos.
- **5 modalidades (acciones):** Escribir · Contemplar · Respirar · Caminar · Hacer.
- **Dos ejes (no un árbol):**
  - **Categoría** = el *qué* (tema). Lo elige el usuario en el onboarding: **de 2 a 6**.
  - **Modalidad** = el *cómo* (ejercicio). Es **propiedad de la carta**, el usuario NO la elige; la recibe.
- **23 moldes viables** (cruce categoría × modalidad, ver matriz abajo).
- **Profundidad:** arrancamos con **3 a 5 cartas por molde**, sin agotar la instancia. Calidad antes que volumen.
- **Anatomía de la carta:** `categoría + modalidad + frase + micro-prompt + tono + color + dibujo`.
  - **Frente:** nombre de categoría + color + dibujo de categoría.
  - **Dorso (se da vuelta):** frase + micro-prompt (+ tono).

## Principios del Motor (M0)

1. **Calidad sobre cantidad** — preferimos menos cartas, pero coherentes y que de verdad ayuden. El volumen nunca justifica una carta floja.
2. **Invitación, nunca obligación** — la actividad sugerida se mantiene pura (caminar es caminar, sin actividad supletoria que la diluya). La única opcionalidad: podés **guardar la carta sin hacer nada y sin tener que probar que la hiciste**.

## Matriz de afinidad (categoría × modalidad)

✅ fuerte · ○ posible · · evitar

| Categoría | Escribir | Contemplar | Respirar | Caminar | Hacer |
|-----------|:--:|:--:|:--:|:--:|:--:|
| Gratitud | ✅ | ✅ | · | ○ | ✅ |
| Calma | ○ | ✅ | ✅ | ✅ | · |
| Perspectiva | ✅ | ✅ | ○ | ○ | · |
| Resiliencia | ✅ | · | ○ | ✅ | ○ |
| Amor propio | ✅ | ○ | ○ | · | ✅ |
| Vínculos | ✅ | ○ | · | · | ✅ |

## Enfoque visual (decidido)

- **Claude Design** (Tomás, plan Max): genera los **bocetos** de cartas — colores + imágenes por categoría + imágenes por acción. **Uso puntual, NO dependencia en runtime.**
- **Script Python (mixer):** combina los bloques (color de categoría + imagen de categoría + imagen de acción + frase + micro-prompt) para componer las cartas.
- Todo **versionado en el repo**, formato consistente.

---

## Plan por pasos (general → particular)

| Paso | Qué | Intervención de Tomás | Se guarda en |
|------|-----|------------------------|--------------|
| **0** | Reglas del Motor ✅ | ratificadas | `00_Reglas_del_Motor.md` |
| **1** | Estética y anatomía de la carta | corre el *prompt maestro* en Claude Design, fija dirección | `00_Estetica_Carta.md` + `assets/` |
| **2** | Sistema de color (6) + imágenes de acción (5) | valida paleta e íconos | `assets/` (tokens + SVG/PNG) |
| **3** | Categoría por categoría (3-5 cartas/molde) | co-escribe y revisa carta por carta | `categorias/0X_Nombre.md` |
| **4** | Consolidación + mixer | revisa el seed | `seed/cartas_seed.csv` + script Python |

## Estructura de carpetas

```
M0_Motor_de_Contenido/
├── README.md               ← este archivo (el plan)
├── 00_Reglas_del_Motor.md  ← principios del Motor ✅
├── 00_Estetica_Carta.md    ← Paso 1 (pendiente)
├── categorias/             ← Paso 3 (un archivo por categoría)
├── assets/
│   ├── cartas/             ← imagen por categoría
│   └── acciones/           ← 5 imágenes de acción
└── seed/
    └── cartas_seed.csv     ← Paso 4 (generado por el mixer)
```

---

## Cómo retomamos (próximo paso concreto)

**Paso 1.** Claude entrega un **prompt maestro de la carta** para que Tomás lo
corra en Claude Design, itere los bocetos visualmente y fije la dirección
estética. Con esa base fijada, se baja al repo y se arranca el Paso 2 (color +
acciones) y el Paso 3 empezando por **Gratitud**.

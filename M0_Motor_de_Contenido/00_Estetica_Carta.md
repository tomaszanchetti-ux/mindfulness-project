# Estética de la Carta

Define **cómo se ve y se compone** la carta — la unidad visual del producto.
Es la referencia para el prompt maestro de Claude Design y para el front.

> Referencia de estilo: tarjeta japonesa minimalista — papel crema, mucho aire,
> tipografía fina, geometría sobria. (Ver `assets/bocetos/bocetos_v2.html`.)

---

## 1. Concepto

Una **carta de papel crema**, simple, íntima y elegante. Tiene **dos caras** y se
**gira con un tap**: recibís la carta cerrada (frente) y la girás para descubrir
la consigna del día (dorso). El giro es una pequeña ceremonia.

## 2. Anatomía

```
        FRENTE                          DORSO (al girar)
┌───────────────────┐          ┌───────────────────┐
│███ franja color ██│          │███ franja color ██│ ← misma franja, da la vuelta
│                   │          │                   │
│   g r a t i t u d │ ←cat.    │  "A veces lo que  │ ← FRASE (protagonista, aire)
│                   │          │   más sostiene…"  │
│        ☀          │ ←dibujo  │                   │
│      categoría    │          │        ◡          │ ← glifo de acción (acento chico)
│                   │          │                   │
│  c o n t e m p l a r │ ←acción │  Mirá a tu        │ ← micro-prompt
│                   │          │  alrededor y…     │
└───────────────────┘          └───────────────────┘
```

- **Frente:** franja de color (categoría) arriba · nombre de categoría (texto chico, espaciado) · dibujo de categoría (centro) · nombre de la acción (abajo).
- **Dorso:** misma franja · **frase** (protagonista, mucho aire) · glifo de acción (acento chico, no compite) · **micro-prompt** (abajo).
- **Simetría:** frente = el *qué* (tema) · dorso = el *cómo* (ejercicio).
- El **tono** es interno (curaduría/filtrado): **no se muestra** en la carta.
- Orientación **vertical**, esquinas redondeadas, textura de papel **muy sutil**.

## 3. Dos capas de estilo (regla clave)

| Capa | Estilo |
|------|--------|
| **Dibujo de categoría** | **Preciso**, formato **acuarela**, **todo en negro neutro**. El **color de la categoría pinta UN solo elemento/detalle**. Tonos claros y contenidos; mismo "valor" de color y misma textura de pincel en las 6. |
| **Glifo de acción** | **Minimalista**, geométrico, un solo color (se pinta del **color de la categoría**), chico. Pasa desapercibido: **no le roba protagonismo** a la frase ni al micro-prompt. |

El contraste es intencional: lo emotivo (categoría) con cuerpo; lo funcional (acción) como acento.

## 4. Vocabulario cerrado

### Categorías — dibujo negro + un acento de color
| Categoría | Motivo | Elemento con acento | Color del acento |
|-----------|--------|---------------------|------------------|
| **Gratitud** | amanecer | el **sol** | amarillo opaco |
| **Calma** | luna sobre el agua | el **reflejo** de la luna (en negativo, agua sombreada) | blanco |
| **Perspectiva** | montañas a lo lejos (paisaje amplio) | una **montaña** | marrón |
| **Resiliencia** | una planta entre piedras | la **planta** | verde |
| **Amor propio** | una flor abriéndose | el **centro / detalle** de la flor | rosa |
| **Vínculos** | dos pájaros | el **ala de uno** de los pájaros | rojo |

### Acciones — glifo geométrico minimalista
| Acción | Glifo |
|--------|-------|
| **Escribir** | una pluma simple |
| **Contemplar** | un ojo estilizado |
| **Respirar** | círculos concéntricos |
| **Caminar** | pasos (chevrons) |
| **Hacer** | un destello |

## 5. Paleta (provisoria — se afina en Paso 2)

| Rol | Color | Hex provisorio |
|-----|-------|----------------|
| Papel | crema cálido | `#EFE6D3` |
| Tinta | negro neutro | `#2b2925` |
| Gratitud | amarillo opaco | `#E0A92E` |
| Calma | blanco | `#FFFFFF` |
| Perspectiva | marrón | `#8A5A3B` |
| Resiliencia | verde | `#5E8C4E` |
| Amor propio | rosa | `#D98AA6` |
| Vínculos | rojo | `#C8453E` |

La **franja superior** de la carta usa el color de la categoría. El **glifo de
acción** también se pinta de ese color.

## 6. Tipografía (a confirmar familia)

- **Frase (dorso):** serif elegante, es la protagonista, con aire.
- **Nombres y labels (categoría, acción):** sans fina con **tracking amplio**, en minúscula, estilo `g r a t i t u d`.
- **Micro-prompt:** sans legible, tamaño menor, tono tranquilo.

## 7. Formato de salida (qué entrega Claude Design)

- **11 assets en SVG:** 6 `cat_*.svg` + 5 `act_*.svg`.
- **Fondo transparente, sin texto, sin chrome de carta** (sólo el dibujo).
- **viewBox consistente**, centrado (categorías `0 0 120 120` · acciones `0 0 90 90`).
- **Acento recoloreable:** dibujo en negro (`#2b2925` / `currentColor`); elemento con acento en grupo identificable (`<g class="accent">` o `var(--accent)`).
- **PNG transparente de alta resolución** sólo si la acuarela precisa no se logra en vector.
- La **carta** (layout, giro, tipografía) se toma como **referencia HTML/CSS** y se reimplementa en el front real.

---

*Próximo: con esta estética, se escribe el prompt maestro para Claude Design y se
prueba el primer asset (Gratitud) antes de producir el resto.*

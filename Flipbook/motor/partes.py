"""Las piezas ilustradas del flipbook (capa de detalle · D1.1 · WS32).

Cada personaje es una marioneta de PIEZAS: una cabeza por cara y un cuerpo por pose. Las
piezas se dibujan UNA vez acá como SVG (línea clara, relleno plano, línea tierra) y se
renderizan a PNG con fondo transparente en `Flipbook/personajes/partes/<personaje>/`.
El motor (render.py) después las compone en cada hoja con temblor y registro imperfecto,
así que es el mismo Pipo en las 60 hojas.

Uso:
    python3 Flipbook/motor/partes.py            # regenera todas las piezas + partes.json
    python3 Flipbook/motor/partes.py pipo       # solo un personaje

Cada pieza declara sus ANCLAS (en coordenadas del lienzo de 400 × 400):
  - cabeza: "cuello" = el punto que se apoya sobre el cuerpo.
  - cuerpo: "cabeza" = dónde va el cuello de la cabeza, con su escala y rotación sugeridas.
"""
import json, os, subprocess, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # Flipbook/
DESTINO = os.path.join(RAIZ, "personajes", "partes")
LIENZO = 400            # unidades del dibujo
ESCALA_PNG = 2          # el PNG sale a 800 px; el motor lo achica (línea más fina y limpia)

# Paleta (REGLAS §1): papel crema, línea tierra, secundaria taupe, un solo acento salvia.
UMBER = "#2f2923"; TAUPE = "#756b5e"; DUST = "#9a8f80"; IVORY = "#fff8ea"
FAWN = "#eadfc7"; FAWN_SOMBRA = "#dccfb3"; NOSE = "#463f38"; TONGUE = "#a8947c"
SAGE = "#8fa58a"; SAGE_DEEP = "#6f8a69"; SAND = "#d6c7ad"; PIEL = "#f1e6d3"
REMERA = "#e6dccb"; PANTALON = "#8b8073"

W_MAIN = 9      # grosor de la línea principal en unidades de lienzo
W_SEC = 5

def path(d, fill="none", stroke=UMBER, w=W_MAIN, extra=""):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'

def circ(cx, cy, r, fill, stroke="none", w=0):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>'

def ell(cx, cy, rx, ry, fill, stroke="none", w=0, rot=0):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" transform="rotate({rot} {cx} {cy})"/>'

def grupo(contenido, transform=""):
    return f'<g transform="{transform}">{"".join(contenido)}</g>'

def svg(contenido, w=LIENZO, h=LIENZO):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            + "".join(contenido) + "</svg>")

# =====================================================================================
# PIPO · la cabeza (a cámara) y sus 6 caras
# =====================================================================================
# Centro del cráneo (200, 205). Ojos en (140, 200) y (260, 200). Máscara del hocico abajo.

def pipo_ojo(cx, cy, r, mirada=(0, 0), parpado=0.0, parpado_abajo=0.0, brillo=1.0, lagrima=False):
    """Ojo enorme y redondo. mirada = desplazamiento de la pupila (-1..1). parpado = cuánto
    tapa el párpado de arriba (0 abierto · 0.5 medio cerrado). brillo = tamaño del reflejo."""
    px, py = cx + mirada[0] * r * 0.32, cy + mirada[1] * r * 0.32
    out = [f'<clipPath id="ojo{cx}{cy}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>',
           circ(cx, cy, r, IVORY),
           f'<g clip-path="url(#ojo{cx}{cy})">',
           circ(px, py, r * 0.74, UMBER),
           circ(px - r * 0.26, py - r * 0.28, r * 0.26 * brillo, IVORY),
           circ(px + r * 0.2, py + r * 0.24, r * 0.1 * brillo, IVORY)]
    if parpado > 0:       # párpado de arriba: un rectángulo del color del pelaje con borde
        top = cy - r + parpado * 2 * r
        out.append(f'<rect x="{cx - r - 4}" y="{cy - r - 6}" width="{2 * r + 8}" height="{top - (cy - r - 6)}" fill="{FAWN}"/>')
        out.append(path(f"M {cx - r - 2} {top} L {cx + r + 2} {top}", w=W_SEC + 1))
    if parpado_abajo > 0:  # párpado de abajo (sonrisa que aprieta el ojo)
        bot = cy + r - parpado_abajo * 2 * r
        out.append(f'<rect x="{cx - r - 4}" y="{bot}" width="{2 * r + 8}" height="{r}" fill="{FAWN}"/>')
        out.append(path(f"M {cx - r - 2} {bot} L {cx + r + 2} {bot}", w=W_SEC + 1))
    out.append("</g>")
    out.append(circ(cx, cy, r, "none", UMBER, W_MAIN - 2))
    if lagrima:
        tx, ty = cx + r * 0.62, cy + r * 0.78
        out.append(path(f"M {tx} {ty} C {tx - 12} {ty + 22}, {tx - 6} {ty + 40}, {tx + 6} {ty + 40} C {tx + 18} {ty + 40}, {tx + 22} {ty + 22}, {tx} {ty} Z",
                        fill=IVORY, w=W_SEC))
    return "".join(out)

def pipo_oreja(lado, caida=0.0, atras=0.0):
    """Oreja negra plegada (botón), pegada al cráneo. lado = -1 izquierda · 1 derecha.
    caida 0..1 = la punta cuelga más; atras 0..1 = la oreja se aplasta hacia atrás (sospecha)."""
    s = lado
    ax, ay = 200 + s * 108, 110                  # inserción en la esquina alta del cráneo
    ang = s * (-26 + 14 * caida - 30 * atras)
    d = (f"M {ax} {ay} C {ax + s * 36} {ay + 4}, {ax + s * 58} {ay + 44}, {ax + s * 46} {ay + 94} "
         f"C {ax + s * 40} {ay + 118}, {ax + s * 8} {ay + 116}, {ax - s * 4} {ay + 86} "
         f"C {ax - s * 10} {ay + 56}, {ax - s * 8} {ay + 24}, {ax} {ay} Z")
    pliegue = f"M {ax + s * 8} {ay + 14} C {ax + s * 30} {ay + 30}, {ax + s * 40} {ay + 54}, {ax + s * 36} {ay + 84}"
    return grupo([path(d, fill=UMBER, w=W_SEC), path(pliegue, stroke=DUST, w=3)], f"rotate({ang} {ax} {ay})")

def pipo_ceja(cx, y, ang, largo=52, w=W_MAIN - 1):
    """Ceja gruesa (la arruga del pug convertida en ceja de historieta). ang > 0 = el extremo de
    adentro (hacia la nariz) BAJA (enojo); ang < 0 = sube (pena / sorpresa). cx = centro del ojo."""
    import math
    hacia_nariz = 1 if cx < 200 else -1
    dy = math.sin(math.radians(ang)) * largo / 2
    dx = math.cos(math.radians(ang)) * largo / 2
    ix, iy = cx + hacia_nariz * dx, y + dy        # extremo interno
    ox, oy = cx - hacia_nariz * dx, y - dy        # extremo externo
    return path(f"M {ox:.1f} {oy:.1f} Q {(ox + ix) / 2:.1f} {(oy + iy) / 2 - 8:.1f} {ix:.1f} {iy:.1f}", w=w)

def pipo_cabeza(cara):
    """Devuelve el SVG de la cabeza de Pipo con una de las 6 caras (dict de parámetros).
    v3 (WS32, pedido de Tomás): más caricatura y más amigable: ojos enormes, cejas gruesas que
    llevan la expresión, boca grande y clara sobre la máscara, sin arrugas de viejo."""
    c = dict(mirada=(0, 0), parpado=(0, 0), parpado_abajo=(0, 0), ojos=(50, 50), brillo=1.0,
             lagrima=False, cejas=(0, 0), cejas_y=(146, 146), boca="sonrisa", lengua=False, dientes=False,
             orejas=(0.0, 0.0), atras=0.0, tilt=0, frente=0, guino=None, estrellas=False)
    c.update(cara)
    partes = []
    # cráneo: ancho arriba, cachetes redondos abajo (forma de corazón blando)
    craneo = ("M 48 208 C 48 116, 118 78, 200 78 C 282 78, 352 116, 352 208 "
              "C 352 266, 336 314, 296 340 C 266 360, 234 366, 200 366 "
              "C 166 366, 134 360, 104 340 C 64 314, 48 266, 48 208 Z")
    partes.append(path(craneo, fill=FAWN))
    partes.append(pipo_oreja(-1, c["orejas"][0], c["atras"]))
    partes.append(pipo_oreja(1, c["orejas"][1], c["atras"]))
    # rubor en los cachetes (en tono, sin color nuevo)
    partes.append(ell(96, 280, 26, 16, FAWN_SOMBRA))
    partes.append(ell(304, 280, 26, 16, FAWN_SOMBRA))
    # mechón de pelo arriba de la cabeza (el detalle achuchable)
    partes.append(path("M 186 82 C 190 64, 204 56, 214 62 C 208 66, 204 74, 206 82", fill=FAWN, w=W_SEC))
    partes.append(path("M 214 62 C 224 52, 238 58, 236 70", w=W_SEC))
    # máscara negra del hocico: más chica que en la v2, deja aire para la sonrisa
    mascara = ("M 200 184 C 178 194, 132 220, 126 266 C 122 314, 156 344, 200 344 "
               "C 244 344, 278 314, 274 266 C 268 220, 222 194, 200 184 Z")
    partes.append(path(mascara, fill=UMBER, w=W_SEC))
    # pliegue de la frente (solo si la cara lo pide: 1 = una línea, 2 = dos)
    if c["frente"] >= 1:
        partes.append(path("M 160 118 C 178 108, 222 108, 240 118", stroke=TAUPE, w=W_SEC))
    if c["frente"] >= 2:
        partes.append(path("M 172 102 C 186 94, 214 94, 228 102", stroke=TAUPE, w=W_SEC))
    # ojos (o guiño)
    for k, cx in enumerate((138, 262)):
        if c["guino"] == k:
            partes.append(path(f"M {cx - 30} 206 C {cx - 14} 190, {cx + 14} 190, {cx + 30} 206", w=W_MAIN))
            continue
        partes.append(pipo_ojo(cx, 206, c["ojos"][k], c["mirada"], c["parpado"][k], c["parpado_abajo"][k], c["brillo"],
                               lagrima=(c["lagrima"] and k == 1)))
        if c["estrellas"]:
            partes.append(path(f"M {cx - 8} 194 l 4 8 l 8 2 l -6 6 l 1 8 l -7 -4 l -7 4 l 1 -8 l -6 -6 l 8 -2 Z", fill=IVORY, stroke="none", w=0))
    # cejas
    partes.append(pipo_ceja(138, c["cejas_y"][0], c["cejas"][0]))
    partes.append(pipo_ceja(262, c["cejas_y"][1], c["cejas"][1]))
    # nariz grande y redonda
    partes.append(path("M 172 250 C 172 232, 228 232, 228 250 C 228 270, 210 282, 200 282 C 190 282, 172 270, 172 250 Z", fill=NOSE, stroke="none", w=0))
    partes.append(path("M 186 254 C 182 258, 184 264, 190 262", stroke=DUST, w=3))
    partes.append(path("M 214 254 C 218 258, 216 264, 210 262", stroke=DUST, w=3))
    partes.append(path("M 200 282 L 200 296", stroke=SAND, w=4))
    # boca, grande y clara sobre la máscara
    B = c["boca"]
    if B == "sonrisa":            # sonrisa amplia
        partes.append(path("M 150 296 C 166 332, 234 332, 250 296", stroke=IVORY, w=6))
    elif B == "sonrisa_abierta":  # boca abierta de alegría
        partes.append(path("M 150 294 C 160 344, 240 344, 250 294 Z", fill=NOSE, stroke=IVORY, w=5))
        partes.append(path("M 156 296 L 244 296", stroke=IVORY, w=8))
    elif B == "torcida":          # sonrisa de costado, engreída
        partes.append(path("M 152 306 C 176 300, 212 322, 254 288", stroke=IVORY, w=6))
    elif B == "ondulada":         # boca de "no sé": una onda
        partes.append(path("M 156 306 C 170 292, 186 320, 200 306 C 214 292, 230 320, 244 306", stroke=IVORY, w=6))
    elif B == "caida":            # bajón
        partes.append(path("M 156 318 C 172 296, 228 296, 244 318", stroke=IVORY, w=6))
    elif B == "apretada":         # boca apretada, chiquita
        partes.append(path("M 180 308 C 190 302, 210 302, 220 308", stroke=IVORY, w=6))
    elif B == "o":                # boquita de sorpresa
        partes.append(path("M 186 300 C 186 288, 214 288, 214 300 C 214 314, 186 314, 186 300 Z", fill=NOSE, stroke=IVORY, w=5))
    if c["lengua"]:
        partes.append(path("M 204 308 C 196 340, 216 380, 250 372 C 276 366, 270 330, 254 304 Z", fill=TONGUE, stroke=UMBER, w=W_SEC))
        partes.append(path("M 232 318 C 234 338, 238 354, 246 366", stroke=UMBER, w=3))
    if c["dientes"]:              # los dientes de abajo asomando (foto Enojado), grandes
        for x in (168, 188, 208, 228):
            partes.append(f'<rect x="{x}" y="{298}" width="16" height="16" rx="4" fill="{IVORY}" stroke="{UMBER}" stroke-width="3"/>')
    partes.append(path(craneo, fill="none"))
    contenido = grupo(partes, f"rotate({c['tilt']} 200 230)")
    return svg([contenido]), {"cuello": [200, 350], "tilt": c["tilt"]}

CARAS_PIPO = {
    # 1. fastidio ("ay no"): cejas en V bien marcadas, ojos a medio cerrar, dientes de abajo, orejas caídas
    "fastidio": dict(cejas=(28, 28), cejas_y=(160, 160), parpado=(0.34, 0.34), boca="caida", dientes=True,
                     orejas=(0.6, 0.6), brillo=0.8, mirada=(0.0, 0.05)),
    # 2. resignación ("otra vez"): cabeza ladeada, ojos al cielo, cejas de pena, boca ondulada, orejas caídas
    "resignacion": dict(cejas=(-24, -24), cejas_y=(142, 142), frente=0, mirada=(0.1, -0.9), boca="ondulada",
                        tilt=-14, orejas=(0.8, 0.5), ojos=(50, 50)),
    # 3. sospecha (side-eye): un ojo entrecerrado y el otro enorme, pupilas de reojo, orejas atrás, boca apretada
    "sospecha": dict(cejas=(30, -18), cejas_y=(164, 138), parpado=(0.5, 0.0), ojos=(46, 54), mirada=(-1.0, 0.1),
                     boca="apretada", atras=0.5, brillo=1.1),
    # 4. ¿en serio?: cabeza muy ladeada, cejas asimétricas, una oreja parada, boquita de "o"
    "en_serio": dict(cejas=(-16, 10), cejas_y=(138, 152), tilt=28, orejas=(0.0, 1.0), boca="o", mirada=(0.15, 0.1), ojos=(52, 48)),
    # 5. alegría sarcástica ("te lo dije"): guiño, sonrisa engreída de costado, lengua afuera, ladeada
    "alegria_sarcastica": dict(cejas=(-8, 18), cejas_y=(142, 150), tilt=-16, guino=1, ojos=(52, 52), parpado_abajo=(0.2, 0.0),
                               boca="torcida", lengua=True, mirada=(0.35, -0.15), orejas=(0.1, 0.5)),
    # 6. orgullo (la Alegría de Tomás, WS34): ojos enormes con estrellas, SIN lágrima, boca abierta de alegría, orejas relajadas
    "orgullo": dict(cejas=(-12, -12), cejas_y=(136, 136), ojos=(54, 54), brillo=1.5, estrellas=True, lagrima=False,
                    boca="sonrisa_abierta", mirada=(0.0, -0.15), orejas=(0.4, 0.4)),
}

# =====================================================================================
# PIPO · los cuerpos (sin cabeza; declaran dónde va la cabeza)
# =====================================================================================

def pipo_collar(cx, cy, rx, ry=14):
    return path(f"M {cx - rx} {cy} C {cx - rx * 0.6} {cy + ry * 1.6}, {cx + rx * 0.6} {cy + ry * 1.6}, {cx + rx} {cy}",
                stroke=SAGE, w=W_MAIN + 4)

def pipo_pata_frente(x, y, largo=70, sep=0):
    """Pata delantera vista de frente: columna recta con la almohadilla."""
    return "".join([
        path(f"M {x - 16} {y} C {x - 18} {y + largo * 0.5}, {x - 18} {y + largo * 0.8}, {x - 20 - sep} {y + largo} "
             f"C {x - 20 - sep} {y + largo + 14}, {x + 20 + sep} {y + largo + 14}, {x + 20 + sep} {y + largo} "
             f"C {x + 18} {y + largo * 0.8}, {x + 18} {y + largo * 0.5}, {x + 16} {y} Z", fill=FAWN),
        path(f"M {x - 10} {y + largo + 6} L {x - 10} {y + largo + 12}", stroke=UMBER, w=3),
        path(f"M {x + 10} {y + largo + 6} L {x + 10} {y + largo + 12}", stroke=UMBER, w=3),
    ])

def pipo_cola(x, y, s=1.0, rot=0):
    """Cola enrulada: una espiral apretada sobre la grupa."""
    d = (f"M {x} {y} C {x - 6 * s} {y - 30 * s}, {x + 10 * s} {y - 66 * s}, {x + 40 * s} {y - 60 * s} "
         f"C {x + 70 * s} {y - 54 * s}, {x + 66 * s} {y - 12 * s}, {x + 38 * s} {y - 10 * s} "
         f"C {x + 18 * s} {y - 10 * s}, {x + 14 * s} {y - 36 * s}, {x + 34 * s} {y - 38 * s}")
    return grupo([path(d, w=W_MAIN)], f"rotate({rot} {x} {y})")

def pipo_cuerpo_sentado():
    """Sentado a cámara: pera ancha, dos patas delanteras rectas, patas traseras asomando."""
    p = []
    p.append(pipo_cola(272, 250, s=0.9, rot=10))
    # patas traseras (asoman a los lados, como en la foto)
    for s in (-1, 1):
        cx = 200 + s * 92
        p.append(path(f"M {cx - 26} 312 C {cx - 34} 330, {cx - 30} 352, {cx - 8} 354 C {cx + 14} 356, {cx + 30} 344, {cx + 24} 322 Z", fill=FAWN))
        p.append(path(f"M {cx - 14} 352 L {cx - 14} 358 M {cx} 354 L {cx} 360", stroke=UMBER, w=3))
    # torso pera
    p.append(path("M 200 130 C 258 130, 300 190, 300 262 C 300 322, 262 352, 200 352 "
                  "C 138 352, 100 322, 100 262 C 100 190, 142 130, 200 130 Z", fill=FAWN))
    # pecho claro
    p.append(path("M 200 166 C 232 166, 250 210, 246 262 C 242 300, 224 318, 200 318 "
                  "C 176 318, 158 300, 154 262 C 150 210, 168 166, 200 166 Z", fill=IVORY, stroke="none", w=0))
    # patas delanteras
    p.append(pipo_pata_frente(158, 270, largo=72))
    p.append(pipo_pata_frente(242, 270, largo=72))
    # collar (la cabeza se apoya justo arriba)
    p.append(pipo_collar(200, 150, 52))
    return svg(p), {"cabeza": [200, 150], "escala": 1.0, "rot": 0, "z_cabeza": "delante"}

def pipo_cuerpo_camina(fase=0):
    """Camina de perfil hacia la derecha; la cabeza (a cámara) va adelante y arriba."""
    import math
    sw = math.sin(fase * 2 * math.pi)
    p = []
    p.append(pipo_cola(98, 226, s=1.0, rot=-10))
    # patas traseras y delanteras (dos planos)
    def pata(x, y, dx, atras=False):
        col = FAWN_SOMBRA if atras else FAWN
        return path(f"M {x - 14} {y} C {x - 16} {y + 40}, {x - 14 + dx} {y + 70}, {x - 16 + dx} {y + 92} "
                    f"C {x - 18 + dx} {y + 106}, {x + 20 + dx} {y + 106}, {x + 18 + dx} {y + 92} "
                    f"C {x + 16 + dx} {y + 70}, {x + 14} {y + 40}, {x + 14} {y} Z", fill=col)
    p.append(pata(146, 246, 26 * sw, atras=True))
    p.append(pata(236, 246, -26 * sw, atras=True))
    # cuerpo (barril)
    p.append(path("M 118 236 C 110 190, 140 152, 200 150 C 262 148, 300 176, 302 226 "
                  "C 304 276, 264 300, 200 302 C 140 304, 124 280, 118 236 Z", fill=FAWN))
    p.append(path("M 256 292 C 284 284, 302 262, 300 232 C 296 214, 276 212, 268 236 C 262 258, 258 276, 256 292 Z", fill=IVORY, stroke="none", w=0))
    p.append(pata(138, 250, -26 * sw))
    p.append(pata(248, 250, 26 * sw))
    p.append(pipo_collar(258, 178, 36, ry=10))
    return svg(p), {"cabeza": [268, 176], "escala": 0.88, "rot": 8, "z_cabeza": "delante"}

def pipo_cuerpo_panza_arriba():
    """Panza arriba, entregado: patas dobladas al aire, la cabeza cae hacia la cámara."""
    p = []
    p.append(pipo_cola(120, 214, s=0.9, rot=140))
    # cuerpo acostado (a lo ancho), panza clara
    p.append(path("M 110 214 C 96 178, 132 146, 200 146 C 268 146, 306 178, 296 220 "
                  "C 290 258, 250 282, 196 284 C 136 286, 116 254, 110 214 Z", fill=FAWN))
    p.append(path("M 148 216 C 148 184, 178 166, 210 168 C 246 170, 268 196, 262 226 "
                  "C 256 254, 226 266, 196 264 C 164 262, 150 244, 148 216 Z", fill=IVORY, stroke="none", w=0))
    # patas dobladas al aire (cuatro patitas cortas)
    def patita(x, y, ang):
        d = (f"M {x} {y} C {x - 6} {y - 26}, {x + 4} {y - 52}, {x + 16} {y - 58} "
             f"C {x + 30} {y - 64}, {x + 38} {y - 46}, {x + 30} {y - 38} C {x + 22} {y - 30}, {x + 18} {y - 10}, {x + 22} {y + 2} Z")
        return grupo([path(d, fill=FAWN), path(f"M {x + 20} {y - 50} L {x + 26} {y - 46} M {x + 27} {y - 56} L {x + 32} {y - 50}", w=3)],
                     f"rotate({ang} {x} {y})")
    p.append(patita(160, 166, -20))
    p.append(patita(236, 160, 15))
    p.append(patita(140, 262, -100))
    p.append(patita(258, 258, 100))
    p.append(pipo_collar(300, 214, 8, ry=26))
    return svg(p), {"cabeza": [262, 218], "escala": 0.86, "rot": 118, "z_cabeza": "delante"}

def pipo_cuerpo_plantado():
    """Plantado con la correa tensa: patas rígidas hacia adelante, cuerpo echado atrás."""
    p = []
    p.append(pipo_cola(96, 214, s=1.0, rot=-30))
    def pata(x, y, dx, atras=False):
        col = FAWN_SOMBRA if atras else FAWN
        return path(f"M {x - 14} {y} C {x - 20} {y + 36}, {x - 14 + dx} {y + 60}, {x - 22 + dx} {y + 92} "
                    f"C {x - 26 + dx} {y + 106}, {x + 16 + dx} {y + 106}, {x + 14 + dx} {y + 92} "
                    f"C {x + 12 + dx} {y + 60}, {x + 14} {y + 36}, {x + 14} {y} Z", fill=col)
    p.append(pata(150, 240, 8, atras=True))
    p.append(pata(226, 236, -30, atras=True))
    p.append(path("M 116 236 C 108 188, 140 150, 200 148 C 262 146, 300 174, 302 224 "
                  "C 304 276, 262 298, 200 300 C 140 302, 122 280, 116 236 Z", fill=FAWN))
    p.append(path("M 256 290 C 284 282, 302 260, 300 230 C 296 212, 276 210, 268 234 C 262 256, 258 274, 256 290 Z", fill=IVORY, stroke="none", w=0))
    p.append(pata(140, 246, 14))
    p.append(pata(236, 244, -38))
    p.append(pipo_collar(262, 170, 36, ry=10))
    # el gancho de la correa
    p.append(circ(300, 186, 7, SAGE_DEEP))
    return svg(p), {"cabeza": [270, 168], "escala": 0.88, "rot": -6, "z_cabeza": "delante", "correa": [300, 186]}

def pipo_cuerpo_cae():
    """Cae del sofá: en el aire, panza al frente, patas abiertas; la cabeza abajo."""
    p = []
    p.append(pipo_cola(176, 122, s=1.0, rot=60))
    p.append(path("M 128 150 C 122 112, 160 88, 210 92 C 264 96, 296 132, 290 184 "
                  "C 284 236, 246 262, 196 258 C 146 254, 134 200, 128 150 Z", fill=FAWN))
    p.append(path("M 160 176 C 158 146, 182 130, 212 132 C 246 134, 262 160, 258 194 "
                  "C 254 224, 230 238, 202 236 C 172 234, 162 208, 160 176 Z", fill=IVORY, stroke="none", w=0))
    def pata(x, y, ang):
        d = (f"M {x - 12} {y} C {x - 16} {y + 30}, {x - 10} {y + 60}, {x - 12} {y + 84} "
             f"C {x - 14} {y + 98}, {x + 22} {y + 98}, {x + 20} {y + 84} C {x + 18} {y + 60}, {x + 16} {y + 30}, {x + 12} {y} Z")
        return grupo([path(d, fill=FAWN), path(f"M {x - 4} {y + 90} L {x - 4} {y + 96} M {x + 10} {y + 90} L {x + 10} {y + 96}", w=3)],
                     f"rotate({ang} {x} {y})")
    p.append(pata(146, 118, -118))
    p.append(pata(268, 126, 122))
    p.append(pata(146, 226, -58))
    p.append(pata(262, 232, 52))
    p.append(pipo_collar(204, 262, 40, ry=-10))
    return svg(p), {"cabeza": [204, 276], "escala": 0.92, "rot": 170, "z_cabeza": "delante"}

def pipo_cuerpo_corre():
    """Corre de perfil hacia la derecha, a lo Milú en la tapa de Tintín (B1, WS34): el cuerpo
    estirado y en el aire, las patas delanteras lanzadas adelante, las traseras atrás, la cola
    enrulada volando. La cabeza (a cámara) va adelante y arriba, mirando hacia donde corre."""
    p = []
    p.append(pipo_cola(104, 196, s=1.0, rot=-40))
    def pata(x, y, dx, dy, atras=False):
        col = FAWN_SOMBRA if atras else FAWN
        return path(f"M {x - 22} {y} C {x - 28} {y + dy * 0.4}, {x - 24 + dx * 0.8} {y + dy * 0.75}, {x - 22 + dx} {y + dy} "
                    f"C {x - 24 + dx} {y + dy + 16}, {x + 24 + dx} {y + dy + 16}, {x + 22 + dx} {y + dy} "
                    f"C {x + 22 + dx * 0.8} {y + dy * 0.75}, {x + 26} {y + dy * 0.4}, {x + 22} {y} Z", fill=col)
    # traseras (atrás, estiradas hacia atrás) y delanteras (lanzadas adelante), en dos planos
    p.append(pata(154, 244, -52, 50, atras=True))
    p.append(pata(254, 238, 46, 56, atras=True))
    # cuerpo estirado, barril largo, un poco alzado adelante
    p.append(path("M 106 232 C 100 190, 140 160, 200 154 C 268 148, 316 168, 318 218 "
                  "C 320 266, 276 292, 206 294 C 140 296, 112 274, 106 232 Z", fill=FAWN))
    p.append(path("M 262 286 C 294 276, 316 254, 316 226 C 312 208, 288 208, 278 232 C 272 254, 266 272, 262 286 Z", fill=IVORY, stroke="none", w=0))
    p.append(pata(140, 250, -58, 44))
    p.append(pata(266, 244, 54, 50))
    p.append(pipo_collar(276, 176, 36, ry=10))
    return svg(p), {"cabeza": [286, 172], "escala": 0.88, "rot": -6, "z_cabeza": "delante"}

def pipo_cuerpo_buda(gesto="rodillas"):
    """Pipo iluminado (B1, WS34): sentado a cámara en flor de loto, la panza redonda y clara,
    las patas traseras cruzadas adelante como un almohadón bajo con las almohadillas hacia
    arriba, las delanteras rectas apoyadas en las rodillas. La cabeza va derecha, arriba."""
    p = []
    p.append(pipo_cola(288, 240, s=0.9, rot=30))
    # torso pera, más ancho y bajo que el sentado (está apoyado en el piso)
    p.append(path("M 200 126 C 266 126, 314 186, 312 258 C 310 306, 268 330, 200 330 "
                  "C 132 330, 90 306, 88 258 C 86 186, 134 126, 200 126 Z", fill=FAWN))
    p.append(path("M 200 176 C 246 176, 270 216, 266 262 C 262 296, 236 312, 200 312 "
                  "C 164 312, 138 296, 134 262 C 130 216, 154 176, 200 176 Z", fill=IVORY, stroke="none", w=0))
    # las patas traseras cruzadas: un almohadón bajo y ancho con el pliegue del cruce
    p.append(path("M 96 328 C 100 300, 150 292, 200 296 C 250 292, 300 300, 304 328 "
                  "C 308 350, 276 362, 200 362 C 124 362, 92 350, 96 328 Z", fill=FAWN))
    p.append(path("M 150 300 C 178 318, 222 334, 262 344", stroke=UMBER, w=W_SEC))
    # almohadillas hacia arriba en las dos puntas
    for cx in (118, 282):
        p.append(ell(cx, 330, 20, 13, FAWN_SOMBRA, UMBER, W_SEC))
        p.append(circ(cx - 8, 326, 3.5, UMBER)); p.append(circ(cx, 323, 3.5, UMBER)); p.append(circ(cx + 8, 326, 3.5, UMBER))
    if gesto == "victoria":
        # las delanteras en Y, bien abiertas hacia arriba, y en cada punta dos "dedos" en V
        for s_ in (-1, 1):
            x0, y0 = 200 + s_ * 74, 232          # el hombro
            x1, y1 = 200 + s_ * 158, 78          # la punta de la pata, al lado de la cara
            p.append(path(f"M {x0 - 16} {y0 + 8} C {x0 - 20 + s_ * 20} {y0 - 40}, {x1 - 20} {y1 + 40}, {x1 - 18} {y1} "
                          f"C {x1 - 18} {y1 - 18}, {x1 + 18} {y1 - 18}, {x1 + 18} {y1} "
                          f"C {x1 + 20} {y1 + 40}, {x0 + 20 + s_ * 20} {y0 - 40}, {x0 + 16} {y0 + 8} Z", fill=FAWN))
            for k in (-1, 1):            # los dos "dedos" en V, bien abiertos
                p.append(ell(x1 + k * 17 + s_ * 6, y1 - 34, 9, 27, FAWN, UMBER, W_SEC, rot=k * 28 + s_ * 8))
    else:
        # patas delanteras rectas, apoyadas sobre las rodillas (el gesto de meditar)
        p.append(pipo_pata_frente(154, 236, largo=64))
        p.append(pipo_pata_frente(246, 236, largo=64))
    p.append(pipo_collar(200, 146, 52))
    return svg(p), {"cabeza": [200, 146], "escala": 1.0, "rot": 0, "pecho": [200, 240],
                    "z_cabeza": "detras" if gesto == "victoria" else "delante"}

CUERPOS_PIPO = {
    "sentado": pipo_cuerpo_sentado,
    "corre": pipo_cuerpo_corre,
    "buda": pipo_cuerpo_buda,
    "buda_victoria": lambda: pipo_cuerpo_buda("victoria"),
    "camina": pipo_cuerpo_camina,
    "panza_arriba": pipo_cuerpo_panza_arriba,
    "plantado": pipo_cuerpo_plantado,
    "cae": pipo_cuerpo_cae,
}

# =====================================================================================
# TEO · la cabeza (3/4, nunca a cámara) con miradas y bocas; el pelo despeinado
# =====================================================================================

def teo_cabeza(mirada="frente", boca="plana", pelo="normal"):
    """pelo: normal (despeinado) · caido (el mechón sobre la frente, Bully Maguire · vol. 1)."""
    p = []
    # cuello
    p.append(path("M 176 318 L 172 366 L 230 366 L 226 318 Z", fill=PIEL))
    # cara alargada, mandíbula marcada
    cara = ("M 118 190 C 118 120, 152 84, 200 84 C 250 84, 284 122, 284 196 "
            "C 284 250, 268 296, 236 322 C 222 334, 180 334, 166 322 C 134 296, 118 250, 118 190 Z")
    p.append(path(cara, fill=PIEL))
    # oreja
    p.append(path("M 118 200 C 100 192, 96 220, 112 236 C 118 240, 122 236, 122 226", fill=PIEL, w=W_SEC + 1))
    # barba de pocos días: puntitos taupe sobre mandíbula y labio superior
    import math
    for k in range(22):
        a = 0.2 * math.pi + k * 0.6 * math.pi / 21
        x, y = 200 + 74 * math.cos(a), 206 + 112 * math.sin(a)
        p.append(circ(round(x, 1), round(y, 1), 2.6, TAUPE))
    for k in range(7):
        p.append(circ(184 + k * 6, 262 + (k % 2) * 2, 2.2, TAUPE))
    # pelo: masa ondulada con volumen hacia la derecha, DESPEINADO (mechones sueltos)
    # silueta de mechones desparejos: chico a la izquierda, grande arriba, el más grande a la
    # derecha (el volumen), con muescas entre ondas para que se lean como pelo y no como gorro
    pelo_d = ("M 112 178 C 104 150, 108 118, 128 100 C 122 84, 138 68, 156 76 "
            "C 158 50, 190 38, 210 56 C 220 34, 256 30, 270 52 C 286 30, 322 40, 322 70 "
            "C 348 74, 358 110, 340 132 C 356 150, 344 178, 322 172 C 330 190, 314 202, 300 188 "
            "C 292 160, 278 140, 260 132 C 236 122, 214 130, 196 136 C 176 128, 148 134, 134 158 "
            "C 128 168, 122 178, 112 178 Z")
    p.append(path(pelo_d, fill=SAND))
    for d in ("M 156 76 C 164 90, 176 100, 190 104", "M 210 56 C 216 74, 216 92, 208 108",
              "M 270 52 C 268 72, 262 92, 250 108", "M 322 70 C 310 86, 296 100, 280 112",
              "M 340 132 C 326 136, 312 146, 302 160"):
        p.append(path(d, w=W_SEC))
    # cejas finas
    p.append(path("M 148 176 C 160 168, 178 168, 190 174", stroke=TAUPE, w=W_SEC - 1))
    p.append(path("M 218 174 C 232 166, 250 166, 262 176", stroke=TAUPE, w=W_SEC - 1))
    # ojos según la mirada (pequeños, de línea; Teo no mira a cámara)
    if mirada == "cerrada":
        # ojos cerrados: la cara de calma de la escena de la magia (D1.2 · F2). Dos párpados
        # que caen en curva suave, sin pupila.
        for cx in (166, 240):
            p.append(path(f"M {cx - 14} 194 C {cx - 6} 204, {cx + 6} 204, {cx + 14} 194", w=W_SEC))
    else:
        ex, ey = {"abajo": (2, 10), "frente": (6, 0), "arriba": (4, -8), "costado": (14, 0)}[mirada]
        for cx in (166, 240):
            p.append(path(f"M {cx - 14} 196 C {cx - 6} 188, {cx + 6} 188, {cx + 14} 196", w=W_SEC))
            p.append(circ(cx + ex, 197 + ey, 5.5, UMBER))
    # nariz
    p.append(path("M 206 208 C 212 226, 216 238, 206 244 C 200 246, 194 244, 192 240", w=W_SEC))
    # boca
    bocas = {"plana": "M 178 282 C 192 284, 214 284, 228 282",
             "sonrisa": "M 174 278 C 190 296, 220 296, 234 276",
             "abierta": "M 178 278 C 192 300, 218 300, 230 278 Z",
             "fruncida": "M 194 276 C 200 270, 212 270, 216 278 C 212 288, 198 288, 194 276 Z",
             "triste": "M 178 288 C 192 276, 216 276, 228 290"}
    p.append(path(bocas[boca], fill=(UMBER if boca in ("abierta",) else "none"), w=W_SEC))
    if pelo == "caido":
        # el mechón caído (Bully Maguire): un mechón grande que cae desde la coronilla y tapa
        # la frente y medio ojo derecho, y uno chico a la izquierda. Van al final: tapan.
        p.append(path("M 176 96 C 232 92, 272 130, 266 214 C 262 232, 238 232, 238 212 "
                      "C 240 176, 222 140, 176 128 Z", fill=SAND))
        p.append(path("M 214 112 C 246 136, 256 172, 252 208", w=W_SEC - 1))
        p.append(path("M 196 104 C 224 128, 236 160, 236 196", w=W_SEC - 1))
        p.append(path("M 150 98 C 166 118, 172 150, 160 182 C 154 192, 142 188, 144 176 "
                      "C 150 148, 146 122, 136 106 Z", fill=SAND))
    return svg(p), {"cuello": [200, 350]}

MIRADAS_TEO = ["abajo", "frente", "arriba", "costado", "cerrada"]
BOCAS_TEO = ["plana", "sonrisa", "abierta", "fruncida", "triste"]

# =====================================================================================
# TEO · cuerpos base (remera y pantalón; los gestos de cada volumen se suman en D1.2)
# =====================================================================================

def miembro(puntos, grosor=22, color=PIEL):
    """Brazo o pierna: una línea gruesa con borde tierra (doble trazo)."""
    d = "M " + " L ".join(f"{x} {y}" for x, y in puntos)
    return path(d, stroke=UMBER, w=grosor + 2 * W_SEC) + path(d, stroke=color, w=grosor)

def teo_cuerpo_parado(postura=1.0):
    """De pie, de perfil 3/4. postura 1 = erguido · 0 = encorvado (el arco de la serie)."""
    lean = (1 - postura) * 46          # hombros hacia adelante
    caida = (1 - postura) * 26         # hombros hacia abajo
    p = []
    # piernas
    p.append(path("M 176 232 L 170 340 C 166 356, 160 372, 158 388 L 196 388 L 198 340 L 202 232 Z", fill=PANTALON))
    p.append(path("M 206 232 L 212 340 C 216 356, 222 372, 226 388 L 262 388 L 248 340 L 238 232 Z", fill=PANTALON))
    # zapatillas
    p.append(path("M 150 388 C 148 398, 154 404, 166 404 L 202 404 C 206 400, 204 392, 198 388 Z", fill=IVORY, w=W_SEC + 1))
    p.append(path("M 220 388 C 216 398, 222 404, 234 404 L 274 404 C 278 400, 276 392, 268 388 Z", fill=IVORY, w=W_SEC + 1))
    # torso (remera): la espalda se curva cuando está encorvado
    sy = 92 + caida
    torso = (f"M {166 + lean} {sy} C {130 + lean * 0.8} {sy + 10}, {132 + lean * 0.4} 150, 142 236 L 258 236 "
             f"C 262 180, {262 + lean * 0.5} 130, {236 + lean} {sy} Z")
    p.append(path(torso, fill=REMERA))
    # brazos colgando
    p.append(miembro([(158 + lean, sy + 16), (134 + lean * 0.5, 160), (138, 222)], grosor=22))
    p.append(miembro([(244 + lean, sy + 16), (268 + lean * 0.5, 160), (262, 222)], grosor=22))
    p.append(circ(138, 226, 14, PIEL, UMBER, W_SEC)); p.append(circ(262, 226, 14, PIEL, UMBER, W_SEC))
    # cuello de la remera
    p.append(path(f"M {180 + lean} {sy} C {188 + lean} {sy + 12}, {214 + lean} {sy + 12}, {222 + lean} {sy}", w=W_SEC))
    return svg(p), {"cabeza": [201 + lean, sy + 4], "escala": 0.72, "rot": (1 - postura) * 20, "z_cabeza": "delante",
                    "mano_izq": [138, 226], "mano_der": [262, 226]}

def teo_cuerpo_sentado(encorvado=1.0):
    """Sentado de perfil (banco, silla, rincón), manos adelante: el teléfono o el cuadernito.
    encorvado 1 = doblado sobre las manos · 0 = derecho."""
    h = encorvado
    p = []
    # pierna de atrás (más oscura) y de adelante: muslo horizontal, canilla vertical, zapatilla
    for k, (dx, dy, col) in enumerate(((-14, 8, "#6f665b"), (0, 0, PANTALON))):
        p.append(miembro([(158 + dx, 246 + dy), (262 + dx, 246 + dy), (270 + dx, 344 + dy)], grosor=34, color=col))
        p.append(path(f"M {250 + dx} {344 + dy} C {244 + dx} {358 + dy}, {254 + dx} {366 + dy}, {268 + dx} {366 + dy} L {306 + dx} {366 + dy} "
                      f"C {310 + dx} {358 + dy}, {304 + dx} {348 + dy}, {292 + dx} {344 + dy} Z", fill=IVORY, w=W_SEC + 1))
    # torso: de la cadera al hombro, inclinado hacia adelante si está encorvado
    sx, sy = 176 + 54 * h, 108 + 34 * h        # hombro
    torso = (f"M 146 262 C 140 210, 150 160, {sx - 16} {sy + 4} C {sx} {sy - 10}, {sx + 44} {sy - 10}, {sx + 52} {sy + 6} "
             f"C {sx + 44 - 20 * h} 160, {236 - 10 * h} 210, 226 262 Z")
    p.append(path(torso, fill=REMERA))
    p.append(path(f"M {sx + 2} {sy - 2} C {sx + 12} {sy + 10}, {sx + 32} {sy + 10}, {sx + 40} {sy - 2}", w=W_SEC))
    # brazos: del hombro a las manos, adelante del cuerpo
    codo = (sx + 30 - 10 * h, sy + 70)
    mano = (246, 214)
    p.append(miembro([(sx + 22, sy + 14), codo, mano], grosor=22))
    p.append(circ(mano[0], mano[1], 15, PIEL, UMBER, W_SEC))
    return svg(p), {"cabeza": [sx + 22, sy + 2], "escala": 0.72, "rot": 24 * h, "z_cabeza": "delante",
                    "manos": [246, 214]}

# =====================================================================================
# TEO · la escena de la magia (D1.2 · F, WS33): medita · camina erguido
# =====================================================================================

def teo_cuerpo_medita():
    """Sentado de frente con las piernas cruzadas, la espalda derecha y las manos apoyadas
    en las rodillas. Es la pequeña acción de la escena 4 (F2) y va con la cara `cerrada`."""
    p = []
    # las piernas cruzadas como una sola forma ancha y baja (leen en un vistazo), con dos
    # pliegues que marcan las canillas cruzadas y las zapatillas asomando adelante
    p.append(path("M 152 268 C 108 270, 66 296, 70 320 C 76 350, 140 356, 200 354 "
                  "C 260 356, 324 350, 330 320 C 334 296, 292 270, 248 268 Z", fill=PANTALON))
    p.append(path("M 92 322 C 150 334, 222 338, 296 304", stroke=UMBER, w=W_SEC))
    p.append(path("M 308 322 C 250 334, 178 338, 104 304", stroke=UMBER, w=W_SEC))
    p.append(path("M 150 338 C 136 344, 136 362, 154 366 L 184 366 C 194 358, 190 344, 178 338 Z", fill=IVORY, w=W_SEC + 1))
    p.append(path("M 222 338 C 210 344, 206 358, 216 366 L 246 366 C 264 362, 264 344, 250 338 Z", fill=IVORY, w=W_SEC + 1))
    # torso derecho (remera)
    p.append(path("M 158 104 C 142 160, 146 230, 152 278 L 248 278 C 254 230, 258 160, 242 104 Z", fill=REMERA))
    p.append(path("M 180 104 C 188 116, 212 116, 220 104", w=W_SEC))
    # brazos relajados, codos hacia afuera, manos en las rodillas
    p.append(miembro([(154, 120), (108, 200), (94, 292)], grosor=22))
    p.append(miembro([(246, 120), (292, 200), (306, 292)], grosor=22))
    p.append(circ(94, 298, 14, PIEL, UMBER, W_SEC)); p.append(circ(306, 298, 14, PIEL, UMBER, W_SEC))
    return svg(p), {"cabeza": [200, 108], "escala": 0.72, "rot": 0, "z_cabeza": "delante",
                    "pecho": [200, 170]}

def teo_cuerpo_camina(fase=0.0):
    """Camina erguido de perfil hacia la derecha, en 4 fases (como Pipo). Brazos y piernas se
    cruzan; el cuerpo entero sube y baja apenas. Es el paseo de F2 y sirve para todo el arco."""
    import math
    sw = math.sin(fase * 2 * math.pi)
    salto = 5 * abs(math.cos(fase * 2 * math.pi))
    p = []
    def zapatilla(fx, fy):
        return path(f"M {fx - 20} {fy} C {fx - 26} {fy + 8}, {fx - 18} {fy + 16}, {fx - 6} {fy + 16} L {fx + 26} {fy + 16} "
                    f"C {fx + 34} {fy + 12}, {fx + 32} {fy + 6}, {fx + 22} {fy} Z", fill=IVORY, w=W_SEC + 1)
    # pierna y brazo de atrás (más oscuros, detrás del torso)
    p.append(miembro([(196, 226), (196 - 24 * sw, 300), (196 - 50 * sw, 372)], grosor=30, color="#6f665b"))
    p.append(zapatilla(196 - 50 * sw, 372))
    p.append(miembro([(190, 116), (186 - 30 * sw, 172), (184 - 44 * sw, 222)], grosor=20, color="#e4d8c4"))
    # torso de perfil, derecho, con el ancho del `parado`
    p.append(path("M 158 96 C 140 132, 148 200, 156 232 L 246 232 C 256 200, 262 132, 244 96 Z", fill=REMERA))
    p.append(path("M 180 96 C 188 108, 214 108, 222 96", w=W_SEC))
    # pierna y brazo de adelante
    p.append(miembro([(210, 226), (210 + 24 * sw, 300), (210 + 50 * sw, 372)], grosor=30, color=PANTALON))
    p.append(zapatilla(210 + 50 * sw, 372))
    p.append(miembro([(232, 116), (238 + 30 * sw, 172), (236 + 44 * sw, 222)], grosor=22))
    p.append(circ(236 + 44 * sw, 226, 13, PIEL, UMBER, W_SEC))
    return svg([grupo(p, f"translate(0 {-salto:.1f})")]), {"cabeza": [204, 100 - salto], "escala": 0.72, "rot": 0,
                                                           "z_cabeza": "delante", "mano": [236 + 44 * sw, 226 - salto]}

def teo_cuerpo_corre():
    """Corre de perfil hacia la derecha, a lo Tintín en la tapa (B1, WS34): el torso bien
    inclinado hacia adelante (los hombros adelante de la cadera), los brazos bombeando en
    ángulo recto con los puños cerrados, la pierna de adelante con la rodilla alta y la de
    atrás con el talón levantado. Es la pose memorable del cartel."""
    p = []
    def zapatilla(fx, fy, ang=0):
        d = (f"M {fx - 20} {fy} C {fx - 26} {fy + 8}, {fx - 18} {fy + 16}, {fx - 6} {fy + 16} L {fx + 26} {fy + 16} "
             f"C {fx + 34} {fy + 12}, {fx + 32} {fy + 6}, {fx + 22} {fy} Z")
        return grupo([path(d, fill=IVORY, w=W_SEC + 1)], f"rotate({ang} {fx} {fy})")
    # pierna y brazo de atrás (más oscuros): el talón levantado atrás, el puño atrás y arriba
    p.append(miembro([(172, 236), (128, 300), (98, 262)], grosor=30, color="#6f665b"))
    p.append(zapatilla(94, 254, ang=-70))
    p.append(miembro([(236, 116), (184, 156), (166, 108)], grosor=20, color="#e4d8c4"))
    p.append(circ(164, 102, 13, "#e4d8c4", UMBER, W_SEC))
    # torso inclinado hacia adelante: la cadera atrás, los hombros bien adelante
    p.append(path("M 140 242 C 132 200, 176 140, 228 100 L 306 112 C 296 156, 264 206, 232 246 Z", fill=REMERA))
    p.append(path("M 248 104 C 254 116, 280 120, 290 110", w=W_SEC))
    # pierna de adelante: rodilla alta, pie adelante y abajo
    p.append(miembro([(196, 240), (272, 262), (296, 338)], grosor=30, color=PANTALON))
    p.append(zapatilla(298, 340, ang=22))
    # brazo de adelante: codo adelante, puño arriba a la altura del pecho
    p.append(miembro([(286, 122), (336, 158), (364, 116)], grosor=22))
    p.append(circ(366, 110, 13, PIEL, UMBER, W_SEC))
    return svg(p), {"cabeza": [268, 106], "escala": 0.72, "rot": 14, "z_cabeza": "delante",
                    "mano": [366, 110]}

# =====================================================================================
# TEO · vol. 1 (Vínculos, WS35): el paso de Spiderman
# =====================================================================================

def _pistolita(x, y, ang=0, s=1.0):
    """La mano haciendo pistolita: puño, el índice estirado hacia la derecha, el pulgar arriba."""
    piezas = [miembro([(x, y), (x + 46 * s, y - 2 * s)], grosor=12 * s),      # el índice
              miembro([(x + 2 * s, y - 4 * s), (x + 8 * s, y - 34 * s)], grosor=11 * s),  # el pulgar
              ell(x, y + 2 * s, 17 * s, 15 * s, PIEL, UMBER, W_SEC),      # el puño
              path(f"M {x + 4 * s} {y + 4 * s} C {x + 12 * s} {y + 2 * s}, {x + 12 * s} {y + 12 * s}, {x + 4 * s} {y + 12 * s}", w=W_SEC - 1)]   # los dedos doblados
    return grupo(piezas, f"rotate({ang} {x} {y})")

def teo_cuerpo_spiderman():
    """El paso de Bully Maguire (vol. 1, la calle): la cadera echada hacia atrás y el torso
    hacia atrás también (chulo), un pie adelante con la punta hacia abajo como si fuera
    bailando, los dos brazos hacia adelante haciendo pistolitas con los dedos. La cabeza va
    apenas echada hacia atrás (rot negativa), con el pelo caído."""
    p = []
    def zapatilla(fx, fy, ang=0):
        d = (f"M {fx - 20} {fy} C {fx - 26} {fy + 8}, {fx - 18} {fy + 16}, {fx - 6} {fy + 16} L {fx + 26} {fy + 16} "
             f"C {fx + 34} {fy + 12}, {fx + 32} {fy + 6}, {fx + 22} {fy} Z")
        return grupo([path(d, fill=IVORY, w=W_SEC + 1)], f"rotate({ang} {fx} {fy})")
    # pierna de atrás, plantada (más oscura) · pierna de adelante estirada con la punta abajo
    p.append(miembro([(166, 244), (152, 318), (150, 384)], grosor=30, color="#6f665b"))
    p.append(zapatilla(154, 388, ang=0))
    p.append(miembro([(200, 246), (256, 300), (306, 370)], grosor=30, color=PANTALON))
    p.append(zapatilla(318, 380, ang=-18))                     # el talón adelante, la punta arriba: el paso
    # brazo de atrás (más claro), ANTES del torso: el codo hacia atrás, la pistola adelante y abajo
    p.append(miembro([(160, 128), (146, 204), (232, 222)], grosor=20, color="#e4d8c4"))
    # torso echado hacia atrás: los hombros ATRÁS de la cadera, la cadera hacia adelante
    p.append(path("M 148 106 C 126 150, 136 202, 154 250 L 240 250 C 250 202, 240 150, 222 106 Z", fill=REMERA))
    p.append(path("M 164 106 C 172 118, 200 118, 208 106", w=W_SEC))
    p.append(_pistolita(242, 224, ang=12, s=1.4))
    # brazo de adelante: el codo afuera y adelante, la pistola alta apuntando a las chicas
    p.append(miembro([(224, 124), (270, 192), (322, 150)], grosor=22))
    p.append(_pistolita(332, 146, ang=-26, s=1.5))
    return svg(p), {"cabeza": [186, 110], "escala": 0.72, "rot": -12, "z_cabeza": "delante",
                    "mano": [332, 128]}

# =====================================================================================
# LA FAMILIA · vol. 1 (Vínculos, WS35): papá, mamá y la hermanita, riéndose
# Una sola pieza compuesta (lienzo apaisado 800×560) con dos estados: `living` (en el sofá,
# la hermanita acaricia a Pipo) y `mesa` (atrás de la mesa, solo torsos). Capa ilustrada:
# son los que cargan la emoción del volumen (REGLAS §1).
# =====================================================================================

PELO_PAPA = "#6f665b"; PELO_MAMA = "#463f38"; VESTIDO = "#c9b99b"; CAMISA = "#e6dccb"; REMERA_NENA = "#b9cbb3"

def _regazo(cx, y0, medio, y1, color):
    """El regazo de alguien sentado a cámara: un bloque redondeado, más ancho abajo (las
    rodillas), del que cuelgan las canillas. Es lo que hace que se lea SENTADO."""
    return path(f"M {cx - medio * 0.8} {y0} L {cx + medio * 0.8} {y0} C {cx + medio * 0.95} {y0 + 40}, {cx + medio * 1.05} {y1 - 30}, {cx + medio} {y1 - 12} "
                f"C {cx + medio * 0.9} {y1 + 4}, {cx + medio * 0.55} {y1 + 6}, {cx + medio * 0.45} {y1 - 8} "
                f"L {cx - medio * 0.45} {y1 - 8} C {cx - medio * 0.55} {y1 + 6}, {cx - medio * 0.9} {y1 + 4}, {cx - medio} {y1 - 12} "
                f"C {cx - medio * 1.05} {y1 - 30}, {cx - medio * 0.95} {y0 + 40}, {cx - medio * 0.8} {y0} Z", fill=color)

def _cara_riendo(cx, cy, r, tilt=0, boca=1.0):
    """Cabeza a cámara riéndose: ojos cerrados de alegría (dos arcos), boca abierta, rubor."""
    p = [circ(cx, cy, r, PIEL, UMBER, W_MAIN - 2)]
    for lado in (-1, 1):
        ex = cx + lado * r * 0.42
        ey = cy - r * 0.12
        p.append(path(f"M {ex - r * 0.2} {ey + 2} C {ex - r * 0.1} {ey - r * 0.18}, {ex + r * 0.1} {ey - r * 0.18}, {ex + r * 0.2} {ey + 2}", w=W_SEC))
        p.append(circ(cx + lado * r * 0.62, cy + r * 0.28, r * 0.13, "#e6c7b2"))
    m = r * 0.42 * boca
    p.append(path(f"M {cx - m} {cy + r * 0.3} C {cx - m * 0.6} {cy + r * 0.3 + m * 1.6}, {cx + m * 0.6} {cy + r * 0.3 + m * 1.6}, {cx + m} {cy + r * 0.3} Z",
                  fill=UMBER, w=W_SEC))
    p.append(path(f"M {cx - m * 0.55} {cy + r * 0.3 + m * 0.9} C {cx - m * 0.25} {cy + r * 0.3 + m * 1.35}, {cx + m * 0.25} {cy + r * 0.3 + m * 1.35}, {cx + m * 0.55} {cy + r * 0.3 + m * 0.9}",
                  fill=TONGUE, stroke="none", w=0))
    p.append(path(f"M {cx - r * 0.05} {cy + r * 0.02} C {cx + r * 0.08} {cy + r * 0.1}, {cx + r * 0.06} {cy + r * 0.18}, {cx - r * 0.02} {cy + r * 0.2}", w=W_SEC - 1))
    return grupo(p, f"rotate({tilt} {cx} {cy})")

def _pelo_papa(cx, cy, r):
    """Pelo corto con entradas, y un bigote."""
    return grupo([path(f"M {cx - r * 0.95} {cy - r * 0.1} C {cx - r * 0.9} {cy - r * 0.9}, {cx - r * 0.3} {cy - r * 1.12}, {cx + r * 0.1} {cy - r * 1.02} "
                       f"C {cx + r * 0.5} {cy - r * 1.14}, {cx + r * 0.98} {cy - r * 0.8}, {cx + r * 0.96} {cy - r * 0.1} "
                       f"C {cx + r * 0.7} {cy - r * 0.55}, {cx + r * 0.2} {cy - r * 0.72}, {cx - r * 0.2} {cy - r * 0.62} "
                       f"C {cx - r * 0.6} {cy - r * 0.62}, {cx - r * 0.85} {cy - r * 0.4}, {cx - r * 0.95} {cy - r * 0.1} Z", fill=PELO_PAPA),
                  path(f"M {cx - r * 0.34} {cy + r * 0.24} C {cx - r * 0.2} {cy + r * 0.1}, {cx - r * 0.04} {cy + r * 0.12}, {cx} {cy + r * 0.24} "
                       f"C {cx + r * 0.04} {cy + r * 0.12}, {cx + r * 0.2} {cy + r * 0.1}, {cx + r * 0.34} {cy + r * 0.24} "
                       f"C {cx + r * 0.2} {cy + r * 0.34}, {cx - r * 0.2} {cy + r * 0.34}, {cx - r * 0.34} {cy + r * 0.24} Z", fill=PELO_PAPA, w=W_SEC - 1)])

def _pelo_mama(cx, cy, r):
    """Pelo largo oscuro que cae a los lados, con raya al medio y un rodete arriba."""
    return grupo([path(f"M {cx - r * 1.08} {cy + r * 0.9} C {cx - r * 1.2} {cy}, {cx - r * 0.9} {cy - r * 1.1}, {cx} {cy - r * 1.08} "
                       f"C {cx + r * 0.9} {cy - r * 1.1}, {cx + r * 1.2} {cy}, {cx + r * 1.08} {cy + r * 0.9} "
                       f"L {cx + r * 0.78} {cy + r * 0.86} C {cx + r * 0.86} {cy + r * 0.1}, {cx + r * 0.6} {cy - r * 0.62}, {cx} {cy - r * 0.7} "
                       f"C {cx - r * 0.6} {cy - r * 0.62}, {cx - r * 0.86} {cy + r * 0.1}, {cx - r * 0.78} {cy + r * 0.86} Z", fill=PELO_MAMA),
                  circ(cx + r * 0.12, cy - r * 1.14, r * 0.3, PELO_MAMA, UMBER, W_SEC)])

def _pelo_nena(cx, cy, r):
    """Flequillo y dos colitas que saltan (se ríe), del color del pelo de Teo (la familia)."""
    p = [path(f"M {cx - r * 0.98} {cy + r * 0.05} C {cx - r * 0.9} {cy - r * 0.9}, {cx - r * 0.3} {cy - r * 1.15}, {cx + r * 0.05} {cy - r * 1.05} "
              f"C {cx + r * 0.5} {cy - r * 1.15}, {cx + r * 1.0} {cy - r * 0.8}, {cx + r * 0.98} {cy + r * 0.05} "
              f"C {cx + r * 0.72} {cy - r * 0.34}, {cx + r * 0.3} {cy - r * 0.5}, {cx} {cy - r * 0.4} "
              f"C {cx - r * 0.3} {cy - r * 0.5}, {cx - r * 0.72} {cy - r * 0.34}, {cx - r * 0.98} {cy + r * 0.05} Z", fill=SAND)]
    for lado in (-1, 1):
        bx = cx + lado * r * 1.02
        by = cy - r * 0.2
        p.append(path(f"M {bx} {by} C {bx + lado * r * 0.5} {by - r * 0.5}, {bx + lado * r * 0.95} {by - r * 0.1}, {bx + lado * r * 0.8} {by + r * 0.55} "
                      f"C {bx + lado * r * 0.7} {by + r * 0.85}, {bx + lado * r * 0.2} {by + r * 0.6}, {bx} {by} Z", fill=SAND))
        p.append(circ(bx, by, r * 0.14, SAGE, UMBER, W_SEC - 1))     # la gomita salvia (el único acento)
    return grupo(p)

def familia(estado="living"):
    """Los tres riéndose. living: sentados en el sofá (cadera en y=250, pies en y≈520), la
    hermanita adelante en el medio con el brazo estirado hacia abajo a la izquierda (ancla
    `mano_nena`, donde va Pipo panza arriba). mesa: solo torsos, brazos sobre la mesa; la
    mesa del fondo tapa de la cintura para abajo."""
    p = []
    living = estado == "living"
    # ---- papá (grande, a la izquierda), el brazo por atrás de mamá
    px, py, pr = 200, 108, 56
    if living:
        for dx in (-30, 30):                          # canillas que cuelgan del regazo
            p.append(miembro([(px + dx * 1.7, 326), (px + dx * 1.7, 500)], grosor=34, color=PANTALON))
            p.append(path(f"M {px + dx * 1.7 - 26} 500 C {px + dx * 1.7 - 32} 512, {px + dx * 1.7 - 22} 522, {px + dx * 1.7 - 6} 522 "
                          f"L {px + dx * 1.7 + 30} 522 C {px + dx * 1.7 + 38} 516, {px + dx * 1.7 + 34} 506, {px + dx * 1.7 + 24} 500 Z", fill=IVORY, w=W_SEC + 1))
        p.append(_regazo(px, 246, 104, 336, PANTALON))
    p.append(path(f"M {px - 92} 176 C {px - 96} 230, {px - 90} 250, {px - 86} 262 L {px + 90} 262 C {px + 94} 250, {px + 96} 230, {px + 88} 176 "
                  f"C {px + 60} 160, {px - 60} 160, {px - 92} 176 Z", fill=CAMISA))
    p.append(path(f"M {px - 18} 170 L {px} 190 L {px + 18} 170", w=W_SEC))
    p.append(miembro([(px + 84, 190), (px + 112, 250), (px + 72, 262 if living else 250)], grosor=26))
    p.append(circ(px + 70, 262 if living else 250, 16, PIEL, UMBER, W_SEC))
    p.append(miembro([(px - 84, 190), (px - 110, 250), (px - 70, 262 if living else 250)], grosor=26))
    p.append(circ(px - 68, 262 if living else 250, 16, PIEL, UMBER, W_SEC))
    p.append(_cara_riendo(px, py, pr, tilt=-8))
    p.append(_pelo_papa(px, py, pr))
    # ---- mamá (a la derecha), la mano en el pecho de la risa
    mx, my, mr = 600, 118, 50
    if living:
        for dx in (-26, 26):
            p.append(miembro([(mx + dx * 1.5, 326), (mx + dx * 1.5, 500)], grosor=28, color=PIEL))
            p.append(path(f"M {mx + dx * 1.5 - 24} 500 C {mx + dx * 1.5 - 30} 512, {mx + dx * 1.5 - 20} 522, {mx + dx * 1.5 - 4} 522 "
                          f"L {mx + dx * 1.5 + 26} 522 C {mx + dx * 1.5 + 34} 516, {mx + dx * 1.5 + 30} 506, {mx + dx * 1.5 + 20} 500 Z", fill=UMBER, w=W_SEC + 1))
        p.append(_regazo(mx, 246, 92, 336, VESTIDO))
    p.append(path(f"M {mx - 80} 184 C {mx - 86} 230, {mx - 80} 250, {mx - 76} 262 L {mx + 80} 262 C {mx + 84} 250, {mx + 88} 230, {mx + 78} 184 "
                  f"C {mx + 50} 168, {mx - 50} 168, {mx - 80} 184 Z", fill=VESTIDO))
    p.append(miembro([(mx + 74, 196), (mx + 96, 250), (mx + 56, 262 if living else 250)], grosor=22))
    p.append(circ(mx + 54, 262 if living else 250, 15, PIEL, UMBER, W_SEC))
    p.append(miembro([(mx - 72, 196), (mx - 90, 240), (mx - 30, 214)], grosor=22))              # la mano al pecho
    p.append(circ(mx - 26, 212, 15, PIEL, UMBER, W_SEC))
    p.append(_cara_riendo(mx, my, mr, tilt=10))
    p.append(_pelo_mama(mx, my, mr))
    # ---- la hermanita (chica, adelante en el medio)
    nx, ny, nr = 400, 196 if living else 140, 40
    if living:
        for dx in (-18, 18):
            p.append(miembro([(nx + dx * 1.4, 356), (nx + dx * 1.4, 470)], grosor=20, color=PIEL))
            p.append(path(f"M {nx + dx * 1.4 - 20} 470 C {nx + dx * 1.4 - 26} 480, {nx + dx * 1.4 - 16} 490, {nx + dx * 1.4 - 2} 490 "
                          f"L {nx + dx * 1.4 + 22} 490 C {nx + dx * 1.4 + 28} 484, {nx + dx * 1.4 + 26} 476, {nx + dx * 1.4 + 16} 470 Z", fill=SAGE, w=W_SEC + 1))
        p.append(_regazo(nx, 300, 66, 364, PANTALON))
        p.append(path(f"M {nx - 58} 250 C {nx - 64} 280, {nx - 58} 300, {nx - 54} 312 L {nx + 54} 312 C {nx + 58} 300, {nx + 64} 280, {nx + 56} 250 "
                      f"C {nx + 30} 236, {nx - 30} 236, {nx - 58} 250 Z", fill=REMERA_NENA))
        # el brazo estirado hacia abajo a la izquierda: acaricia a Pipo
        p.append(miembro([(nx - 50, 258), (nx - 110, 292), (nx - 134, 356)], grosor=18))
        p.append(circ(nx - 136, 360, 13, PIEL, UMBER, W_SEC))
        p.append(miembro([(nx + 50, 258), (nx + 78, 296), (nx + 62, 318)], grosor=18))
        p.append(circ(nx + 60, 320, 13, PIEL, UMBER, W_SEC))
        mano_nena = [nx - 136, 360]
    else:
        p.append(path(f"M {nx - 58} 194 C {nx - 64} 224, {nx - 58} 244, {nx - 54} 256 L {nx + 54} 256 C {nx + 58} 244, {nx + 64} 224, {nx + 56} 194 "
                      f"C {nx + 30} 180, {nx - 30} 180, {nx - 58} 194 Z", fill=REMERA_NENA))
        for lado in (-1, 1):
            p.append(miembro([(nx + lado * 50, 202), (nx + lado * 74, 240), (nx + lado * 40, 254)], grosor=18))
            p.append(circ(nx + lado * 38, 254, 13, PIEL, UMBER, W_SEC))
        mano_nena = [nx, 254]
    p.append(_cara_riendo(nx, ny, nr, tilt=-14, boca=0.9))
    p.append(_pelo_nena(nx, ny, nr))
    anclas = {"centro": [400, 250], "mano_nena": mano_nena, "tipo": "grupo", "lienzo_w": 800, "lienzo_h": 560}
    return svg(p, w=800, h=560), anclas

# =====================================================================================
# EXTRAS · vol. 1: las chicas que pasan de largo, DE ESPALDAS (lo que se lee: no le dan bola)
# =====================================================================================

PELO_CHICA_1 = "#463f38"; PELO_CHICA_2 = "#b39a72"; VESTIDO_1 = "#e6dccb"; VESTIDO_2 = "#c9b99b"

def _chica_espaldas(cx, top, pelo, vestido, telefono=False, paso=1.0, largo_pelo=1.0):
    """Una chica de espaldas caminando hacia la derecha: la melena tapa la cabeza, vestido
    corto, piernas en zancada. Si `telefono`, el brazo derecho sube con el teléfono."""
    p = []
    r = 40
    cy = top + r
    # piernas en zancada
    p.append(miembro([(cx - 6, cy + 150), (cx - 30 * paso, cy + 236), (cx - 40 * paso, cy + 300)], grosor=18, color=PIEL))
    p.append(miembro([(cx + 8, cy + 150), (cx + 34 * paso, cy + 230), (cx + 46 * paso, cy + 300)], grosor=18, color=PIEL))
    for fx in (cx - 40 * paso, cx + 46 * paso):
        p.append(path(f"M {fx - 16} {cy + 300} L {fx + 14} {cy + 300} C {fx + 20} {cy + 306}, {fx + 18} {cy + 314}, {fx + 10} {cy + 314} L {fx - 14} {cy + 314} Z", fill=UMBER, w=W_SEC))
    # vestido (trapecio) y brazos
    p.append(path(f"M {cx - 36} {cy + 46} L {cx + 36} {cy + 46} L {cx + 56} {cy + 160} L {cx - 56} {cy + 160} Z", fill=vestido))
    p.append(miembro([(cx - 34, cy + 56), (cx - 50, cy + 110), (cx - 42, cy + 150)], grosor=16))
    if telefono:
        p.append(miembro([(cx + 34, cy + 56), (cx + 62, cy + 90), (cx + 50, cy + 40)], grosor=16))
        p.append(f'<rect x="{cx + 40}" y="{cy + 8}" width="24" height="40" rx="5" fill="{UMBER}" stroke="{UMBER}" stroke-width="{W_SEC}"/>')
    else:
        p.append(miembro([(cx + 34, cy + 56), (cx + 52, cy + 110), (cx + 44, cy + 150)], grosor=16))
    # el cuello y la melena, vista desde atrás: solo pelo
    p.append(path(f"M {cx - 10} {cy + 30} L {cx + 10} {cy + 30} L {cx + 10} {cy + 50} L {cx - 10} {cy + 50} Z", fill=PIEL, w=W_SEC))
    p.append(path(f"M {cx - r} {cy} C {cx - r} {cy - r * 1.3}, {cx + r} {cy - r * 1.3}, {cx + r} {cy} "
                  f"C {cx + r * 1.05} {cy + 30 * largo_pelo}, {cx + r * 0.9} {cy + 70 * largo_pelo}, {cx + r * 0.7} {cy + 90 * largo_pelo} "
                  f"L {cx - r * 0.7} {cy + 90 * largo_pelo} C {cx - r * 0.9} {cy + 70 * largo_pelo}, {cx - r * 1.05} {cy + 30 * largo_pelo}, {cx - r} {cy} Z", fill=pelo))
    p.append(path(f"M {cx} {cy - r * 0.95} C {cx + 4} {cy - 20}, {cx + 2} {cy + 20}, {cx} {cy + 60 * largo_pelo}", stroke=UMBER, w=W_SEC - 2))
    return grupo(p)

def chicas_pasan():
    """Dos chicas de espaldas yéndose hacia la derecha; la de adelante mira su teléfono."""
    p = [_chica_espaldas(150, 30, PELO_CHICA_2, VESTIDO_2, telefono=False, paso=1.0, largo_pelo=0.7),
         _chica_espaldas(262, 46, PELO_CHICA_1, VESTIDO_1, telefono=True, paso=-0.8, largo_pelo=1.0)]
    return svg(p), {"centro": [200, 200], "tipo": "grupo"}

# =====================================================================================
# PROPS · la escena de la magia (D1.2 · F): el teléfono que se pone verde · el cuadernito
# Piezas grandes en su lienzo; se pegan con `escala_rel` × la escala del personaje.
# =====================================================================================

SAGE_LIGHT = "#b9cbb3"; SAGE_GLOW = "#d5e2cf"

def prop_telefono(nivel=0):
    """Algo parecido a un teléfono. nivel 0 = apagado · 1 = se enciende (desde abajo) ·
    2 = pantalla entera salvia · 3 = salvia respirando (centro más claro). La pantalla ENTERA
    se enciende, no un halo alrededor (pedido de Tomás, WS32)."""
    p = []
    defs = ('<defs>'
            '<linearGradient id="enciende" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{NOSE}"/><stop offset="0.45" stop-color="{SAGE_DEEP}"/><stop offset="1" stop-color="{SAGE}"/>'
            '</linearGradient>'
            '<radialGradient id="respira" cx="0.5" cy="0.5" r="0.6">'
            f'<stop offset="0" stop-color="{SAGE_GLOW}"/><stop offset="0.55" stop-color="{SAGE_LIGHT}"/><stop offset="1" stop-color="{SAGE}"/>'
            '</radialGradient></defs>')
    p.append(defs)
    p.append(f'<rect x="118" y="60" width="164" height="280" rx="26" fill="{UMBER}" stroke="{UMBER}" stroke-width="{W_MAIN}"/>')
    pantalla = {0: NOSE, 1: "url(#enciende)", 2: SAGE, 3: "url(#respira)"}[nivel]
    p.append(f'<rect x="134" y="86" width="132" height="228" rx="12" fill="{pantalla}"/>')
    if nivel == 0:      # reflejo apagado: una diagonal apenas
        p.append(path("M 150 290 L 250 110", stroke="#5a524a", w=W_SEC))
    p.append(path("M 182 74 L 218 74", stroke=DUST, w=4))
    p.append(path("M 176 328 L 224 328", stroke=DUST, w=4))
    return svg(p), {"centro": [200, 200], "escala_rel": 0.32, "tipo": "prop"}

def prop_cuadernito(avance=0):
    """Cuadernito abierto con lápiz. avance 0..3 = cuántas líneas ya escribió (el lápiz avanza)."""
    p = []
    p.append(f'<rect x="70" y="90" width="260" height="220" rx="10" fill="{IVORY}" stroke="{UMBER}" stroke-width="{W_MAIN - 2}"/>')
    for k in range(6):
        p.append(circ(70, 110 + k * 36, 8, "none", UMBER, W_SEC))
    filas = [138, 180, 222, 264]
    escrito = {0: [0, 0, 0, 0], 1: [1, 0.5, 0, 0], 2: [1, 1, 1, 0], 3: [1, 1, 1, 0.8]}[avance]
    x0, x1 = 108, 300
    for y, f in zip(filas, escrito):
        p.append(path(f"M {x0} {y} L {x1} {y}", stroke=SAND, w=3))
        if f > 0:
            xf = x0 + (x1 - x0) * f
            d = f"M {x0} {y}"
            x = x0
            while x < xf - 6:
                d += f" q 6 -9 12 0 q 6 9 12 0"
                x += 24
            p.append(path(d, stroke=TAUPE, w=4))
    # el lápiz: la punta en el final de la última línea escrita
    ult = max([k for k, f in enumerate(escrito) if f > 0], default=0)
    tx = x0 + (x1 - x0) * (escrito[ult] if escrito[ult] > 0 else 0)
    ty = filas[ult]
    p.append(path(f"M {tx} {ty} L {tx + 14} {ty - 22} L {tx + 96} {ty - 128} L {tx + 116} {ty - 112} L {tx + 34} {ty - 6} Z", fill=SAND, w=W_SEC + 1))
    p.append(path(f"M {tx} {ty} L {tx + 14} {ty - 22} L {tx + 34} {ty - 6} Z", fill=UMBER, w=W_SEC))
    return svg(p), {"centro": [200, 200], "escala_rel": 0.36, "tipo": "prop"}

# =====================================================================================
# render
# =====================================================================================

def escribir(personaje, nombre, contenido, anclas, indice):
    carpeta = os.path.join(DESTINO, personaje)
    os.makedirs(carpeta, exist_ok=True)
    ruta_svg = os.path.join(carpeta, nombre + ".svg")
    ruta_png = os.path.join(carpeta, nombre + ".png")
    with open(ruta_svg, "w") as f:
        f.write(contenido)
    lw, lh = anclas.get("lienzo_w", LIENZO), anclas.get("lienzo_h", LIENZO)     # piezas apaisadas (la familia)
    subprocess.run(["rsvg-convert", "-w", str(lw * ESCALA_PNG), "-h", str(lh * ESCALA_PNG),
                    "-o", ruta_png, ruta_svg], check=True)
    indice.setdefault(personaje, {})[nombre] = dict(anclas, png=os.path.relpath(ruta_png, RAIZ), lienzo=LIENZO, escala_png=ESCALA_PNG)

def generar(solo=None):
    indice = {}
    if solo in (None, "pipo"):
        for nombre, cara in CARAS_PIPO.items():
            s, a = pipo_cabeza(cara); escribir("pipo", "cara_" + nombre, s, dict(a, tipo="cabeza"), indice)
        for nombre, fn in CUERPOS_PIPO.items():
            s, a = fn(); escribir("pipo", "cuerpo_" + nombre, s, dict(a, tipo="cuerpo"), indice)
        for k in range(4):   # el ciclo de caminar en 4 fases
            s, a = pipo_cuerpo_camina(k / 4); escribir("pipo", "cuerpo_camina_%d" % k, s, dict(a, tipo="cuerpo"), indice)
    if solo in (None, "teo"):
        for m in MIRADAS_TEO:
            for b in BOCAS_TEO:
                s, a = teo_cabeza(m, b); escribir("teo", f"cara_{m}_{b}", s, dict(a, tipo="cabeza"), indice)
        for nombre, fn, kw in (("parado", teo_cuerpo_parado, dict(postura=1.0)), ("encorvado", teo_cuerpo_parado, dict(postura=0.0)),
                               ("sentado", teo_cuerpo_sentado, dict(encorvado=1.0)), ("sentado_erguido", teo_cuerpo_sentado, dict(encorvado=0.2)),
                               ("medita", teo_cuerpo_medita, {}), ("corre", teo_cuerpo_corre, {}),
                               ("spiderman", teo_cuerpo_spiderman, {})):
            s, a = fn(**kw); escribir("teo", "cuerpo_" + nombre, s, dict(a, tipo="cuerpo"), indice)
        for k in range(4):   # el paseo erguido en 4 fases
            s, a = teo_cuerpo_camina(k / 4); escribir("teo", "cuerpo_camina_%d" % k, s, dict(a, tipo="cuerpo"), indice)
        for m in ("costado", "frente"):   # vol. 1: la cara con el pelo caído (Bully Maguire)
            s, a = teo_cabeza(m, "sonrisa", pelo="caido"); escribir("teo", f"cara_{m}_sonrisa_caido", s, dict(a, tipo="cabeza"), indice)
    if solo in (None, "familia"):
        for estado in ("living", "mesa"):
            s, a = familia(estado); escribir("familia", "familia_" + estado, s, a, indice)
        s, a = chicas_pasan(); escribir("extras", "chicas_pasan", s, a, indice)
    if solo in (None, "props"):
        for k in range(4):
            s, a = prop_telefono(k); escribir("props", "telefono_%d" % k, s, a, indice)
            s, a = prop_cuadernito(k); escribir("props", "cuadernito_%d" % k, s, a, indice)
    ruta = os.path.join(DESTINO, "partes.json")
    previo = {}
    if os.path.exists(ruta):
        with open(ruta) as f:
            previo = json.load(f)
    previo.update(indice)
    with open(ruta, "w") as f:
        json.dump(previo, f, indent=1, ensure_ascii=False)
    print("piezas:", sum(len(v) for v in indice.values()), "->", DESTINO)

if __name__ == "__main__":
    generar(sys.argv[1] if len(sys.argv) > 1 else None)

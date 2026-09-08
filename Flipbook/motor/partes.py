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
           circ(px - r * 0.28, py - r * 0.3, r * 0.2 * brillo, IVORY),
           circ(px + r * 0.18, py + r * 0.22, r * 0.08 * brillo, IVORY)]
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
    ax, ay = 200 + s * 104, 96                   # inserción en la esquina alta del cráneo
    ang = s * (-6 + 10 * caida - 38 * atras)
    d = (f"M {ax} {ay} C {ax + s * 36} {ay + 4}, {ax + s * 58} {ay + 44}, {ax + s * 46} {ay + 94} "
         f"C {ax + s * 40} {ay + 118}, {ax + s * 8} {ay + 116}, {ax - s * 4} {ay + 86} "
         f"C {ax - s * 10} {ay + 56}, {ax - s * 8} {ay + 24}, {ax} {ay} Z")
    pliegue = f"M {ax + s * 8} {ay + 14} C {ax + s * 30} {ay + 30}, {ax + s * 40} {ay + 54}, {ax + s * 36} {ay + 84}"
    return grupo([path(d, fill=UMBER, w=W_SEC), path(pliegue, stroke=DUST, w=3)], f"rotate({ang} {ax} {ay})")

def pipo_cabeza(cara):
    """Devuelve el SVG de la cabeza de Pipo con una de las 6 caras (dict de parámetros)."""
    c = dict(mirada=(0, 0), parpado=(0, 0), parpado_abajo=(0, 0), ojos=(42, 42), brillo=1.0,
             lagrima=False, arrugas="arco", boca="plana", lengua=False, dientes=False,
             orejas=(0.0, 0.0), atras=0.0, tilt=0)
    c.update(cara)
    partes = []
    # cráneo: ancho, con cachetes (jowls) abajo
    craneo = ("M 58 212 C 58 118, 122 64, 200 64 C 278 64, 342 118, 342 212 "
              "C 342 262, 330 300, 300 326 C 268 354, 236 360, 200 360 "
              "C 164 360, 132 354, 100 326 C 70 300, 58 262, 58 212 Z")
    partes.append(path(craneo, fill=FAWN))
    # sombra suave del cachete (línea clara: una sola forma más oscura por lado)
    partes.append(path("M 84 268 C 96 306, 130 332, 172 340", stroke=FAWN_SOMBRA, w=W_SEC + 3))
    partes.append(path("M 316 268 C 304 306, 270 332, 228 340", stroke=FAWN_SOMBRA, w=W_SEC + 3))
    # orejas (detrás del cráneo en la foto, pero pegadas al borde: se dibujan encima del contorno)
    partes.append(pipo_oreja(-1, c["orejas"][0], c["atras"]))
    partes.append(pipo_oreja(1, c["orejas"][1], c["atras"]))
    # máscara negra del hocico: sube en punta entre los ojos, ancha abajo
    mascara = ("M 200 166 C 176 178, 124 210, 116 262 C 110 312, 150 344, 200 344 "
               "C 250 344, 290 312, 284 262 C 276 210, 224 178, 200 166 Z")
    partes.append(path(mascara, fill=UMBER, w=W_SEC))
    # arrugas de la frente = las cejas del pug
    if c["arrugas"] == "arco":          # preocupado / atento: dos arcos altos
        partes.append(path("M 118 150 C 150 118, 250 118, 282 150", w=W_SEC))
        partes.append(path("M 140 128 C 165 106, 235 106, 260 128", stroke=TAUPE, w=W_SEC - 1))
        partes.append(path("M 200 166 C 196 150, 198 138, 204 128", stroke=TAUPE, w=W_SEC - 1))
    elif c["arrugas"] == "v":           # fastidio: las cejas se juntan hacia adentro y abajo
        partes.append(path("M 108 132 C 140 150, 170 160, 190 172", w=W_SEC))
        partes.append(path("M 292 132 C 260 150, 230 160, 210 172", w=W_SEC))
        partes.append(path("M 150 112 C 170 120, 190 128, 200 136", stroke=TAUPE, w=W_SEC - 1))
        partes.append(path("M 250 112 C 230 120, 210 128, 200 136", stroke=TAUPE, w=W_SEC - 1))
    elif c["arrugas"] == "alto":        # resignación: la frente entera se pliega hacia arriba
        partes.append(path("M 112 150 C 150 112, 250 112, 288 150", w=W_SEC))
        partes.append(path("M 130 124 C 160 96, 240 96, 270 124", stroke=TAUPE, w=W_SEC - 1))
        partes.append(path("M 156 102 C 176 86, 224 86, 244 102", stroke=TAUPE, w=W_SEC - 1))
    elif c["arrugas"] == "una":         # sospecha: una ceja arriba y la otra recta
        partes.append(path("M 108 128 C 130 100, 170 104, 186 132", w=W_SEC))
        partes.append(path("M 214 152 C 240 146, 268 148, 290 154", w=W_SEC))
        partes.append(path("M 130 106 C 150 90, 176 92, 190 108", stroke=TAUPE, w=W_SEC - 1))
    elif c["arrugas"] == "suave":       # orgullo / alegría: dos arcos tranquilos
        partes.append(path("M 120 148 C 152 124, 248 124, 280 148", w=W_SEC))
        partes.append(path("M 200 166 C 198 154, 200 144, 204 136", stroke=TAUPE, w=W_SEC - 1))
    # ojos
    partes.append(pipo_ojo(140, 200, c["ojos"][0], c["mirada"], c["parpado"][0], c["parpado_abajo"][0], c["brillo"]))
    partes.append(pipo_ojo(260, 200, c["ojos"][1], c["mirada"], c["parpado"][1], c["parpado_abajo"][1], c["brillo"], lagrima=c["lagrima"]))
    # nariz: un poco más clara que la máscara, con los dos orificios
    partes.append(path("M 176 252 C 176 236, 224 236, 224 252 C 224 270, 208 280, 200 280 C 192 280, 176 270, 176 252 Z", fill=NOSE, stroke="none", w=0))
    partes.append(path("M 188 258 C 184 262, 186 268, 192 266", stroke=DUST, w=3))
    partes.append(path("M 212 258 C 216 262, 214 268, 208 266", stroke=DUST, w=3))
    partes.append(path("M 200 280 L 200 298", stroke=DUST, w=3))
    # boca (líneas claras sobre la máscara negra)
    if c["boca"] == "plana":
        partes.append(path("M 168 306 C 184 300, 216 300, 232 306", stroke=SAND, w=5))
    elif c["boca"] == "caida":
        partes.append(path("M 166 312 C 184 300, 216 300, 234 312", stroke=SAND, w=5))
    elif c["boca"] == "sonrisa":
        partes.append(path("M 156 298 C 176 322, 224 322, 244 298", stroke=SAND, w=5))
    elif c["boca"] == "torcida":        # sonrisa de costado con la lengua afuera
        partes.append(path("M 158 296 C 176 318, 218 326, 248 300", stroke=SAND, w=5))
    elif c["boca"] == "chica":
        partes.append(path("M 186 308 C 194 312, 206 312, 214 308", stroke=SAND, w=5))
    elif c["boca"] == "abierta":        # boca abierta blanda (orgullo)
        partes.append(path("M 168 300 C 180 330, 220 330, 232 300 Z", fill=NOSE, stroke=SAND, w=4))
    if c["lengua"]:
        partes.append(path("M 206 306 C 200 336, 214 372, 244 366 C 268 360, 264 328, 250 306 Z", fill=TONGUE, stroke=UMBER, w=W_SEC))
        partes.append(path("M 230 316 C 232 334, 236 350, 242 360", stroke=UMBER, w=3))
    if c["dientes"]:                    # los dientes de abajo asomando (la foto "Enojado")
        for x in (176, 192, 208, 224):
            partes.append(f'<rect x="{x}" y="{298}" width="12" height="13" rx="3" fill="{IVORY}" stroke="{UMBER}" stroke-width="3"/>')
    # contorno del cráneo otra vez, para que quede limpio arriba de la máscara y los cachetes
    partes.append(path(craneo, fill="none"))
    contenido = grupo(partes, f"rotate({c['tilt']} 200 230)")
    return svg([contenido]), {"cuello": [200, 350], "tilt": c["tilt"]}

CARAS_PIPO = {
    # 1. fastidio ("ay no"): cejas en V, ojos entrecerrados, dientes de abajo (foto Enojado)
    "fastidio": dict(arrugas="v", parpado=(0.28, 0.28), boca="caida", dientes=True, orejas=(0.2, 0.2), brillo=0.8),
    # 2. resignación ("otra vez"): cabeza inclinada, mira arriba, frente plegada (foto Clásica)
    "resignacion": dict(arrugas="alto", mirada=(0.15, -0.75), boca="caida", tilt=-10, orejas=(0.5, 0.3), parpado=(0.12, 0.12)),
    # 3. sospecha (side-eye): ojos al máximo, pupilas de reojo, orejas atrás, una ceja arriba (foto Sorpresa)
    "sospecha": dict(arrugas="una", mirada=(-0.9, 0.05), ojos=(46, 46), boca="chica", atras=0.8, brillo=1.1),
    # 4. ¿en serio?: cabeza ladeada, ojos parejos, una oreja arriba (foto No entender nada)
    "en_serio": dict(arrugas="arco", tilt=22, orejas=(0.0, 0.8), boca="plana", mirada=(0.0, 0.1)),
    # 5. alegría sarcástica ("te lo dije"): ladeada al otro lado, lengua afuera, ojos desparejos (foto Ironía)
    "alegria_sarcastica": dict(arrugas="suave", tilt=-16, ojos=(44, 34), parpado=(0.0, 0.42), parpado_abajo=(0.18, 0.0),
                               boca="torcida", lengua=True, mirada=(0.35, -0.15), orejas=(0.1, 0.6)),
    # 6. orgullo: ojos enormes y brillantes, casi una lágrima, boca abierta blanda
    "orgullo": dict(arrugas="suave", ojos=(46, 46), brillo=1.5, lagrima=True, boca="abierta", mirada=(0.0, -0.2), orejas=(0.4, 0.4)),
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

CUERPOS_PIPO = {
    "sentado": pipo_cuerpo_sentado,
    "camina": pipo_cuerpo_camina,
    "panza_arriba": pipo_cuerpo_panza_arriba,
    "plantado": pipo_cuerpo_plantado,
    "cae": pipo_cuerpo_cae,
}

# =====================================================================================
# TEO · la cabeza (3/4, nunca a cámara) con miradas y bocas; el pelo despeinado
# =====================================================================================

def teo_cabeza(mirada="frente", boca="plana"):
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
    pelo = ("M 112 178 C 104 150, 108 118, 128 100 C 122 84, 138 68, 156 76 "
            "C 158 50, 190 38, 210 56 C 220 34, 256 30, 270 52 C 286 30, 322 40, 322 70 "
            "C 348 74, 358 110, 340 132 C 356 150, 344 178, 322 172 C 330 190, 314 202, 300 188 "
            "C 292 160, 278 140, 260 132 C 236 122, 214 130, 196 136 C 176 128, 148 134, 134 158 "
            "C 128 168, 122 178, 112 178 Z")
    p.append(path(pelo, fill=SAND))
    for d in ("M 156 76 C 164 90, 176 100, 190 104", "M 210 56 C 216 74, 216 92, 208 108",
              "M 270 52 C 268 72, 262 92, 250 108", "M 322 70 C 310 86, 296 100, 280 112",
              "M 340 132 C 326 136, 312 146, 302 160"):
        p.append(path(d, w=W_SEC))
    # anteojos de sol apoyados en el pelo (el prop fijo)
    p.append(path("M 148 118 C 146 100, 172 96, 188 104 L 194 120 C 178 130, 152 132, 148 118 Z", fill=UMBER, w=W_SEC))
    p.append(path("M 212 104 C 230 92, 258 96, 262 114 C 258 130, 232 130, 214 120 Z", fill=UMBER, w=W_SEC))
    p.append(path("M 188 104 C 196 100, 206 100, 212 104", w=W_SEC))
    p.append(path("M 262 108 C 276 104, 286 108, 292 120", w=W_SEC))
    # cejas finas
    p.append(path("M 148 176 C 160 168, 178 168, 190 174", stroke=TAUPE, w=W_SEC - 1))
    p.append(path("M 218 174 C 232 166, 250 166, 262 176", stroke=TAUPE, w=W_SEC - 1))
    # ojos según la mirada (pequeños, de línea; Teo no mira a cámara)
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
    return svg(p), {"cuello": [200, 350]}

MIRADAS_TEO = ["abajo", "frente", "arriba", "costado"]
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
# render
# =====================================================================================

def escribir(personaje, nombre, contenido, anclas, indice):
    carpeta = os.path.join(DESTINO, personaje)
    os.makedirs(carpeta, exist_ok=True)
    ruta_svg = os.path.join(carpeta, nombre + ".svg")
    ruta_png = os.path.join(carpeta, nombre + ".png")
    with open(ruta_svg, "w") as f:
        f.write(contenido)
    subprocess.run(["rsvg-convert", "-w", str(LIENZO * ESCALA_PNG), "-h", str(LIENZO * ESCALA_PNG),
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
                               ("sentado", teo_cuerpo_sentado, dict(encorvado=1.0)), ("sentado_erguido", teo_cuerpo_sentado, dict(encorvado=0.2))):
            s, a = fn(**kw); escribir("teo", "cuerpo_" + nombre, s, dict(a, tipo="cuerpo"), indice)
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

"""La fábrica: un guion en archivo YAML → el mp4 completo, sin tocar código (D1.2 · A+B2+C+E).

    python3 Flipbook/motor/libro.py Flipbook/guiones/vol00_prueba.yaml
    python3 Flipbook/motor/libro.py Flipbook/guiones/vol00_prueba.yaml --solo-cuadros

Salidas: `pruebas/<nombre>.mp4` (1080×1920, 30 fps) y `pruebas/<nombre>_cuadros.png`, la hoja
fija con un cuadro clave de cada cuadro del guion, para revisar sin abrir el video. Los
cuadros sueltos van a `pruebas/frames_<nombre>/` (fuera del repo).

Qué hace este archivo, en orden:
  1. lee el guion (`cargar`) y lo aplana en una lista de CUADROS (beats) de N hojas cada uno;
  2. dibuja cada hoja (`hoja_de`): papel → fondo → secundarios → props → personajes → globo;
  3. le pone el libro encima (`R.chrome`, `R.page_turn`) y emite los frames;
  4. antes va el CARTEL (B2) y después el CIERRE fijo (C: Pipo, iris, tapa, contratapa).

La capa de detalle (Teo, Pipo, teléfono, cuadernito) entra SIEMPRE por `Marioneta`; los
fondos, los props sueltos, los secundarios y el globo son capa simple, programados acá.
El vocabulario del guion está documentado en `REGLAS.md` §7.
"""
import argparse
import copy
import math
import os
import random
import subprocess
import sys

import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R                       # noqa: E402  (helpers de la v1: papel, línea, libro)
from marioneta import Marioneta          # noqa: E402  (la única puerta para poner un personaje)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # Flipbook/
PISO = 1420                              # la línea del piso en una hoja
HOJAS_POR_SEG = R.FPS / R.HOLD           # 10 hojas por segundo (REGLAS §2)

# La cuarta tinta, reservada solo para carteles (REGLAS §3): apagadas, retro, conviven con
# crema, tierra y salvia.
TINTAS = {"ocre": (181, 141, 78), "ladrillo": (164, 92, 71), "azul_cartel": (73, 97, 117)}


# ---------------------------------------------------------------- utilidades chicas

def entre(v, a, b):
    return max(a, min(b, v))


def lerp(a, b, t):
    return a + (b - a) * t


def mezcla(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def font_condensada(tam):
    """La tipografía del cartel: condensada, grande, tipo cartel de los años 30."""
    for p in ("/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf",
              "/System/Library/Fonts/Supplemental/Impact.ttf",
              "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf",
              "/System/Library/Fonts/Avenir Next Condensed.ttc"):
        if os.path.exists(p):
            return ImageFont.truetype(p, tam)
    return R.font(tam, bold=True)         # respaldo: Georgia Bold


def ancho(d, texto, f):
    caja = d.textbbox((0, 0), texto, font=f)
    return caja[2] - caja[0], caja[3] - caja[1]


def font_que_entra(d, texto, ancho_max, tam, condensada=True, minimo=28):
    """Achica la tipografía hasta que el texto entre en `ancho_max`."""
    while tam > minimo:
        f = font_condensada(tam) if condensada else R.font(tam)
        if ancho(d, texto, f)[0] <= ancho_max:
            return f
        tam -= 4
    return font_condensada(minimo) if condensada else R.font(minimo)


# ---------------------------------------------------------------- fondos (capa simple)
# Un fondo es una función (d, rng, desp, capa) → dict de anclas. `desp` es el corrimiento
# del parallax en píxeles (crece cuando alguien camina); `capa` vale "atras" (antes de los
# secundarios) o "delante" (después: la mesa tapa a los que están sentados).

def _piso(d, rng, y=PISO, x0=90, x1=990):
    R.stroke(d, [(x0, y), (x1, y)], rng, width=6, color=R.TAUPE)


def _arbol(d, x, rng, s=1.0, color=None):
    color = color or R.LINE
    R.stroke(d, [(x, PISO - 10), (x, PISO - 170 * s)], rng, width=6, color=color)
    R.circle(d, x, PISO - 225 * s, 70 * s, rng, width=6, color=color)


def _silla(d, x, rng, ancho_s=160, alto=240):
    """Una silla de perfil: respaldo, asiento y dos patas."""
    y = PISO - alto
    R.stroke(d, [(x, y), (x + ancho_s, y)], rng, width=7, color=R.TAUPE)
    R.stroke(d, [(x, y), (x, y - 150)], rng, width=6, color=R.TAUPE)
    R.stroke(d, [(x + 14, y), (x + 14, PISO)], rng, width=6, color=R.TAUPE)
    R.stroke(d, [(x + ancho_s - 14, y), (x + ancho_s - 14, PISO)], rng, width=6, color=R.TAUPE)


def fondo_habitacion(d, rng, desp=0.0, capa="atras"):
    """Piso + ventana."""
    if capa == "atras":
        R.stroke(d, [(650, 470), (960, 470), (960, 860), (650, 860), (650, 470)], rng, width=5, color=R.LINE)
        R.stroke(d, [(805, 470), (805, 860)], rng, width=4, color=R.LINE)
        R.stroke(d, [(650, 665), (960, 665)], rng, width=4, color=R.LINE)
        _piso(d, rng)
    return {"ventana": (805, 665)}


def fondo_rincon(d, rng, desp=0.0, capa="atras"):
    """Piso + banquito + el ángulo de la pared: el rincón donde Teo se esconde."""
    if capa == "atras":
        R.stroke(d, [(150, 620), (150, PISO)], rng, width=5, color=R.LINE)
        R.stroke(d, [(150, PISO), (990, PISO)], rng, width=6, color=R.TAUPE)
        R.stroke(d, [(380, 1180), (700, 1180), (700, PISO)], rng, width=6, color=R.TAUPE)
        R.stroke(d, [(400, 1180), (400, PISO)], rng, width=6, color=R.TAUPE)
    return {"banquito": (540, 1180)}


def fondo_banco_plaza(d, rng, desp=0.0, capa="atras"):
    """Banco + sol salvia + árboles (que hacen parallax si alguien camina)."""
    if capa == "atras":
        R.circle(d, 845, 400, 88, rng, width=8, color=R.SAGE)
        for base in (170, 910):
            _arbol(d, (base - desp * 0.35) % 1500 - 180, rng, s=0.9)
        _piso(d, rng)
        R.stroke(d, [(290, 1180), (770, 1180)], rng, width=8, color=R.TAUPE)
        R.stroke(d, [(320, 1180), (320, PISO)], rng, width=6, color=R.TAUPE)
        R.stroke(d, [(740, 1180), (740, PISO)], rng, width=6, color=R.TAUPE)
        R.stroke(d, [(300, 1090), (760, 1090)], rng, width=6, color=R.TAUPE)
    return {"banco": (530, 1180), "sol": (845, 400)}


def fondo_mesa_familiar(d, rng, desp=0.0, capa="atras"):
    """Mesa con platos + sillas. La mesa va DELANTE: los que están sentados quedan detrás."""
    if capa == "atras":
        _piso(d, rng)
        _silla(d, 250, rng, ancho_s=170, alto=250)
    else:
        R.stroke(d, [(455, 1130), (1010, 1130)], rng, width=8, color=R.TAUPE)
        R.stroke(d, [(510, 1130), (510, PISO)], rng, width=6, color=R.TAUPE)
        R.stroke(d, [(955, 1130), (955, PISO)], rng, width=6, color=R.TAUPE)
        for cx in (610, 770, 900):
            R.circle(d, cx, 1122, 34, rng, width=4, color=R.TAUPE, fill=R.IVORY, ry=10)
    return {"mesa": (730, 1130), "silla": (335, 1170)}


def _sofa(d, rng, dx=0):
    """Un sofá de línea, de frente: respaldo, asiento y dos brazos, corrido dx píxeles."""
    R.stroke(d, [(250 + dx, 1170), (250 + dx, 940), (880 + dx, 940), (880 + dx, 1170)], rng, width=7, color=R.TAUPE)
    R.stroke(d, [(250 + dx, 1170), (880 + dx, 1170)], rng, width=8, color=R.TAUPE)
    R.stroke(d, [(190 + dx, 1330), (190 + dx, 1030)], rng, width=8, color=R.TAUPE)
    R.stroke(d, [(940 + dx, 1330), (940 + dx, 1030)], rng, width=8, color=R.TAUPE)
    R.stroke(d, [(190 + dx, 1030), (250 + dx, 1000)], rng, width=7, color=R.TAUPE)
    R.stroke(d, [(940 + dx, 1030), (880 + dx, 1000)], rng, width=7, color=R.TAUPE)
    R.stroke(d, [(190 + dx, 1330), (940 + dx, 1330)], rng, width=8, color=R.TAUPE)
    R.stroke(d, [(565 + dx, 940), (565 + dx, 1170)], rng, width=4, color=R.LINE)
    for x in (230 + dx, 960 + dx):
        R.stroke(d, [(x, 1330), (x, PISO)], rng, width=6, color=R.TAUPE)


def fondo_sofa(d, rng, desp=0.0, capa="atras"):
    """Un sofá de línea, de frente: respaldo, asiento y dos brazos."""
    if capa == "atras":
        _piso(d, rng)
        _sofa(d, rng)
    return {"sofa": (565, 1170)}


def fondo_living(d, rng, desp=0.0, capa="atras"):
    """El living de la familia (vol. 1): el sofá corrido a la derecha y, a la izquierda, el
    rincón con el banquito y una lámpara de pie. Es el lugar de la escena 2 y del espejo."""
    if capa == "atras":
        R.stroke(d, [(40, 560), (40, PISO)], rng, width=5, color=R.LINE)              # el ángulo de la pared
        _piso(d, rng, x0=40)
        R.stroke(d, [(150, 700), (150, PISO)], rng, width=5, color=R.LINE)            # la lámpara de pie
        R.stroke(d, [(96, 700), (204, 700), (186, 600), (114, 600), (96, 700)], rng, width=5, color=R.LINE)
        R.stroke(d, [(70, 1180), (210, 1180), (210, PISO)], rng, width=6, color=R.TAUPE)   # el banquito
        R.stroke(d, [(90, 1180), (90, PISO)], rng, width=6, color=R.TAUPE)
        _sofa(d, rng, dx=110)
    return {"banquito": (140, 1180), "sofa": (675, 1170)}


def fondo_espejo_bano(d, rng, desp=0.0, capa="atras"):
    """Un espejo ovalado (ancla `espejo`: ahí se pega una cabeza) sobre una repisa."""
    if capa == "atras":
        R.circle(d, 540, 760, 265, rng, width=9, color=R.TAUPE, fill=R.IVORY, ry=345)
        R.circle(d, 540, 760, 240, rng, width=3, color=R.LINE, ry=318)
        R.stroke(d, [(200, 1210), (880, 1210)], rng, width=8, color=R.TAUPE)
        R.stroke(d, [(230, 1210), (230, PISO)], rng, width=6, color=R.TAUPE)
        R.stroke(d, [(850, 1210), (850, PISO)], rng, width=6, color=R.TAUPE)
        _piso(d, rng)
    return {"espejo": (540, 760), "repisa": (540, 1210)}


def fondo_calle(d, rng, desp=0.0, capa="atras"):
    """Piso ondulado + árboles que corren con el parallax."""
    if capa == "atras":
        R.stroke(d, [(k * 40, PISO + 28 * math.sin(k / 6 + desp / 260)) for k in range(0, 28)],
                 rng, width=6, color=R.TAUPE, amp=1.5)
        for base in (1500, 2200, 2900):
            _arbol(d, (base - desp) % 1500 - 200, rng)
    return {"vereda": (540, PISO)}


FONDOS = {"habitacion": fondo_habitacion, "rincon": fondo_rincon, "banco_plaza": fondo_banco_plaza,
          "mesa_familiar": fondo_mesa_familiar, "sofa": fondo_sofa, "living": fondo_living, "espejo_bano": fondo_espejo_bano,
          "calle": fondo_calle, "ninguno": lambda d, rng, desp=0.0, capa="atras": {}}


# ---------------------------------------------------------------- dibujos simples de burbuja
# Lo que Teo ve cuando escribe: el contenido cambia por volumen. Para agregar uno nuevo se
# escribe una función y se la registra en DIBUJOS; el guion lo pide por nombre.

def dibujo_abuelos(d, x, y, rng, s=1.0):
    """Los abuelos: la abuela con rodete, el abuelo con bigote."""
    for cx, abuela in ((x - 72 * s, True), (x + 72 * s, False)):
        R.circle(d, cx, y + 10 * s, 46 * s, rng, width=5, fill=R.CREAM, ry=52 * s)
        if abuela:
            R.circle(d, cx, y - 46 * s, 18 * s, rng, width=5, fill=R.SAND)
        else:
            for k in range(3):
                R.stroke(d, [(cx + (-14 + 14 * k) * s, y - 40 * s), (cx + (-18 + 14 * k) * s, y - 58 * s)],
                         rng, width=4, color=R.TAUPE)
            R.stroke(d, [(cx - 16 * s, y + 22 * s), (cx + 16 * s, y + 22 * s)], rng, width=5, color=R.TAUPE)
        for dx in (-16 * s, 16 * s):
            d.ellipse((cx + dx - 4 * s, y - 4 * s, cx + dx + 4 * s, y + 4 * s), fill=R.UMBER)
        d.line(R.wobble(R.arc_pts(cx, y + 16 * s, 16 * s, 9 * s, 0.15 * math.pi, 0.85 * math.pi, 6), rng, 1),
               fill=R.UMBER, width=4, joint="curve")


def dibujo_familia_riendo(d, x, y, rng, s=1.0):
    """Los tres de la familia riéndose (lo que Teo piensa en la Pausa, vol. 1): papá, la
    hermanita en el medio (más chica) y mamá, de línea simple, con la boca abierta."""
    for cx, cy, r, pelo in ((x - 108 * s, y - 4 * s, 50 * s, "corto"),
                            (x, y + 40 * s, 38 * s, "colitas"),
                            (x + 108 * s, y - 4 * s, 50 * s, "largo")):
        R.circle(d, cx, cy, r, rng, width=5, fill=R.CREAM, ry=r * 1.12)
        if pelo == "corto":
            d.line(R.wobble(R.arc_pts(cx, cy - r * 0.5, r * 1.02, r * 0.72, math.pi, 2 * math.pi, 8), rng, 1.5),
                   fill=R.TAUPE, width=8, joint="curve")
        elif pelo == "largo":
            for lado in (-1, 1):
                d.line(R.wobble(R.arc_pts(cx + lado * r * 0.94, cy + r * 0.22, r * 0.32, r * 0.9,
                                          -0.5 * math.pi, 0.5 * math.pi, 8), rng, 1.2),
                       fill=R.TAUPE, width=9, joint="curve")
            d.line(R.wobble(R.arc_pts(cx, cy - r * 0.5, r * 1.02, r * 0.72, math.pi, 2 * math.pi, 8), rng, 1.5),
                   fill=R.TAUPE, width=8, joint="curve")
            R.circle(d, cx + r * 0.36, cy - r * 0.98, r * 0.24, rng, width=4, color=R.TAUPE, fill=R.SAND)
        else:
            for lado in (-1, 1):
                R.circle(d, cx + lado * r * 1.02, cy - r * 0.24, r * 0.32, rng, width=4, color=R.TAUPE, fill=R.SAND)
            d.line(R.wobble(R.arc_pts(cx, cy - r * 0.46, r * 0.96, r * 0.6, math.pi, 2 * math.pi, 8), rng, 1.5),
                   fill=R.TAUPE, width=7, joint="curve")
        # ojos cerrados de risa (dos arcos) y la boca abierta
        for dx in (-r * 0.38, r * 0.38):
            d.line(R.wobble(R.arc_pts(cx + dx, cy - r * 0.02, r * 0.2, r * 0.16, math.pi, 2 * math.pi, 6), rng, 1),
                   fill=R.UMBER, width=4, joint="curve")
        R.circle(d, cx, cy + r * 0.44, r * 0.34, rng, width=4, color=R.UMBER, fill=R.UMBER, ry=r * 0.26)


def dibujo_corazon(d, x, y, rng, s=1.0):
    """Un corazón de línea: lo que Teo escribe cuando ya entendió (vol. 1)."""
    a, b = 92 * s, 84 * s
    pts = []
    for k in range(65):
        u = math.pi * (1 - 2 * k / 64)
        pts.append((x + a * (16 * math.sin(u) ** 3) / 17.0,
                    y - b * (13 * math.cos(u) - 5 * math.cos(2 * u) - 2 * math.cos(3 * u) - math.cos(4 * u)) / 16.0))
    pts = R.wobble(pts, rng, 2.0)
    d.polygon(pts, fill=R.SAGE_LIGHT)
    d.line(pts + [pts[0]], fill=R.UMBER, width=6, joint="curve")
    d.line(R.wobble(R.arc_pts(x - a * 0.34, y - b * 0.42, a * 0.2, b * 0.16, 0.9 * math.pi, 1.7 * math.pi, 6), rng, 1),
           fill=R.IVORY, width=6, joint="curve")     # el brillito


DIBUJOS = {"abuelos": dibujo_abuelos, "familia_riendo": dibujo_familia_riendo, "corazon": dibujo_corazon}


# ---------------------------------------------------------------- props simples (programados)
# Firma común: (d, x, y, escala, rng, t, **opciones). `t` es 0..1 dentro del cuadro.

def prop_nube_garabatos(d, x, y, escala, rng, t=0.0, disolucion=0.0, **kw):
    """El ruido mental. `disolucion` 0..1: a 1 casi no queda nada y lo que queda subió."""
    dis = entre(disolucion, 0.0, 1.0)
    r = 80 * escala * max(0.06, 1 - dis)
    R.scribble(d, x, y - 70 * dis * escala, rng, r=r, color=R.TAUPE, width=4)


def prop_burbuja_pensamiento(d, x, y, escala, rng, t=0.0, dibujo="abuelos", punta=None, **kw):
    """La burbuja de pensamiento con un dibujo simple adentro (lo que importa del volumen).
    `punta` = de dónde sale (la cabeza de quien piensa); por defecto, justo abajo."""
    punta = tuple(punta) if punta else (x, y + 400)
    for f, r in ((0.28, 14), (0.56, 25)):
        R.circle(d, lerp(punta[0], x, f), lerp(punta[1], y, f), r * escala, rng, width=5, fill=R.IVORY)
    R.circle(d, x, y, 212 * escala, rng, width=6, fill=R.IVORY, ry=152 * escala, amp=3)
    fn = DIBUJOS.get(dibujo)
    if fn:
        fn(d, x, y, rng, s=escala)


def prop_correa(d, x, y, escala, rng, t=0.0, hasta=None, **kw):
    """La correa: una curva floja entre la mano y el collar."""
    hasta = hasta or (x + 240, y + 120)
    mx, my = (x + hasta[0]) / 2, (y + hasta[1]) / 2 + 60 * escala
    R.stroke(d, [(x, y), (mx, my), tuple(hasta)], rng, width=4, color=R.TAUPE)


def prop_plato_croquetas(d, x, y, escala, rng, t=0.0, cuantas=5, **kw):
    """El plato de todos los días, recibido como la mejor fiesta de su vida."""
    R.circle(d, x, y, 86 * escala, rng, width=6, color=R.TAUPE, fill=R.IVORY, ry=26 * escala)
    for k in range(int(cuantas)):
        a = 0.6 + k * 1.15
        R.circle(d, x + 46 * escala * math.cos(a), y - 6 * escala + 12 * escala * math.sin(a),
                 13 * escala, rng, width=4, color=R.TAUPE, fill=R.SAND, ry=10 * escala)


def prop_globo(d, x, y, escala, rng, t=0.0, texto="", hacia=None, **kw):
    """El globo de diálogo suelto (lo normal es pedirlo con `pipo_dice`)."""
    globo(d, texto, hacia or (x, y + 260), rng, forzar=(x, y))


PROPS_SIMPLES = {"nube_garabatos": prop_nube_garabatos, "burbuja_pensamiento": prop_burbuja_pensamiento,
                 "correa": prop_correa, "plato_croquetas": prop_plato_croquetas, "globo": prop_globo}


# ---------------------------------------------------------------- secundarios de línea

def secundario(d, x, y, rng, tipo="abuela", escala=1.9):
    """Un secundario de línea simple a la escala del personaje: cabeza + cuerpo + brazos.
    Tipos: abuela · abuelo · chica · senor. Son capa simple a propósito (REGLAS §1: el
    contraste con la capa ilustrada es lo que hace que Teo y Pipo se vean)."""
    s = escala
    R.circle(d, x, y, 44 * s, rng, width=6, color=R.TAUPE, fill=R.CREAM, ry=50 * s)
    if tipo == "abuela":
        R.circle(d, x, y - 50 * s, 18 * s, rng, width=5, color=R.TAUPE, fill=R.SAND)
    elif tipo == "abuelo":
        for k in range(3):
            R.stroke(d, [(x + (-14 + 14 * k) * s, y - 40 * s), (x + (-18 + 14 * k) * s, y - 60 * s)],
                     rng, width=4, color=R.TAUPE)
        R.stroke(d, [(x - 16 * s, y + 14 * s), (x + 16 * s, y + 14 * s)], rng, width=6, color=R.TAUPE)
    elif tipo == "chica":
        for lado in (-1, 1):
            d.line(R.wobble(R.arc_pts(x + lado * 34 * s, y - 6 * s, 26 * s, 62 * s,
                                      -0.55 * math.pi, 0.5 * math.pi, 8), rng, 1.5),
                   fill=R.TAUPE, width=int(7 * s / 1.9) + 4, joint="curve")
        d.line(R.wobble(R.arc_pts(x, y - 42 * s, 42 * s, 22 * s, math.pi, 2 * math.pi, 8), rng, 1.5),
               fill=R.TAUPE, width=7, joint="curve")
    else:                                   # senor
        d.line(R.wobble(R.arc_pts(x, y - 34 * s, 44 * s, 26 * s, math.pi, 2 * math.pi, 8), rng, 1.5),
               fill=R.TAUPE, width=8, joint="curve")
        R.stroke(d, [(x - 44 * s, y - 34 * s), (x + 44 * s, y - 34 * s)], rng, width=6, color=R.TAUPE)
    for dx in (-15 * s, 15 * s):
        d.ellipse((x + dx - 5, y - 10, x + dx + 5, y), fill=R.UMBER)
    d.line(R.wobble(R.arc_pts(x, y + 6 * s, 16 * s, 9 * s, 0.15 * math.pi, 0.85 * math.pi, 6), rng, 1),
           fill=R.UMBER, width=5, joint="curve")
    R.stroke(d, [(x, y + 50 * s), (x, y + 120 * s)], rng, width=8, color=R.TAUPE)
    R.stroke(d, [(x, y + 70 * s), (x - 60 * s, y + 105 * s)], rng, width=7, color=R.TAUPE)
    R.stroke(d, [(x, y + 70 * s), (x + 50 * s, y + 105 * s)], rng, width=7, color=R.TAUPE)


# ---------------------------------------------------------------- el globo de Pipo
# La voz de Pipo NO va suelta en la hoja: Pipo rompe la cuarta pared y le habla a la
# audiencia desde un globo de historieta, con la colita apuntando a su cabeza (WS33).

ANCHO_GLOBO = 330            # ancho máximo de una línea adentro del globo, en píxeles
MAX_LINEAS_GLOBO = 4         # hasta 12 palabras en 3-4 líneas cortas (WS34, el tempo)
GLOBO_DESDE = 5              # hojas que la imagen está SOLA antes de que aparezca el globo (0,5 s)
MODO_GLOBO = ["abajo"]       # abajo (WS35, Tomás: el globo vive en el tercio vacío de abajo y no tapa la escena) | arriba
SUBE_ESCENA = [0]            # píxeles que la escena entera sube (WS35): TikTok tapa la franja de abajo con la
                             # descripción y el usuario; con la escena más arriba, el globo de abajo queda en zona segura
# La vida del cuadro (WS34): cabeceo automático de la cabeza, (grados, radianes por hoja).
# Pipo cabecea rápido y visible; Teo apenas, lento. `vida: false` en el personaje lo apaga.
# WS36: el cabeceo sube (era 4,0/1,5). A escala de teléfono el movimiento chico no se ve;
# `vida: 0` lo apaga en un cuadro y `vida: 1.8` lo exagera.
VIDA = {"pipo": (5.5, 0.72), "teo": (3.0, 0.5)}


def _envolver(d, texto, f, ancho_max):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if actual and ancho(d, prueba, f)[0] > ancho_max:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    return lineas


ANCHO_GLOBO_ABAJO = 600      # el globo de abajo va APAISADO (2-3 líneas): en la franja de abajo hay ancho, no alto
MAX_LINEAS_ABAJO = 3


def _texto_globo(d, texto, tam=52, minimo=38, ancho=None, max_lineas=None):
    """Georgia, minúsculas. Arriba: hasta 4 líneas cortas (un globo alto). Abajo: hasta 3
    líneas anchas (un globo apaisado que no sube hasta la escena)."""
    ancho = ancho or ANCHO_GLOBO
    max_lineas = max_lineas or MAX_LINEAS_GLOBO
    while True:
        f = R.font(tam)
        lineas = _envolver(d, texto, f, ancho)
        if len(lineas) <= max_lineas or tam <= minimo:
            return f, lineas, tam
        tam -= 4


def _colita(cx, cy, rx, ry, ax, ay):
    """Los tres puntos de la colita del globo: las dos bases sobre el óvalo y la punta."""
    a = math.atan2(ay - cy, ax - cx)
    b1 = (cx + rx * math.cos(a - 0.30), cy + ry * math.sin(a - 0.30))
    b2 = (cx + rx * math.cos(a + 0.30), cy + ry * math.sin(a + 0.30))
    base = (cx + rx * math.cos(a), cy + ry * math.sin(a))
    punta = (lerp(base[0], ax, 0.80), lerp(base[1], ay, 0.80))
    return b1, b2, base, punta


def globo(d, texto, ancla, rng, evitar=(), forzar=None, flota=0.0, modo=None, ancla_abajo=None):
    """Dibuja el globo de Pipo. `ancla` = (x, y) de su cabeza: de ahí sale la colita.
    `evitar` = cajas (x0, y0, x1, y1) que ni el globo ni la colita pueden tapar (las caras
    y la burbuja de pensamiento). Se prueban posiciones cerca de Pipo y se elige la primera
    que no tape nada; si ninguna limpia, la menos mala. `flota` = píxeles que el globo sube o
    baja en esta hoja (la vida del cuadro)."""
    if not texto:
        return
    modo = modo or MODO_GLOBO[0]
    if modo == "abajo":
        f, lineas, tam = _texto_globo(d, texto, ancho=ANCHO_GLOBO_ABAJO, max_lineas=MAX_LINEAS_ABAJO)
    else:
        f, lineas, tam = _texto_globo(d, texto)
    tw = max(ancho(d, s, f)[0] for s in lineas)
    th = len(lineas) * int(tam * 1.28)
    if modo == "abajo":                              # caja redondeada apaisada, con aire alrededor del texto
        rx, ry = tw / 2 + 60, th / 2 + 44
    else:                                            # óvalo de historieta
        rx, ry = tw * 0.70 + 40, th * 0.86 + 38

    ax, ay = ancla
    # la cabeza de la que sale la colita no cuenta como obstáculo de la colita
    cabeza = [c for c in evitar if (c[0] - 30 < ax < c[2] + 30 and c[1] - 30 < ay < c[3] + 30)]
    esquivar_colita = [c for c in evitar if c not in cabeza]
    if forzar:
        cx, cy = forzar
    else:
        arriba = [(ax, ay - ry - 80), (ax - rx - 130, ay - 30), (ax + rx + 130, ay - 30),
                  (ax - rx - 90, ay - ry - 130), (ax + rx + 90, ay - ry - 130),
                  (ax, ay - ry - 330), (ax - 320, ay - ry - 380), (ax + 320, ay - ry - 380),
                  (R.W / 2, 340), (rx + 60, 340), (R.W - rx - 60, 340)]
        mx, my = ancla_abajo or ancla
        # 130 px de colita entre el piso y la caja; si Pipo cuelga por debajo del piso (panza
        # arriba), la caja baja para que la colita mida al menos 110 px
        yb = min(max(PISO - int(SUBE_ESCENA[0]) + ry + 130, my + ry + 110), R.H - ry - 180)
        abajo = [(mx, yb, (mx, my)), (R.W / 2, yb, (mx, my)), (rx + 70, yb, (mx, my)), (R.W - rx - 110, yb, (mx, my)),
                 (mx - 260, yb, (mx, my)), (mx + 260, yb, (mx, my))]
        arriba = [(px, py, (ax, ay)) for px, py in arriba]
        candidatos = (abajo + arriba) if modo == "abajo" else (arriba + abajo)
        mejor, puntaje_mejor = None, None
        for k, (px, py, (ax, ay)) in enumerate(candidatos):
            px = entre(px, rx + 55, R.W - rx - 55)
            py = entre(py, ry + 150, R.H - ry - 180)
            caja = (px - rx, py - ry, px + rx, py + ry)
            if py > ay:
                b1, b2, base, punta = _colita_caja(px, py, rx, ry, ax, ay)[:4]
            else:
                b1, b2, base, punta = _colita(px, py, rx, ry, ax, ay)
            puntaje = 4.0 * sum(_solape(caja, c) for c in evitar)
            puntaje += 9.0 * sum(1 for c in esquivar_colita
                                 if _cruza(base, punta, c) or _cruza(b1, punta, c) or _cruza(b2, punta, c))
            puntaje += math.hypot(px - ax, py - ay) / 340.0 + k * 0.05
            if modo == "abajo":                       # los globos viven abajo: no tapan la escena
                puntaje += max(0.0, yb - py) / 250.0
            else:                                     # los globos viven arriba, como en la historieta
                puntaje += max(0.0, py - 650) / 250.0
            if puntaje_mejor is None or puntaje < puntaje_mejor:
                mejor, puntaje_mejor = (px, py, ax, ay), puntaje
        cx, cy, ax, ay = mejor
    cy += flota

    if modo == "abajo" and cy > ay:
        _caja_globo(d, cx, cy, rx, ry, rng, ax, ay)          # caja + colita integradas
    else:
        R.circle(d, cx, cy, rx, rng, width=6, fill=R.IVORY, ry=ry, amp=2.5)
        b1, b2, _, punta = _colita(cx, cy, rx, ry, ax, ay)
        d.polygon([b1, punta, b2, (cx, cy)], fill=R.IVORY)  # el relleno tapa el borde del óvalo
        R.stroke(d, [b1, punta], rng, width=6, amp=1.2)
        R.stroke(d, [b2, punta], rng, width=6, amp=1.2)
    for k, s in enumerate(lineas):
        d.text((cx, cy - th / 2 + int(tam * 1.28) * (k + 0.5)), s, fill=R.UMBER, font=f, anchor="mm")


RADIO_CAJA = 56
BASE_COLITA = 34             # media base de la colita de la caja (68 px de ancho en el borde)


def _bezier(p0, p1, p2, n=14):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]) for t in (k / n for k in range(n + 1))]


def _colita_caja(cx, cy, rx, ry, ax, ay):
    """La colita del globo de abajo: nace en el BORDE SUPERIOR de la caja, con una base
    angosta, y sube al mentón de Pipo en dos curvas que primero suben derechas y después se
    cierran en la punta (colita de historieta). Devuelve (b1, b2, base, punta, curva1, curva2)."""
    bx = entre(ax, cx - rx + RADIO_CAJA + BASE_COLITA, cx + rx - RADIO_CAJA - BASE_COLITA)
    by = cy - ry
    b1, b2 = (bx - BASE_COLITA, by), (bx + BASE_COLITA, by)
    punta = (ax, ay)
    alto = max(40.0, by - ay)
    c1 = (b1[0] + (ax - b1[0]) * 0.18, by - alto * 0.62)
    c2 = (b2[0] + (ax - b2[0]) * 0.18, by - alto * 0.62)
    return b1, b2, (bx, by), punta, _bezier(b1, c1, punta), _bezier(b2, c2, punta)


def _caja_globo(d, cx, cy, rx, ry, rng, ax, ay, radio=RADIO_CAJA):
    """El globo apaisado de abajo: un rectángulo redondeado de línea temblorosa, con la
    colita integrada al borde (el contorno se abre en la base de la colita)."""
    b1, b2, base, punta, curva1, curva2 = _colita_caja(cx, cy, rx, ry, ax, ay)
    # el contorno arranca en b2 (derecha de la base), da la vuelta y termina en b1
    pts = [b2]
    esquinas = [(cx + rx - radio, cy - ry + radio, -0.5), (cx + rx - radio, cy + ry - radio, 0.0),
                (cx - rx + radio, cy + ry - radio, 0.5), (cx - rx + radio, cy - ry + radio, 1.0)]
    for ex, ey, a0 in esquinas:
        for k in range(7):
            a = (a0 + 0.5 * k / 6) * math.pi
            pts.append((ex + radio * math.cos(a), ey + radio * math.sin(a)))
    pts.append(b1)
    pts = R.wobble(pts, rng, 1.8)
    # relleno: la caja y la colita, como una sola forma marfil
    d.polygon(pts, fill=R.IVORY)
    d.polygon(curva1 + curva2[::-1], fill=R.IVORY)
    # contorno de la caja (abierto en la base) y las dos curvas de la colita, más finas
    d.line(pts, fill=R.UMBER, width=6, joint="curve")
    d.line(R.wobble(curva1, rng, 1.0), fill=R.UMBER, width=5, joint="curve")
    d.line(R.wobble(curva2, rng, 1.0), fill=R.UMBER, width=5, joint="curve")


def _solape(a, b):
    w = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return w * h / 10000.0


def _cruza(p0, p1, caja):
    """¿El segmento (la colita) pasa por adentro de la caja? Se mide muestreándolo."""
    for k in range(1, 21):
        x, y = lerp(p0[0], p1[0], k / 20), lerp(p0[1], p1[1], k / 20)
        if caja[0] < x < caja[2] and caja[1] < y < caja[3]:
            return True
    return False


# ---------------------------------------------------------------- personajes

_CAJAS = {}


def caja_pieza(m, personaje, pieza):
    """La caja real de una pieza (la silueta del PNG) en unidades de lienzo, relativa a su
    pivote. Sirve para saber DÓNDE está la cara y no taparla con un globo."""
    clave = (personaje, pieza)
    if clave not in _CAJAS:
        a = m.anclas(personaje, pieza)
        with Image.open(os.path.join(RAIZ, a["png"])) as im:
            b = im.convert("RGBA").split()[3].getbbox()
        k = a["escala_png"]
        pvx, pvy = a.get("cuello") or a.get("centro") or (200, 200)
        _CAJAS[clave] = (b[0] / k - pvx, b[1] / k - pvy, b[2] / k - pvx, b[3] / k - pvy)
    return _CAJAS[clave]


def _caja_cabeza(m, personaje, cuerpo, cara, punto, escala, rot=0.0, espejo=False):
    """La caja de la cabeza EN LA HOJA, con la misma rotación y el mismo espejo que le aplica
    `Marioneta.pegar` (si no, en poses giradas como `panza_arriba` la cara queda en otro lado
    y el globo apunta a la nada)."""
    ac = m.anclas(personaje, "cuerpo_" + cuerpo)
    s = escala * ac["escala"]
    a = math.radians(rot + (-ac["rot"] if espejo else ac["rot"]))
    x0, y0, x1, y1 = caja_pieza(m, personaje, cara)
    xs, ys = [], []
    for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        qx = px * math.cos(a) - py * math.sin(a)
        qy = px * math.sin(a) + py * math.cos(a)
        xs.append(-qx if espejo else qx)
        ys.append(qy)
    ax, ay = punto
    return (ax + min(xs) * s, ay + min(ys) * s, ax + max(xs) * s, ay + max(ys) * s)


def _ancla_hoja(m, personaje, cuerpo, nombre, x, y, escala):
    a = m.anclas(personaje, "cuerpo_" + cuerpo)[nombre]
    return x + (a[0] - 200) * escala, y + (a[1] - 200) * escala


def _alterna(v, i, ritmo, fase=0):
    """Una lista en el guion = poses (o caras) que ALTERNAN dentro del mismo cuadro, cada
    `ritmo` hojas. WS36: la escena se mueve aunque el personaje no se desplace."""
    return v[(i // max(1, int(ritmo)) + int(fase)) % len(v)]


def _cuerpo_de(spec, i):
    """`ciclo: true` convierte `camina` en camina_0..3, una fase por hoja. Una LISTA de
    cuerpos alterna entre ellos cada `ritmo` hojas (3 por defecto, 0,3 s)."""
    cuerpo = spec["cuerpo"]
    if isinstance(cuerpo, list):
        return _alterna(cuerpo, i, spec.get("ritmo", 3), spec.get("fase", 0))
    if spec.get("ciclo"):
        cuerpo = "%s_%d" % (cuerpo, (i + int(spec.get("fase", 0))) % 4)
    return cuerpo


def _cara_de(spec, i):
    """Igual que el cuerpo: una lista de caras alterna dentro del cuadro."""
    cara = spec.get("cara", "frente_plana")
    if isinstance(cara, list):
        return _alterna(cara, i, spec.get("ritmo_cara", spec.get("ritmo", 3)), spec.get("fase_cara", 0))
    return cara


def _num(spec, clave, defecto, t):
    """Un número del guion, interpolado dentro del cuadro si hay `hacia_<clave>` (WS36):
    `escala` + `hacia_escala` = el personaje se acerca; `rot` + `hacia_rot` = se inclina."""
    v = float(spec.get(clave, defecto) or 0)
    h = spec.get("hacia_" + clave)
    return lerp(v, float(h), t) if h is not None else v


def _sacudida(spec, i):
    """`sacude: <px>` = vibración corta y nerviosa (el remate de un chiste)."""
    a = float(spec.get("sacude", 0) or 0)
    if not a:
        return 0.0, 0.0
    return a * math.sin(i * 2.6), a * 0.6 * math.cos(i * 3.1)


# --- la cámara (WS36) -------------------------------------------------------------------
# El vol. 1 se publicó con la escena CONGELADA: el papel pasaba, pero adentro no se movía
# nada (Tomás, 09/09). En el feed eso se lee como una lámina, no como un video. La cámara es
# el movimiento más barato y el que más rinde: sirve en CUALQUIER cuadro, sin dibujar nada.

def _camara(spec, t):
    """(zoom, dx, dy) en el instante `t` del cuadro. `empuje` / `retroceso` son atajos."""
    if not spec:
        return 1.0, 0.0, 0.0
    if isinstance(spec, str):
        spec = {"empuje": {"hasta": 1.12}, "empuje_fuerte": {"hasta": 1.28},
                "retroceso": {"desde": 1.12, "hasta": 1.0}}.get(spec, {})
    desde = max(1.0, float(spec.get("desde", 1.0)))
    hasta = max(1.0, float(spec.get("hasta", spec.get("zoom", desde))))
    e = t * t * (3 - 2 * t)                       # suavizado: arranca y termina sin tirón
    return lerp(desde, hasta, e), lerp(0.0, float(spec.get("x", 0)), e), lerp(0.0, float(spec.get("y", 0)), e)


def _aplicar_camara(lienzo, caras, z, dx, dy):
    """Recorta y agranda la ESCENA (el globo y el libro no se mueven con la cámara)."""
    if z <= 1.001 and not dx and not dy:
        return lienzo, caras
    w, h = lienzo.size
    grande = lienzo.resize((max(w, int(w * z)), max(h, int(h * z))), Image.LANCZOS)
    ox = entre((grande.width - w) / 2 - dx, 0, grande.width - w)
    oy = entre((grande.height - h) / 2 - dy, 0, grande.height - h)
    recorte = grande.crop((int(ox), int(oy), int(ox) + w, int(oy) + h))
    mover = lambda x, y: (x * z - ox, y * z - oy)                                  # noqa: E731
    return recorte, [mover(c[0], c[1]) + mover(c[2], c[3]) for c in caras]


def _valor(v, t):
    """Un número, o "sube"/"baja" para una rampa dentro del cuadro."""
    if isinstance(v, str):
        return entre(t * 1.6 - 0.15, 0, 1) if v == "sube" else entre(1.2 - t * 1.6, 0, 1)
    return float(v or 0)


def pegar_personaje(m, im, d, personaje, spec, i, n, t, rng, anclas_fondo):
    """Pega un personaje con su prop en la mano. Devuelve (punto de cuello, caja de cara)."""
    cuerpo = _cuerpo_de(spec, i)
    cara = _cara_de(spec, i)
    x, y = _posicion(spec, anclas_fondo, t)
    sx, sy = _sacudida(spec, i)
    x, y = x + sx, y + sy
    escala = _num(spec, "escala", 1.0, t)
    aura = _valor(spec.get("aura", 0), t)
    pulso = (0.5 + 0.5 * math.sin(i * 0.55)) if spec.get("pulso", aura > 0) else 0.0
    espejo = bool(spec.get("espejo", False))
    rot = _num(spec, "rot", 0, t)
    cara_pieza = cara if cara.startswith("cara_") else "cara_" + cara
    amp, vel = VIDA.get(personaje, (0.0, 0.0))
    fase = 0.0 if personaje == "pipo" else 1.3
    vida = spec.get("vida", True)
    amp *= float(vida) if not isinstance(vida, bool) else 1.0
    rot_cabeza = amp * math.sin(i * vel + fase) if vida else 0.0
    punto = m.pegar(im, personaje, cuerpo, cara, x, y, escala=escala, rng=rng,
                    rot=rot, espejo=espejo, aura=aura, pulso=pulso, rot_cabeza=rot_cabeza)
    cajas = []
    for p in _lista(spec.get("prop")):
        cajas.append(_prop_en_mano(m, im, personaje, cuerpo, p, x, y, escala, rng, i))
    cajas.append(_caja_cabeza(m, personaje, cuerpo, cara_pieza, punto, escala, rot, espejo))
    return punto, cajas


COLORES_BRILLO = {"salvia": (R.SAGE_LIGHT, R.SAGE, R.SAGE_DEEP),
                  "blanco": ((255, 255, 255), (255, 252, 244), (236, 226, 206))}


def _resplandor(im, cx, cy, r, fuerza=1.0, rng=None, color="salvia"):
    """El resplandor salvia detrás de una pieza chica (el teléfono que se enciende en la
    mano, WS35): un halo difuminado + rayitos de línea. Sin esto, a la escala de la mano el
    verde no se lee."""
    claro, medio, linea = COLORES_BRILLO.get(color, COLORES_BRILLO["salvia"])
    capa = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(capa)
    for k, (rr, op) in enumerate(((r * 2.1, 46), (r * 1.55, 70), (r * 1.1, 98))):
        col = claro if k == 0 else medio
        dd.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=col + (int(op * fuerza),))
    capa = capa.filter(ImageFilter.GaussianBlur(r * 0.5))
    im.paste(capa, (0, 0), capa)
    if rng is not None:                     # los rayitos: ocho trazos cortos alrededor
        d2 = ImageDraw.Draw(im)
        for k in range(6):
            a = k * math.pi / 3 + 0.35
            p0 = (cx + math.cos(a) * r * 1.15, cy + math.sin(a) * r * 1.15)
            p1 = (cx + math.cos(a) * r * 1.5, cy + math.sin(a) * r * 1.5)
            R.stroke(d2, [p0, p1], rng, width=max(3, int(r * 0.06)), color=linea, amp=0.8)


def _prop_en_mano(m, im, personaje, cuerpo, spec, x, y, escala, rng, i):
    """Una pieza ilustrada de utilería, colgada de un ancla del cuerpo, con su escala_rel.
    `brillo: 0..1` le pone detrás el resplandor salvia (el teléfono que se enciende)."""
    if isinstance(spec, str):
        spec = {"nombre": spec}
    nombre = spec["nombre"]
    ciclo = spec.get("ciclo")
    if ciclo:
        nombre = ciclo[i % len(ciclo)]
    a = m.anclas(personaje, "cuerpo_" + cuerpo)
    nombre_ancla = spec.get("ancla") or next((k for k in ("manos", "mano", "pecho") if k in a), None)
    if nombre_ancla:
        ax, ay = _ancla_hoja(m, personaje, cuerpo, nombre_ancla, x, y, escala)
    else:
        ax, ay = x, y
    rel = m.anclas("props", nombre)["escala_rel"]
    esc = escala * rel * float(spec.get("escala", 1.0))
    px, py = ax + float(spec.get("dx", 0)), ay + float(spec.get("dy", 0))
    brillo = float(spec.get("brillo", 0) or 0)
    if brillo:                       # el resplandor va DEBAJO de la pieza
        pulso = 0.72 + 0.28 * math.sin(i * 0.5)
        _resplandor(im, px, py, 200 * esc, brillo * pulso, rng=rng, color=spec.get("brillo_color", "salvia"))
    m.solo(im, "props", nombre, px, py, escala=esc, rng=rng, rot=float(spec.get("rot", 0)))
    x0, y0, x1, y1 = caja_pieza(m, "props", nombre)                 # el objeto que sostiene
    return (px + x0 * esc, py + y0 * esc, px + x1 * esc, py + y1 * esc)   # tampoco se tapa


def _lista(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _posicion(spec, anclas_fondo, t):
    """x/y del guion, o `en: <ancla del fondo>`, interpolados hacia `hacia:` dentro del cuadro."""
    if spec.get("en") and spec["en"] in anclas_fondo:
        bx, by = anclas_fondo[spec["en"]]
    else:
        bx, by = float(spec.get("x", R.W / 2)), float(spec.get("y", 1200))
    bx += float(spec.get("dx", 0)) if spec.get("en") else 0
    by += float(spec.get("dy", 0)) if spec.get("en") else 0
    h = spec.get("hacia")
    if h:
        bx = lerp(bx, float(h.get("x", bx)), t)
        by = lerp(by, float(h.get("y", by)), t)
    return bx, by


# ---------------------------------------------------------------- una hoja

# Regla de caras (WS34): problema = sospecha → fastidio · espejo y magia = orgullo (alegría) ·
# en_serio (duda) solo para "algo se enciende" · alegria_sarcastica (pícaro) solo en el iris.
CARAS_ASOMA = {"problema": "fastidio", "espejo": "orgullo", "magia": "orgullo", "cartel": "alegria_sarcastica"}


def hoja_de(m, cuadro, i, n, rng, desp=0.0):
    """Dibuja UNA hoja del cuadro (beat) `cuadro`, hoja número `i` de `n`."""
    im = R.paper(rng)
    sube = int(SUBE_ESCENA[0])
    t = i / max(1, n - 1)
    cam = _camara(cuadro.get("camara"), t)
    # la escena se dibuja sobre un papel OPACO (no una capa transparente: el aura y los bordes
    # antialiasados se oscurecen al componer sobre alfa cero) y se pega corrida hacia arriba.
    # También va aparte cuando hay cámara: el zoom es de la ESCENA, no del globo ni del libro.
    aparte = bool(sube) or cam[0] > 1.001 or bool(cam[1]) or bool(cam[2])
    lienzo = R.paper(random.Random(rng.randint(0, 10 ** 6))) if aparte else im
    d = ImageDraw.Draw(lienzo)
    caras = []
    anclas_fondo = {}
    ancla_pipo = None
    ancla_menton = None

    if cuadro.get("zoom"):
        caras += _zoom(m, lienzo, d, cuadro["zoom"], i, n, t, rng)
    else:
        fn = FONDOS.get(cuadro.get("fondo", "ninguno"), FONDOS["ninguno"])
        anclas_fondo = fn(d, rng, desp, "atras") or {}
        for sec in _lista(cuadro.get("secundarios")):
            sx, sy = _posicion(sec, anclas_fondo, t)
            se = float(sec.get("escala", 1.9))
            secundario(d, sx, sy, rng, tipo=sec.get("tipo", "abuela"), escala=se)
            caras.append((sx - 48 * se, sy - 58 * se, sx + 48 * se, sy + 56 * se))
        for pz in _lista(cuadro.get("piezas")):
            pz = dict(pz, _i=i)                       # la hoja, para `alterna` y `sacude`
            caras.append(_pieza_suelta(m, lienzo, pz, anclas_fondo, t, rng))
        fn(d, rng, desp, "delante")
        caras += _props_sueltos(d, cuadro, anclas_fondo, t, rng, delante=False)
        for quien in ("teo", "pipo"):
            spec = cuadro.get(quien)
            if not spec:
                continue
            punto, cajas = pegar_personaje(m, lienzo, d, quien, spec, i, n, t, rng, anclas_fondo)
            caras += cajas
            if quien == "pipo":
                caja = cajas[-1]                       # la última es la cabeza
                ancla_pipo = ((caja[0] + caja[2]) / 2, caja[1] + 0.25 * (caja[3] - caja[1]))
                # la colita de abajo apunta a Pipo desde DEBAJO de su silueta entera (cabeza o
                # cuerpo, lo que llegue más abajo), sin tocarlo
                px_, py_ = _posicion(spec, anclas_fondo, t)
                cb = caja_pieza(m, "pipo", "cuerpo_" + _cuerpo_de(spec, i))
                fondo_cuerpo = py_ + cb[3] * float(spec.get("escala", 1.0))
                ancla_menton = ((caja[0] + caja[2]) / 2, max(caja[3], fondo_cuerpo) + 14)
        caras += _props_sueltos(d, cuadro, anclas_fondo, t, rng, delante=True)

    if cuadro.get("anillos"):                        # la respiración de la escena de la magia
        _anillos(d, m, cuadro, i, rng)

    if aparte:                       # la cámara mueve la escena; después sube; cajas y anclas la siguen
        n_caras = len(caras)
        extra = [(p[0], p[1], p[0], p[1]) for p in (ancla_pipo, ancla_menton) if p]
        lienzo, todo = _aplicar_camara(lienzo, caras + extra, *cam)
        caras, resto = todo[:n_caras], list(todo[n_caras:])
        if ancla_pipo:
            ancla_pipo = (resto.pop(0)[:2])
        if ancla_menton:
            ancla_menton = (resto.pop(0)[:2])
        im.paste(lienzo, (0, -sube))
        d = ImageDraw.Draw(im)
        caras = [(c[0], c[1] - sube, c[2], c[3] - sube) for c in caras]
        if ancla_pipo:
            ancla_pipo = (ancla_pipo[0], ancla_pipo[1] - sube)
        if ancla_menton:
            ancla_menton = (ancla_menton[0], ancla_menton[1] - sube)

    g = globo_en(cuadro, i, n)
    if g:
        if ancla_pipo is None:                       # Pipo no está en el cuadro: asoma por un borde
            ancla_pipo, caja = _pipo_asoma(m, im, cuadro, rng, cara=g.get("cara"))
            caras.append(caja)
        globo(d, g["texto"], ancla_pipo, rng, evitar=caras, flota=5.0 * math.sin(i * 0.5),
              modo=g.get("lado", cuadro.get("globo_lado")), ancla_abajo=ancla_menton)

    f = cuadro.get("flash")                          # WS36: el fogonazo (el flash de una foto)
    if f:
        f = f if isinstance(f, dict) else {}
        desde, cada, dura = int(f.get("desde", 3)), max(1, int(f.get("cada", 8))), max(1, int(f.get("dura", 1)))
        if i >= desde and (i - desde) % cada < dura:
            im = Image.blend(im, Image.new("RGB", im.size, (255, 255, 255)), float(f.get("fuerza", 0.8)))
    return im


def globos_de(cuadro):
    """`pipo_dice` es un texto, una lista de textos (varios globos sobre la misma imagen), o
    una lista de mapas `{texto, desde, hasta, cara}` (WS36): así un globo tiene VENTANA
    propia y Pipo **entra y se va de escena** en el medio del cuadro, con la cara que le toca."""
    fuera = []
    for t in _lista(cuadro.get("pipo_dice")):
        g = t if isinstance(t, dict) else {"texto": t}
        if str(g.get("texto", "")).strip():
            fuera.append(dict(g, texto=str(g["texto"])))
    return fuera


def globo_en(cuadro, i, n):
    """Qué globo se ve en la hoja `i` de `n`. Con `desde`/`hasta` manda la ventana (y entre
    ventanas NO hay globo: Pipo desaparece). Sin ellos, el reparto parejo de la WS34: la
    imagen está sola `globo_desde` hojas y después los globos se reparten el resto."""
    globos = globos_de(cuadro)
    if not globos:
        return None
    if any("desde" in g or "hasta" in g for g in globos):
        for g in globos:
            if int(g.get("desde", 0)) <= i < int(g.get("hasta", n)):
                return g
        return None
    desde = int(cuadro.get("globo_desde", GLOBO_DESDE))
    if i < desde:
        return None
    tramo = max(1.0, (n - desde) / len(globos))
    return globos[min(len(globos) - 1, int((i - desde) / tramo))]


def _pieza_suelta(m, im, spec, anclas_fondo, t, rng):
    """Una pieza ilustrada compuesta (la familia del vol. 1) pegada por su ancla `centro`:
    `pieza: familia/familia_living`, `x`, `y`, `escala`, `rot`, `espejo`. Devuelve la caja
    real (del alfa) para que el globo no la tape."""
    personaje, nombre = spec["pieza"].split("/")
    if isinstance(spec.get("pieza"), str) and isinstance(spec.get("alterna"), list):
        personaje, nombre = _alterna(spec["alterna"], int(spec.get("_i", 0)), spec.get("ritmo", 3)).split("/")
    x, y = _posicion(spec, anclas_fondo, t)
    sx, sy = _sacudida(spec, int(spec.get("_i", 0)))
    x, y = x + sx, y + sy
    escala = _num(spec, "escala", 1.0, t)
    a = m.anclas(personaje, nombre)
    pivote = tuple(a.get("centro", [200, 200]))
    brillo = _valor(spec.get("brillo", 0), t)        # WS36: una pieza suelta también se enciende
    if brillo:
        i_h = int(spec.get("_i", 0))
        _resplandor(im, x, y, 210 * escala, brillo * (0.72 + 0.28 * math.sin(i_h * 0.5)),
                    rng=rng, color=spec.get("brillo_color", "salvia"))
    if spec.get("espejo"):
        capa = Image.new("RGBA", im.size, (0, 0, 0, 0))
        m.solo(capa, personaje, nombre, x, y, escala=escala, rng=rng, rot=_num(spec, "rot", 0, t), pivote=pivote)
        caja = capa.getbbox()
        capa = capa.transpose(Image.FLIP_LEFT_RIGHT)
        im.paste(capa, (0, 0), capa)
        return (im.width - caja[2], caja[1], im.width - caja[0], caja[3]) if caja else (x, y, x, y)
    m.solo(im, personaje, nombre, x, y, escala=escala, rng=rng, rot=_num(spec, "rot", 0, t), pivote=pivote)
    png = m._png(personaje, nombre)
    b = png.getbbox() or (0, 0, png.width, png.height)
    k = escala / a["escala_png"]
    return (x + (b[0] * k - pivote[0] * escala), y + (b[1] * k - pivote[1] * escala),
            x + (b[2] * k - pivote[0] * escala), y + (b[3] * k - pivote[1] * escala))


def _props_sueltos(d, cuadro, anclas_fondo, t, rng, delante):
    """Dibuja los props sueltos de la capa pedida. Devuelve las cajas que el globo tiene que
    esquivar (la burbuja de pensamiento y la nube de garabatos)."""
    cajas = []
    for p in _lista(cuadro.get("props")):
        if bool(p.get("delante", False)) != delante:
            continue
        fn = PROPS_SIMPLES.get(p["nombre"])
        if not fn:
            raise SystemExit("prop simple desconocido: %s (hay: %s)" % (p["nombre"], ", ".join(sorted(PROPS_SIMPLES))))
        px, py = _posicion(p, anclas_fondo, t)
        esc = float(p.get("escala", 1.0))
        opciones = {k: v for k, v in p.items()
                    if k not in ("nombre", "x", "y", "escala", "delante", "hacia", "en", "dx", "dy")}
        for clave in list(opciones):
            if clave.startswith("hacia_"):
                base = clave[6:]
                opciones[base] = lerp(float(p.get(base, 0)), float(opciones.pop(clave)), t)
        fn(d, px, py, esc, rng, t=t, **opciones)
        if p["nombre"] == "burbuja_pensamiento":
            cajas.append((px - 220 * esc, py - 160 * esc, px + 220 * esc, py + 160 * esc))
        elif p["nombre"] == "nube_garabatos":          # el ruido mental tampoco se tapa (WS34)
            r = 90 * esc * max(0.06, 1 - float(opciones.get("disolucion", 0)))
            cajas.append((px - r, py - r, px + r, py + r))
    return cajas


def _anillos(d, m, cuadro, i, rng):
    """Dos anillos salvia que crecen desde el pecho: la respiración."""
    spec = cuadro.get("teo") or {}
    x, y = _posicion(spec, {}, 0)
    escala = float(spec.get("escala", 1.6))
    try:
        px, py = _ancla_hoja(m, "teo", _cuerpo_de(spec, i), "pecho", x, y, escala)
    except KeyError:
        px, py = x, y - 120 * escala
    for k in range(2):
        r = 170 + 120 * k + 40 * math.sin(i * 0.45 - k * 0.9)
        R.circle(d, px, py, r, rng, width=(4 if k == 0 else 3), color=R.SAGE_LIGHT, amp=3, ry=r * 1.1)


def _pipo_asoma(m, im, cuadro, rng, cara=None):
    """Pipo no está en el cuadro pero habla: se pega su cabeza sola asomando por un borde.
    La cara del GLOBO manda sobre la del cuadro (WS36: Pipo entra contento y vuelve enojado)."""
    spec = cuadro.get("pipo_asoma") or {}
    lado = spec.get("lado", "derecha")
    cara = "cara_" + (cara or spec.get("cara", CARAS_ASOMA.get(cuadro.get("escena"), "alegria_sarcastica")))
    escala = float(spec.get("escala", 1.15))
    # la esquina de abajo a la derecha es del pulgar y del número de página: Pipo no va ahí
    x, y = {"izquierda": (100, 1420), "derecha": (R.W - 100, 1420), "abajo": (320, R.H - 70)}[lado]
    rot = {"izquierda": 12, "derecha": -12, "abajo": 0}[lado]
    m.solo(im, "pipo", cara, x, y, escala=escala, rng=rng, rot=rot, pivote=(200, 230))
    x0, y0, x1, y1 = caja_pieza(m, "pipo", cara)
    caja = (x + x0 * escala, y + (y0 + 120) * escala, x + x1 * escala, y + (y1 + 120) * escala)
    return (x, y - 140 * escala), caja


def _zoom(m, im, d, spec, i, n, t, rng):
    """La hoja "acerca" (REGLAS §2): una pieza o un prop grande en primer plano.
    Devuelve su caja, para que el globo no le pase por encima."""
    x, y = float(spec.get("x", 540)), float(spec.get("y", 950))
    escala = float(spec.get("escala", 3.0))
    caja = (x - 130 * escala, y - 180 * escala, x + 130 * escala, y + 180 * escala)
    if spec.get("prop"):
        PROPS_SIMPLES[spec["prop"]](d, x, y, escala, rng, t=t,
                                    **{k: v for k, v in spec.items()
                                       if k not in ("prop", "x", "y", "escala", "manos", "rot", "pieza", "ciclo")})
    else:
        personaje, pieza = spec["pieza"].split("/")
        ciclo = spec.get("ciclo")
        if ciclo:
            pieza = ciclo[i % len(ciclo)]
        m.solo(im, personaje, pieza, x, y, escala=escala, rng=rng, rot=float(spec.get("rot", 0)),
               pivote=tuple(spec.get("pivote", (200, 200))))
    if spec.get("manos"):                             # las dos manos que lo sostienen
        k = escala / 3.2
        for dx, dy in ((-210, 300), (250, 250)):
            hx, hy = x + dx * k, y + dy * k
            R.circle(d, hx, hy, 92 * k, rng, width=7, fill=R.CREAM, ry=76 * k)
            R.stroke(d, [(hx - 20 * k, hy - 60 * k), (hx + 24 * k, hy - 110 * k)], rng, width=7)
    return [caja]


# ---------------------------------------------------------------- la escena de la magia (bloque fijo)
# Cuatro momentos con TRES huecos (contrato de Tomás, WS33 §1): el guion solo declara
# `accion` (medita | pasea), `burbuja` (el descubrimiento del volumen) y `final` (la acción
# que muestra el cambio, con su entorno). Todo lo demás es fijo en todos los volúmenes.

TEXTOS_MAGIA = {"enciende": "hasta que un día, algo se enciende.",
                "medita": "por suerte, Teo descubrió la Pausa.",
                "pasea": "por suerte, Teo descubrió la Pausa.",
                "escribe": "y escribió lo que de verdad importa.",
                "final": "y ahora se le nota."}
HOJAS_MAGIA = {"enciende": 26, "accion": 34, "escribe": 34, "resultado": 38}   # 13,2 s
TEO_MAGIA = 1.6


def _en_mano(previo, hojas, texto, cara="en_serio"):
    """El teléfono se enciende EN LA MISMA IMAGEN del cuadro anterior (Tomás, WS35): se clona
    el cuadro, el prop `telefono_*` de Teo pasa a ciclar 1→3 (la pantalla se pone salvia y
    respira) y Pipo cambia la cara. Sin zoom: no se corta la escena."""
    if not previo:
        raise SystemExit("la magia con `enciende: en_mano` necesita un cuadro antes (el de la escena previa)")
    c = copy.deepcopy(previo)
    c["hojas"] = hojas
    c["pipo_dice"] = texto
    c.pop("globo_desde", None)
    if c.get("pipo"):
        c["pipo"] = dict(c["pipo"], cara=cara)
    props = _lista((c.get("teo") or {}).get("prop"))
    tel = [pz for pz in props if str(pz.get("nombre", "")).startswith("telefono")]
    if not tel:
        raise SystemExit("`enciende: en_mano`: en el cuadro anterior Teo no tiene un prop telefono_*")
    tel[0].update({"nombre": "telefono_2", "brillo": 1.0,
                   "escala": float(tel[0].get("escala", 1.0)) * 1.45,     # a la escala de la mano, el verde no se lee
                   "ciclo": ["telefono_2", "telefono_3", "telefono_2", "telefono_3"]})
    c["teo"] = dict(c["teo"], prop=props)
    return c


def cuadros_magia(esc, previo=None):
    """Expande la escena `magia` en sus cuadros. Los tres huecos: accion, burbuja, final."""
    accion = esc.get("accion", "medita")
    if accion not in ("medita", "pasea"):
        raise SystemExit("la escena magia acepta accion: medita | pasea (llegó %r)" % accion)
    burbuja = esc.get("burbuja", "abuelos")
    if burbuja not in DIBUJOS:
        raise SystemExit("dibujo de burbuja desconocido: %s (hay: %s)" % (burbuja, ", ".join(DIBUJOS)))
    fin = esc.get("resultado") or esc.get("final") or {}
    txt = dict(TEXTOS_MAGIA, **(esc.get("textos") or {}))
    hojas = dict(HOJAS_MAGIA, **(esc.get("hojas") or {}))
    teo = {"x": 420, "y": 1100, "escala": TEO_MAGIA}
    pipo = {"cuerpo": "sentado", "x": 890, "y": 1300, "escala": 0.58}

    # momento 1 · el teléfono se enciende. Dos modos: `zoom` (WS34, la hoja "acerca" del
    # teléfono grande) o `en_mano` (WS35, Tomás: la misma imagen anterior, el teléfono que Teo
    # ya tiene en la mano se pone verde).
    if esc.get("enciende", "zoom") == "en_mano":
        c = [_en_mano(previo, hojas["enciende"], txt["enciende"])]
    else:
        c = [{"hojas": hojas["enciende"],
              "zoom": {"pieza": "props/telefono_1", "escala": 2.7, "rot": -12, "manos": True,
                       "ciclo": ["telefono_1", "telefono_2", "telefono_3", "telefono_2"]},
              "pipo_dice": txt["enciende"], "pipo_asoma": {"lado": "izquierda", "cara": "en_serio"}}]

    # momento 2 · la pequeña acción, cargando el aura (hueco 1: medita | pasea)
    burbuja_accion = esc.get("burbuja_accion")
    if burbuja_accion and burbuja_accion not in DIBUJOS:
        raise SystemExit("dibujo de burbuja desconocido: %s (hay: %s)" % (burbuja_accion, ", ".join(DIBUJOS)))
    if accion == "medita":
        cuadro = {"hojas": hojas["accion"], "fondo": esc.get("fondo_accion", "rincon"), "anillos": True,
                  "teo": dict(teo, cuerpo="medita", x=430, y=1180, aura="sube", pulso=True,
                              cara="cerrada_sonrisa"),
                  "pipo": dict(pipo, cara=esc.get("cara_accion", "orgullo")),
                  "pipo_dice": txt["medita"]}
        if burbuja_accion:      # lo que ve en la Pausa (vol. 1: la familia riéndose)
            cuadro["props"] = [dict({"nombre": "burbuja_pensamiento", "x": 700, "y": 430, "escala": 1.0,
                                     "dibujo": burbuja_accion, "punta": (430, 830), "delante": True},
                                    **(esc.get("burbuja_accion_pos") or {}))]
        c.append(cuadro)
    else:
        c.append({"hojas": hojas["accion"], "fondo": esc.get("fondo_accion", "calle"), "parallax": 26,
                  "teo": dict(teo, cuerpo="camina", ciclo=True, cara="costado_sonrisa", x=400, y=1120,
                              aura="sube", pulso=True),
                  "pipo": {"cuerpo": "camina", "ciclo": True, "fase": 2, "cara": "orgullo",
                           "x": 790, "y": 1290, "escala": 0.7},
                  "pipo_dice": txt["pasea"]})

    # momento 3 · escribe: la burbuja es el descubrimiento del volumen (hueco 2)
    c.append({"hojas": hojas["escribe"], "fondo": "banco_plaza",
              "teo": dict(teo, cuerpo="sentado_erguido", cara="abajo_sonrisa", x=330, y=1090,
                          prop={"nombre": "cuadernito_0", "ciclo": ["cuadernito_0", "cuadernito_1", "cuadernito_2", "cuadernito_3"],
                                "dx": 30, "dy": -10, "rot": -10}),
              "pipo": dict(pipo, cara="orgullo"),
              "props": [dict({"nombre": "burbuja_pensamiento", "x": 740, "y": 430, "escala": 0.9,
                              "dibujo": burbuja, "punta": (370, 610), "delante": True},
                             **(esc.get("burbuja_pos") or {}))],
              "pipo_dice": txt["escribe"]})

    # momento 4 · el RESULTADO (Tomás, WS34): la acción con el aura desplegada (hueco 3)
    ultimo = {"hojas": hojas["resultado"], "fondo": fin.get("fondo", "mesa_familiar"),
              "teo": dict(teo, cuerpo="sentado_erguido", cara="costado_sonrisa", x=400, y=1100, aura=1.0, pulso=True),
              "pipo": {"cuerpo": "sentado", "cara": "orgullo", "x": 185, "y": 1345, "escala": 0.55},
              "secundarios": fin.get("secundarios", [{"tipo": "abuela", "x": 720, "y": 900},
                                                     {"tipo": "abuelo", "x": 920, "y": 890}]),
              "pipo_dice": fin.get("pipo_dice", txt["final"])}
    for clave in ("teo", "pipo", "props", "piezas", "secundarios", "hojas", "globo_desde"):
        if clave in fin:
            if clave in ("teo", "pipo"):
                ultimo[clave] = dict(ultimo[clave], **fin[clave])
            else:
                ultimo[clave] = fin[clave]
    c.append(ultimo)
    return c


# ---------------------------------------------------------------- el guion → cuadros

def cargar(ruta):
    with open(ruta) as f:
        g = yaml.safe_load(f)
    if not isinstance(g, dict) or "escenas" not in g:
        raise SystemExit("el guion tiene que ser un mapa con `escenas` (ver REGLAS.md §7)")
    return g


# ---------------------------------------------------------------- la gramática de la serie
# Tomás, WS36. Todas las píldoras repiten el MISMO patrón visual, y eso es lo que enseña a
# la gente a leer la cuenta sin que nadie se lo explique:
#
#   CONEXIÓN    (algo que trae a Teo al presente)   → Pipo CONTENTO · Teo con AURA verde y sonrisa
#   DESCONEXIÓN (algo que se lo lleva del presente) → Pipo ENOJADO  · Teo TRISTE y sin aura
#
# Se declara con una palabra en el cuadro (`estado: conexion | desconexion`) y el motor pone
# el aura, la boca de Teo y la cara de Pipo. El guion sigue eligiendo la MIRADA de Teo
# (abajo, cerrada, costado…) y puede pisar cualquier cosa a mano.

BOCAS_TEO = ("abierta", "fruncida", "plana", "sonrisa", "triste")
ESTADOS = {"conexion": {"aura": "sube", "boca": "sonrisa", "pipo": "orgullo"},
           "desconexion": {"aura": 0, "boca": "triste", "pipo": "fastidio"}}


def _con_boca(cara, boca):
    """Cambia SOLO la boca de una cara de Teo (`cerrada_plana` → `cerrada_triste`)."""
    if isinstance(cara, list):
        return [_con_boca(c, boca) for c in cara]
    partes = str(cara).split("_")
    for k in (-1, -2):                       # -2 cubre las caras con el pelo `_caido`
        if len(partes) >= abs(k) + 1 and partes[k] in BOCAS_TEO:
            partes[k] = boca
            break
    return "_".join(partes)


def _aplicar_estado(c):
    """`estado: conexion | desconexion` en un cuadro: pone la gramática y no pisa lo explícito."""
    e = ESTADOS.get(c.get("estado"))
    if not e:
        return c
    teo = dict(c["teo"]) if c.get("teo") else None
    if teo:
        teo.setdefault("aura", e["aura"])
        if "cara" in teo and not teo.get("boca_libre"):
            teo["cara"] = _con_boca(teo["cara"], e["boca"])
        c["teo"] = teo
    if c.get("pipo") and "cara" not in c["pipo"]:
        c["pipo"] = dict(c["pipo"], cara=e["pipo"])
    asoma = dict(c.get("pipo_asoma") or {})
    asoma.setdefault("cara", e["pipo"])
    c["pipo_asoma"] = asoma
    return c


def aplanar(g):
    """Convierte el guion en una lista plana de cuadros, cada uno con sus hojas."""
    fuera = []
    for esc in g["escenas"]:
        tipo = esc.get("tipo", "problema")
        if tipo == "magia":
            cuadros = cuadros_magia(esc, fuera[-1] if fuera else None)
        else:
            cuadros = list(esc.get("cuadros") or [])
            if not cuadros:
                raise SystemExit("la escena %r no tiene cuadros" % tipo)
        for k, c in enumerate(cuadros):
            c = dict(c)
            c.setdefault("fondo", esc.get("fondo", "ninguno"))
            c.setdefault("parallax", esc.get("parallax", 0))
            c["escena"] = tipo
            c.setdefault("estado", esc.get("estado"))
            c = _aplicar_estado(c)
            if "duracion" in c:
                c["hojas"] = max(1, int(round(float(c["duracion"]) * HOJAS_POR_SEG)))
            c["hojas"] = int(c.get("hojas", 10))
            if c["fondo"] not in FONDOS:
                raise SystemExit("fondo desconocido: %s (hay: %s)" % (c["fondo"], ", ".join(sorted(FONDOS))))
            fuera.append(c)
    if fuera:
        # WS36: el PRIMER cuadro entra con su globo desde la hoja 0. En el resto la imagen
        # respira medio segundo sola (el ojo ve el chiste antes de leerlo), pero al principio
        # del video medio segundo sin texto es medio segundo para irse.
        fuera[0].setdefault("globo_desde", 0)
    return fuera


# ------------------------------------------------- B2b · el rótulo del arranque (WS36)
# El vol. 1 midió 3,64 s de tiempo medio de visualización sobre 30,7 s (11,8 % de retención,
# 1,7 % de completado): la gente se iba ANTES del primer chiste, durante los 2 s de cartel
# quieto. En el feed, una pantalla fija al principio se lee como "esto va lento" y el dedo
# sube. Desde acá el video ABRE con la primera imagen y su globo, y el título viaja como
# RÓTULO superpuesto arriba. El cartel no se pierde: se guarda como PORTADA del video
# (`<nombre>_portada.png`), que es donde de verdad trabaja, en la grilla del perfil.

ROTULO_SEG = 2.4                 # cuánto se queda el rótulo sobre la imagen viva
ROTULO_FUNDE = 0.5               # los últimos segundos se va con un fundido
ROTULO_Y = (150, 390)            # la banda vive debajo de la barra "Para ti" de TikTok


def _alpha_rotulo(pagina, hojas, funde):
    """1 mientras el rótulo está entero, baja a 0 en las últimas `funde` hojas."""
    if hojas <= 0 or pagina > hojas:
        return 0.0
    if pagina <= hojas - funde:
        return 1.0
    return max(0.0, (hojas - pagina + 1) / (funde + 1.0))


def rotulo_titulo(im, g, rng, alpha=1.0):
    """El título del volumen superpuesto arriba de la imagen, sobre el video ya compuesto
    (no es papel: no se dobla con el paso de página). Cuarta tinta del volumen, como el cartel."""
    if alpha <= 0.01:
        return im
    c = g.get("cartel") or {}
    tinta = TINTAS.get(c.get("tinta", "ocre"), TINTAS["ocre"])
    tmb = (rng.randint(-2, 2), rng.randint(-2, 2))            # temblor: que se sienta dibujado
    y0, y1 = ROTULO_Y[0] + tmb[1], ROTULO_Y[1] + tmb[1]
    x0, x1 = 66 + tmb[0], R.W - 66 + tmb[0]
    capa = Image.new("RGBA", (R.W, R.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    d.rounded_rectangle((x0, y0, x1, y1), 28, fill=tinta + (255,))
    d.rounded_rectangle((x0 + 10, y0 + 10, x1 - 10, y1 - 10), 20,
                        outline=mezcla(tinta, R.IVORY, 0.5) + (255,), width=4)
    cx = (x0 + x1) / 2
    d.text((cx, y0 + 62), "TEO Y PIPO EN", fill=R.CREAM + (240,), font=R.font(46, bold=True), anchor="mm")
    titulo = str(g.get("titulo", "")).upper()
    d.text((cx, y0 + 152), titulo, fill=R.IVORY + (255,),
           font=font_que_entra(d, titulo, x1 - x0 - 96, 108), anchor="mm")
    d.text((x1 - 36, y1 - 34), "VOL. %s" % g.get("volumen", 0),
           fill=mezcla(tinta, R.CREAM, 0.8) + (255,), font=R.font(30), anchor="rm")
    if alpha < 1.0:
        capa.putalpha(capa.getchannel("A").point(lambda v: int(v * alpha)))
    fuera = im.convert("RGBA")
    fuera.alpha_composite(capa)
    return fuera.convert("RGB")


# ---------------------------------------------------------------- B2 · el cartel de apertura

def _remolino(d, x, y, rng, s=1.0, vueltas=1.6, color=None):
    """El remolino de velocidad de la tapa de Tintín: una espiral de línea que se abre."""
    pts = []
    for k in range(int(vueltas * 24)):
        a = k / 24 * 2 * math.pi
        r = 6 * s + 9 * s * a
        pts.append((x + r * math.cos(a), y + r * math.sin(a) * 0.8))
    R.stroke(d, pts, rng, width=6, color=color or R.UMBER, amp=1.4)


def imagen_cartel_iluminado(im, m, rng, cx, cy, r):
    """B1 (WS34, tercera vuelta de Tomás): Teo corre grande y limpio (cuerpo `corre`, sonrisa
    de costado) y Pipo, chico abajo a la derecha, está sentado en flor de loto haciendo la Y
    con las patas y la V de la victoria (cuerpo `buda_victoria`, alegría sarcástica), con unos
    rayitos de iluminado. Sin remolinos ni ruido mental. El círculo, el centro y el radio no
    cambian."""
    d = ImageDraw.Draw(im)
    R.circle(d, cx, cy, r, rng, width=9, color=R.UMBER, fill=R.CREAM)
    m.pegar(im, "teo", "corre", CARA_CARTEL_TEO, cx - 90, cy + 40, escala=1.16, rng=rng)
    px, py = cx + 190, cy + 172
    d = ImageDraw.Draw(im)
    for k in range(7):                              # rayitos cortos sobre Pipo
        a = -math.pi / 2 + (k - 3) * 0.34
        R.stroke(d, [(px + 128 * math.cos(a), py - 40 + 128 * math.sin(a)),
                     (px + 152 * math.cos(a), py - 40 + 152 * math.sin(a))], rng, width=4, color=R.TAUPE, amp=1.0)
    m.pegar(im, "pipo", "buda_victoria", CARA_CARTEL_PIPO, px, py, escala=0.54, rng=rng)


CARA_CARTEL_PIPO, CARA_CARTEL_TEO = "cara_alegria_sarcastica", "cara_costado_sonrisa"


def imagen_cartel_tintin(im, m, rng, cx, cy, r):
    """B1 (WS34): LA viñeta de la serie, a lo Tintín (elegida por Tomás sobre dos alternativas). Teo corre inclinado con los brazos
    bombeando (cuerpo `corre`, cara costado_sonrisa) y Pipo galopa ADELANTE (cuerpo `corre`,
    alegría sarcástica), los dos rompiendo apenas el borde del círculo; atrás, los remolinos de
    velocidad y unas líneas de polvo. El círculo, el centro y el radio no cambian."""
    d = ImageDraw.Draw(im)
    R.circle(d, cx, cy, r, rng, width=9, color=R.UMBER, fill=R.CREAM)
    # los remolinos, atrás de Teo, y las líneas de velocidad atrás de Pipo
    _remolino(d, cx - 222, cy + 168, rng, s=0.9)
    _remolino(d, cx - 272, cy + 96, rng, s=0.55, vueltas=1.3)
    for k, (dx, dy, largo) in enumerate(((-20, 150, 110), (-32, 184, 80), (-10, 216, 100))):
        R.stroke(d, [(cx + dx - largo, cy + dy), (cx + dx, cy + dy)], rng, width=5, color=R.TAUPE, amp=1.0)
    m.pegar(im, "teo", "corre", "cara_costado_sonrisa", cx - 70, cy - 10, escala=1.18, rng=rng)
    m.pegar(im, "pipo", "corre", "cara_alegria_sarcastica", cx + 165, cy + 200, escala=0.74, rng=rng, rot=-6)


VINETAS = {"tintin": imagen_cartel_tintin, "iluminado": imagen_cartel_iluminado}


def imagen_cartel(im, m, rng, cx, cy, r, vineta="tintin"):
    """La viñeta fija del cartel. `tintin` (los dos corriendo, elegida por Tomás en la WS34) es
    la de la serie; `iluminado` queda como alternativa (`cartel: {vineta: iluminado}`)."""
    fn = VINETAS.get(vineta)
    if not fn:
        raise SystemExit("viñeta desconocida: %s (hay: %s)" % (vineta, ", ".join(VINETAS)))
    fn(im, m, rng, cx, cy, r)


def _formas(d, rng, tinta, forma, claro, oscuro):
    if forma == "diagonales":
        for k in range(-3, 9):
            x = k * 210
            d.polygon([(x, 0), (x + 95, 0), (x + 95 - 620, R.H), (x - 620, R.H)], fill=claro if k % 2 else oscuro)
    elif forma == "rayos":
        for k in range(16):
            a0, a1 = k * math.pi / 8, k * math.pi / 8 + math.pi / 16
            d.polygon([(540, 1010), (540 + 2400 * math.cos(a0), 1010 + 2400 * math.sin(a0)),
                       (540 + 2400 * math.cos(a1), 1010 + 2400 * math.sin(a1))], fill=claro)
    elif forma == "circulo":
        R.circle(d, 540, 1010, 470, rng, width=0, fill=claro, amp=4)
        R.circle(d, 540, 1010, 470, rng, width=10, color=oscuro, amp=4)
    elif forma == "franja":
        d.rectangle((0, 300, R.W, 620), fill=claro)
        d.rectangle((0, 1330, R.W, 1560), fill=claro)
    elif forma == "marco":
        d.rectangle((60, 90, R.W - 60, R.H - 90), outline=claro, width=26)
        d.rectangle((110, 140, R.W - 110, R.H - 140), outline=oscuro, width=6)


def cartel(g, m, i, n, rng):
    """2 s, respira sin pasar página. Cuarta tinta + formas por volumen (REGLAS §3)."""
    c = g.get("cartel") or {}
    tinta = TINTAS.get(c.get("tinta", "ocre"), TINTAS["ocre"])
    im = R.paper(rng, base=tinta)
    d = ImageDraw.Draw(im)
    _formas(d, rng, tinta, c.get("formas", "diagonales"), mezcla(tinta, R.CREAM, 0.26), mezcla(tinta, R.UMBER, 0.35))
    f = font_que_entra(d, "TEO Y PIPO", 900, 210)
    d.text((R.W / 2, 400), "TEO Y PIPO", fill=R.IVORY, font=f, anchor="mm")
    R.stroke(d, [(240, 520), (840, 520)], rng, width=6, color=R.IVORY, amp=1.5)
    imagen_cartel(im, m, rng, R.W / 2, 1030, 340, vineta=c.get("vineta", "tintin"))
    d = ImageDraw.Draw(im)
    titulo = str(g.get("titulo", "SIN TÍTULO")).upper()
    d.text((R.W / 2, 1480), "en", fill=R.IVORY, font=R.font(52), anchor="mm")
    d.text((R.W / 2, 1600), titulo, fill=R.IVORY, font=font_que_entra(d, titulo, 900, 120), anchor="mm")
    d.text((R.W / 2, 1740), "Vol. %s" % g.get("volumen", 0), fill=mezcla(tinta, R.CREAM, 0.75),
           font=R.font(54), anchor="mm")
    return im


# ---------------------------------------------------------------- C · el cierre fijo

# La contratapa NO se toca (Tomás, WS36, explícito): el gancho de la serie va primero y
# grande, y abajo el bloque de Dwellia. El mensaje general de la cuenta se dice en el globo
# del cierre, no acá. Igual quedó configurable por guion: `cierre: {textos: [a, b, c, d, e]}`.
TEXTOS_CONTRATAPA = ["Teo y Pipo volverán", "próximamente",
                     "Dwellia", "una Pausa al día, fuera del teléfono", "link en la bio"]


CARA_CIERRE, ESC_CIERRE, POS_CIERRE, PIVOTE_CIERRE = "cara_alegria_sarcastica", 2.15, (R.W / 2, 1010), (200, 210)


def caja_cierre(m):
    """La caja de la cara de Pipo en la hoja del cierre, en coordenadas de la hoja."""
    x0, y0, x1, y1 = caja_pieza(m, "pipo", CARA_CIERRE)
    dy = m.anclas("pipo", CARA_CIERRE)["cuello"][1] - PIVOTE_CIERRE[1]
    return (POS_CIERRE[0] + x0 * ESC_CIERRE, POS_CIERRE[1] + (y0 + dy) * ESC_CIERRE,
            POS_CIERRE[0] + x1 * ESC_CIERRE, POS_CIERRE[1] + (y1 + dy) * ESC_CIERRE)


def hoja_pipo_camara(m, i, n, rng, dice=None):
    """C1: Pipo a cámara, cabeza grande, alegría sarcástica. `dice` (WS36) le pone su globo:
    es el único lugar donde Pipo le habla derecho a la persona, y ahí va el mensaje de la
    cuenta — el iris se cierra sobre eso."""
    im = R.paper(rng)
    m.solo(im, "pipo", CARA_CIERRE, POS_CIERRE[0], POS_CIERRE[1], escala=ESC_CIERRE, rng=rng, pivote=PIVOTE_CIERRE)
    if dice:
        caja = caja_cierre(m)
        cx = (caja[0] + caja[2]) / 2
        globo(ImageDraw.Draw(im), dice, (cx, caja[1] + 0.3 * (caja[3] - caja[1])), rng,
              evitar=[caja], flota=4.0 * math.sin(i * 0.4), modo="abajo", ancla_abajo=(cx, caja[3] + 14))
    return im


def centro_cierre(m):
    """El centro exacto de la cara de Pipo en la hoja del cierre: ahí se cierra el iris."""
    x0, y0, x1, y1 = caja_pieza(m, "pipo", CARA_CIERRE)     # relativo al cuello (200, 350)
    dy = m.anclas("pipo", CARA_CIERRE)["cuello"][1] - PIVOTE_CIERRE[1]
    return (POS_CIERRE[0] + (x0 + x1) / 2 * ESC_CIERRE,
            POS_CIERRE[1] + ((y0 + y1) / 2 + dy) * ESC_CIERRE)


def frames_iris(base, cx, cy, cuantos):
    """C2: el iris Looney Tunes. El círculo se achica sobre la cara; afuera, tinta tierra."""
    fuera = []
    for k in range(cuantos):
        e = (k + 1) / cuantos
        r = int(1500 * (1 - e) ** 1.7)
        im = Image.new("RGB", (R.W, R.H), R.UMBER)
        if r > 0:
            mask = Image.new("L", (R.W, R.H), 0)
            ImageDraw.Draw(mask).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
            im.paste(base, (0, 0), mask)
        fuera.append(im)
    return fuera


FUENTE_FRAUNCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes", "Fraunces-Italic.ttf")


def font_fraunces(tam):
    """La serif itálica de la marca (la del ícono de la app). Georgia Italic de respaldo."""
    for p in [FUENTE_FRAUNCES, "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, tam)
    return R.font(tam)


def icono_dwellia(im, cx, cy, lado):
    """El símbolo de Dwellia, literal al ícono de la app (`apps/web/public/icon.svg`, WS34):
    cuadrado redondeado con el degradado radial salvia (claro arriba, profundo en los bordes)
    y la D itálica en marfil (Fraunces)."""
    n = 256
    tile = Image.new("RGB", (n, n))
    px = tile.load()
    paradas = [(0.0, (168, 187, 160)), (0.6, (143, 165, 138)), (1.0, (111, 138, 105))]
    fx, fy, fr = n * 0.5, n * 0.36, n * 0.75
    for y in range(n):
        for x in range(n):
            t = min(1.0, math.hypot(x - fx, y - fy) / fr)
            for (t0, c0), (t1, c1) in zip(paradas, paradas[1:]):
                if t <= t1:
                    px[x, y] = mezcla(c0, c1, (t - t0) / (t1 - t0))
                    break
    tile = tile.resize((lado, lado), Image.LANCZOS)
    mask = Image.new("L", (lado, lado), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, lado - 1, lado - 1), int(lado * 112 / 512), fill=255)
    im.paste(tile, (int(cx - lado / 2), int(cy - lado / 2)), mask)
    d = ImageDraw.Draw(im)
    # sobre la hoja salvia el borde del degradado se funde con el fondo: un filete marfil fino
    d.rounded_rectangle((cx - lado / 2, cy - lado / 2, cx + lado / 2, cy + lado / 2), int(lado * 112 / 512),
                        outline=mezcla(R.SAGE_DEEP, R.IVORY, 0.6), width=4)
    d.text((cx, cy - lado * 0.02), "D", fill=(251, 245, 232), font=font_fraunces(int(lado * 340 / 512)), anchor="mm")


def contratapa(rng, textos=None):
    """C3: hoja salvia. Primero y GRANDE "Teo y Pipo volverán próximamente"; abajo y más chico el
    bloque de Dwellia con el ícono de la app (WS34, orden invertido por Tomás). Fija para todos los volúmenes."""
    T = list(textos or TEXTOS_CONTRATAPA)
    im = R.paper(rng, base=R.SAGE_DEEP)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((80, 120, R.W - 80, R.H - 120), 30, outline=mezcla(R.SAGE_DEEP, R.CREAM, 0.45), width=5)
    d.text((R.W / 2, 560), T[0], fill=R.IVORY, font=font_que_entra(d, T[0], 880, 108, condensada=False), anchor="mm")
    d.text((R.W / 2, 690), T[1], fill=R.IVORY, font=font_que_entra(d, T[1], 880, 108, condensada=False), anchor="mm")
    R.stroke(d, [(400, 840), (680, 840)], rng, width=4, color=mezcla(R.SAGE_DEEP, R.CREAM, 0.5), amp=1.2)
    icono_dwellia(im, R.W / 2, 1110, 200)
    d = ImageDraw.Draw(im)
    d.text((R.W / 2, 1300), T[2], fill=R.IVORY, font=R.font(84, bold=True), anchor="mm")
    d.text((R.W / 2, 1385), T[3], fill=R.CREAM, font=R.font(40), anchor="mm")
    d.text((R.W / 2, 1660), T[4], fill=mezcla(R.SAGE_DEEP, R.CREAM, 0.78), font=R.font(38), anchor="mm")
    return im


# ---------------------------------------------------------------- el render

def render(ruta_guion, solo_cuadros=False):
    g = cargar(ruta_guion)
    nombre = g.get("nombre") or os.path.splitext(os.path.basename(ruta_guion))[0]
    MODO_GLOBO[0] = g.get("globos", "abajo")
    SUBE_ESCENA[0] = int(g.get("subir_escena", 220 if MODO_GLOBO[0] == "abajo" else 0))
    m = Marioneta()
    cuadros = aplanar(g)

    # El envase del feed (WS36): por defecto el video ABRE con la historia y el título va como
    # rótulo; `cartel: {modo: apertura}` vuelve a la pantalla fija de 2 s del vol. 1.
    c_cartel = g.get("cartel") or {}
    modo_cartel = c_cartel.get("modo", "rotulo")
    hojas_rotulo = int(float(c_cartel.get("rotulo_seg", ROTULO_SEG)) * HOJAS_POR_SEG) if modo_cartel == "rotulo" else 0
    hojas_funde = max(1, int(float(c_cartel.get("rotulo_funde", ROTULO_FUNDE)) * HOJAS_POR_SEG))
    cie = g.get("cierre") or {}
    n_pipo = max(1, int(float(cie.get("pipo", 3.0 if cie.get("dice") else 0.5)) * HOJAS_POR_SEG))
    seg_iris = float(cie.get("iris", 0.9))
    seg_tapa = float(cie.get("tapa", 0.5))
    seg_contratapa = float(cie.get("contratapa", 1.8))
    total_hojas = sum(c["hojas"] for c in cuadros) + n_pipo

    pruebas = os.path.join(RAIZ, "pruebas")
    os.makedirs(pruebas, exist_ok=True)
    png = os.path.join(pruebas, "%s_cuadros.png" % nombre)
    hoja_de_cuadros(g, m, cuadros, total_hojas, modo_cartel=modo_cartel,
                    textos_cierre=cie.get("textos"), dice_cierre=cie.get("dice")).save(png)
    print("cuadros ->", png)
    # el cartel, siempre, como PORTADA para la grilla del perfil de TikTok
    portada = os.path.join(pruebas, "%s_portada.png" % nombre)
    cartel(g, m, 0, 1, random.Random(9000)).save(portada)
    print("portada ->", portada)
    if solo_cuadros:
        return

    frames = os.path.join(pruebas, "frames_%s" % nombre)
    os.makedirs(frames, exist_ok=True)
    for f in os.listdir(frames):
        os.remove(os.path.join(frames, f))
    k = [0]

    def emitir(im, veces=1):
        for _ in range(veces):
            im.save(os.path.join(frames, "f%05d.png" % k[0]))
            k[0] += 1

    # el cartel como PANTALLA solo en modo apertura (el del vol. 1). Por defecto no se emite:
    # el video arranca con la historia y el título viaja de rótulo.
    previo = None
    if modo_cartel == "apertura":
        n_cartel = max(1, int(float(c_cartel.get("duracion", 2.0)) * HOJAS_POR_SEG))
        for i in range(n_cartel):
            previo = cartel(g, m, i, n_cartel, random.Random(9000 + i))
            emitir(previo, R.HOLD)

    # la historia
    pagina = 0
    desp = 0.0
    for c in cuadros:
        n = c["hojas"]
        for i in range(n):
            pagina += 1
            rng = random.Random(pagina)
            im = R.chrome(hoja_de(m, c, i, n, rng, desp), pagina, total_hojas, rng)
            a = _alpha_rotulo(pagina, hojas_rotulo, hojas_funde)
            paso = R.page_turn(previo, im, 0.5) if previo is not None else im
            emitir(rotulo_titulo(paso, g, rng, a), 1)
            emitir(rotulo_titulo(im, g, rng, a), R.HOLD - 1)
            previo = im
            desp += float(c.get("parallax", 0) or 0)

    # el cierre fijo
    for i in range(n_pipo):
        pagina += 1
        rng = random.Random(pagina)
        im = R.chrome(hoja_pipo_camara(m, i, n_pipo, rng, cie.get("dice")), pagina, total_hojas, rng)
        emitir(R.page_turn(previo, im, 0.5), 1)
        emitir(im, R.HOLD - 1)
        previo = im
    cx, cy = centro_cierre(m)
    for im in frames_iris(previo, cx, cy, max(1, int(seg_iris * R.FPS))):
        emitir(im, 1)
    textos_ct = cie.get("textos")
    tapa = contratapa(random.Random(77), textos_ct)
    cerrado = Image.new("RGB", (R.W, R.H), R.UMBER)          # el iris terminó en tinta tierra
    n_tapa = max(1, int(seg_tapa * R.FPS))
    for i in range(n_tapa):
        emitir(R.close_book(cerrado, tapa, (i + 1) / n_tapa), 1)
    for i in range(max(1, int(seg_contratapa * HOJAS_POR_SEG))):
        emitir(contratapa(random.Random(7000 + i), textos_ct), R.HOLD)

    salida = os.path.join(pruebas, "%s.mp4" % nombre)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(R.FPS),
                    "-i", os.path.join(frames, "f%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "20", "-movflags", "+faststart", salida], check=True)
    print("hojas:", total_hojas, "cuadros de video:", k[0], "seg:", round(k[0] / R.FPS, 1), "->", salida)


# El cierre (WS36): se acorta de 6,1 s a ~3,7 s. Con 1,7 % de completado en el vol. 1, la
# contratapa la veían 3 personas de 183 y las otras 180 pagaban el peaje. Los tiempos se
# pueden mover por guion (`cierre: {pipo, iris, tapa, contratapa}`, en segundos).


def hoja_de_cuadros(g, m, cuadros, total_hojas, columnas=6, escala=0.30, modo_cartel="rotulo", textos_cierre=None, dice_cierre=None):
    """La hoja fija: un cuadro clave de cada cuadro del guion (más el cartel y el cierre),
    para revisar la lectura sin abrir el video. Con el envase del feed (WS36) el cartel ya no
    es la primera pantalla: aparece rotulado como PORTADA y el rótulo se dibuja sobre la
    primera imagen, que es lo que la persona ve de verdad en el segundo cero."""
    piezas = [("portada (grilla)" if modo_cartel == "rotulo" else "cartel",
               cartel(g, m, 0, 1, random.Random(9000)))]
    pagina = 0
    for k, c in enumerate(cuadros):
        n = c["hojas"]
        gs = globos_de(c)
        desde = int(c.get("globo_desde", GLOBO_DESDE))
        # un cuadro clave por globo (en el medio de su ventana o de su tramo); sin globo, al 72 %
        if gs and any("desde" in g or "hasta" in g for g in gs):
            claves = [min(n - 1, int((int(g.get("desde", 0)) + int(g.get("hasta", n))) / 2)) for g in gs]
        elif gs:
            tramo = max(1.0, (n - desde) / len(gs))
            claves = [min(n - 1, int(desde + tramo * (j + 0.5))) for j in range(len(gs))]
        else:
            claves = [int(n * 0.72)]
        for j, i in enumerate(claves):
            rng = random.Random(pagina + i + 1)
            etiqueta = "%d · %s" % (k + 1, c["escena"]) + (" (%d/%d)" % (j + 1, len(claves)) if len(claves) > 1 else "")
            pieza = R.chrome(hoja_de(m, c, i, n, rng, 0.0), pagina + i + 1, total_hojas, rng)
            if modo_cartel == "rotulo" and k == 0 and j == 0:
                pieza = rotulo_titulo(pieza, g, random.Random(1), 1.0)
                etiqueta += " · con rótulo"
            piezas.append((etiqueta, pieza))
        pagina += n
    piezas.append(("cierre", R.chrome(hoja_pipo_camara(m, 0, 6, random.Random(5), dice_cierre), total_hojas, total_hojas, random.Random(5))))
    piezas.append(("contratapa", contratapa(random.Random(77), textos_cierre)))

    w, h = int(R.W * escala), int(R.H * escala)
    filas = (len(piezas) + columnas - 1) // columnas
    margen, alto_rotulo = 26, 40
    im = Image.new("RGB", (columnas * w + (columnas + 1) * margen,
                           filas * (h + alto_rotulo) + (filas + 1) * margen + 70), R.SAND)
    d = ImageDraw.Draw(im)
    d.text((im.width / 2, 40), "%s · Vol. %s · %d cuadros · %d hojas · %.1f s de historia"
           % (g.get("titulo", ""), g.get("volumen", 0), len(cuadros), total_hojas, total_hojas / HOJAS_POR_SEG),
           fill=R.UMBER, font=R.font(34), anchor="mm")
    for k, (rotulo, pieza) in enumerate(piezas):
        cx = margen + (k % columnas) * (w + margen)
        cy = 70 + margen + (k // columnas) * (h + alto_rotulo + margen)
        im.paste(pieza.resize((w, h), Image.LANCZOS), (cx, cy))
        d.text((cx + w / 2, cy + h + 20), rotulo, fill=R.UMBER, font=R.font(24), anchor="mm")
    return im


def main():
    ap = argparse.ArgumentParser(description="Renderiza un volumen del flipbook desde su guion YAML.")
    ap.add_argument("guion", help="ruta al guion (Flipbook/guiones/volNN.yaml)")
    ap.add_argument("--solo-cuadros", action="store_true", help="solo la hoja fija de cuadros, sin mp4")
    args = ap.parse_args()
    render(args.guion, solo_cuadros=args.solo_cuadros)


if __name__ == "__main__":
    main()

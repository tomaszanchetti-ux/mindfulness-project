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


def fondo_sofa(d, rng, desp=0.0, capa="atras"):
    """Un sofá de línea, de frente: respaldo, asiento y dos brazos."""
    if capa == "atras":
        _piso(d, rng)
        R.stroke(d, [(250, 1170), (250, 940), (880, 940), (880, 1170)], rng, width=7, color=R.TAUPE)
        R.stroke(d, [(250, 1170), (880, 1170)], rng, width=8, color=R.TAUPE)
        R.stroke(d, [(190, 1330), (190, 1030)], rng, width=8, color=R.TAUPE)
        R.stroke(d, [(940, 1330), (940, 1030)], rng, width=8, color=R.TAUPE)
        R.stroke(d, [(190, 1030), (250, 1000)], rng, width=7, color=R.TAUPE)
        R.stroke(d, [(940, 1030), (880, 1000)], rng, width=7, color=R.TAUPE)
        R.stroke(d, [(190, 1330), (940, 1330)], rng, width=8, color=R.TAUPE)
        R.stroke(d, [(565, 940), (565, 1170)], rng, width=4, color=R.LINE)
        for x in (230, 960):
            R.stroke(d, [(x, 1330), (x, PISO)], rng, width=6, color=R.TAUPE)
    return {"sofa": (565, 1170)}


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
          "mesa_familiar": fondo_mesa_familiar, "sofa": fondo_sofa, "espejo_bano": fondo_espejo_bano,
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


DIBUJOS = {"abuelos": dibujo_abuelos}


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


def _texto_globo(d, texto, tam=52, minimo=38):
    """Georgia, minúsculas, hasta 3 líneas cortas: un globo alto lee mejor que uno ancho."""
    while True:
        f = R.font(tam)
        lineas = _envolver(d, texto, f, ANCHO_GLOBO)
        if len(lineas) <= 3 or tam <= minimo:
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


def globo(d, texto, ancla, rng, evitar=(), forzar=None):
    """Dibuja el globo de Pipo. `ancla` = (x, y) de su cabeza: de ahí sale la colita.
    `evitar` = cajas (x0, y0, x1, y1) que ni el globo ni la colita pueden tapar (las caras
    y la burbuja de pensamiento). Se prueban posiciones cerca de Pipo y se elige la primera
    que no tape nada; si ninguna limpia, la menos mala."""
    if not texto:
        return
    f, lineas, tam = _texto_globo(d, texto)
    tw = max(ancho(d, s, f)[0] for s in lineas)
    th = len(lineas) * int(tam * 1.28)
    rx, ry = tw * 0.70 + 40, th * 0.86 + 38

    ax, ay = ancla
    # la cabeza de la que sale la colita no cuenta como obstáculo de la colita
    esquivar_colita = [c for c in evitar
                       if not (c[0] - 30 < ax < c[2] + 30 and c[1] - 30 < ay < c[3] + 30)]
    if forzar:
        cx, cy = forzar
    else:
        candidatos = [(ax, ay - ry - 80), (ax - rx - 130, ay - 30), (ax + rx + 130, ay - 30),
                      (ax - rx - 90, ay - ry - 130), (ax + rx + 90, ay - ry - 130),
                      (ax, ay - ry - 330), (ax - 320, ay - ry - 380), (ax + 320, ay - ry - 380),
                      (R.W / 2, 340), (rx + 60, 340), (R.W - rx - 60, 340)]
        mejor, puntaje_mejor = None, None
        for k, (px, py) in enumerate(candidatos):
            px = entre(px, rx + 55, R.W - rx - 55)
            py = entre(py, ry + 150, R.H - ry - 290)
            caja = (px - rx, py - ry, px + rx, py + ry)
            b1, b2, base, punta = _colita(px, py, rx, ry, ax, ay)
            puntaje = 4.0 * sum(_solape(caja, c) for c in evitar)
            puntaje += 9.0 * sum(1 for c in esquivar_colita
                                 if _cruza(base, punta, c) or _cruza(b1, punta, c) or _cruza(b2, punta, c))
            puntaje += math.hypot(px - ax, py - ay) / 340.0 + k * 0.05
            puntaje += max(0.0, py - 650) / 250.0     # los globos viven arriba, como en la historieta
            if puntaje_mejor is None or puntaje < puntaje_mejor:
                mejor, puntaje_mejor = (px, py), puntaje
        cx, cy = mejor

    R.circle(d, cx, cy, rx, rng, width=6, fill=R.IVORY, ry=ry, amp=2.5)
    b1, b2, _, punta = _colita(cx, cy, rx, ry, ax, ay)
    d.polygon([b1, punta, b2, (cx, cy)], fill=R.IVORY)      # el relleno tapa el borde del óvalo
    R.stroke(d, [b1, punta], rng, width=6, amp=1.2)
    R.stroke(d, [b2, punta], rng, width=6, amp=1.2)
    for k, s in enumerate(lineas):
        d.text((cx, cy - th / 2 + int(tam * 1.28) * (k + 0.5)), s, fill=R.UMBER, font=f, anchor="mm")


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


def _cuerpo_de(spec, i):
    """`ciclo: true` convierte `camina` en camina_0..3, una fase por hoja."""
    cuerpo = spec["cuerpo"]
    if spec.get("ciclo"):
        cuerpo = "%s_%d" % (cuerpo, (i + int(spec.get("fase", 0))) % 4)
    return cuerpo


def _valor(v, t):
    """Un número, o "sube"/"baja" para una rampa dentro del cuadro."""
    if isinstance(v, str):
        return entre(t * 1.6 - 0.15, 0, 1) if v == "sube" else entre(1.2 - t * 1.6, 0, 1)
    return float(v or 0)


def pegar_personaje(m, im, d, personaje, spec, i, n, t, rng, anclas_fondo):
    """Pega un personaje con su prop en la mano. Devuelve (punto de cuello, caja de cara)."""
    cuerpo = _cuerpo_de(spec, i)
    cara = spec.get("cara", "frente_plana")
    x, y = _posicion(spec, anclas_fondo, t)
    escala = float(spec.get("escala", 1.0))
    aura = _valor(spec.get("aura", 0), t)
    pulso = (0.5 + 0.5 * math.sin(i * 0.55)) if spec.get("pulso", aura > 0) else 0.0
    espejo = bool(spec.get("espejo", False))
    rot = float(spec.get("rot", 0))
    cara_pieza = cara if cara.startswith("cara_") else "cara_" + cara
    punto = m.pegar(im, personaje, cuerpo, cara, x, y, escala=escala, rng=rng,
                    rot=rot, espejo=espejo, aura=aura, pulso=pulso)
    cajas = []
    for p in _lista(spec.get("prop")):
        cajas.append(_prop_en_mano(m, im, personaje, cuerpo, p, x, y, escala, rng, i))
    cajas.append(_caja_cabeza(m, personaje, cuerpo, cara_pieza, punto, escala, rot, espejo))
    return punto, cajas


def _prop_en_mano(m, im, personaje, cuerpo, spec, x, y, escala, rng, i):
    """Una pieza ilustrada de utilería, colgada de un ancla del cuerpo, con su escala_rel."""
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
    d = ImageDraw.Draw(im)
    t = i / max(1, n - 1)
    caras = []
    anclas_fondo = {}
    ancla_pipo = None

    if cuadro.get("zoom"):
        caras += _zoom(m, im, d, cuadro["zoom"], i, n, t, rng)
    else:
        fn = FONDOS.get(cuadro.get("fondo", "ninguno"), FONDOS["ninguno"])
        anclas_fondo = fn(d, rng, desp, "atras") or {}
        for sec in _lista(cuadro.get("secundarios")):
            sx, sy = _posicion(sec, anclas_fondo, t)
            se = float(sec.get("escala", 1.9))
            secundario(d, sx, sy, rng, tipo=sec.get("tipo", "abuela"), escala=se)
            caras.append((sx - 48 * se, sy - 58 * se, sx + 48 * se, sy + 56 * se))
        fn(d, rng, desp, "delante")
        caras += _props_sueltos(d, cuadro, anclas_fondo, t, rng, delante=False)
        for quien in ("teo", "pipo"):
            spec = cuadro.get(quien)
            if not spec:
                continue
            punto, cajas = pegar_personaje(m, im, d, quien, spec, i, n, t, rng, anclas_fondo)
            caras += cajas
            if quien == "pipo":
                caja = cajas[-1]                       # la última es la cabeza
                ancla_pipo = ((caja[0] + caja[2]) / 2, caja[1] + 0.25 * (caja[3] - caja[1]))
        caras += _props_sueltos(d, cuadro, anclas_fondo, t, rng, delante=True)

    if cuadro.get("anillos"):                        # la respiración de la escena de la magia
        _anillos(d, m, cuadro, i, rng)

    texto = cuadro.get("pipo_dice")
    if texto and i >= 1:
        if ancla_pipo is None:                       # Pipo no está en el cuadro: asoma por un borde
            ancla_pipo, caja = _pipo_asoma(m, im, cuadro, rng)
            caras.append(caja)
        globo(d, texto, ancla_pipo, rng, evitar=caras)
    return im


def _props_sueltos(d, cuadro, anclas_fondo, t, rng, delante):
    """Dibuja los props sueltos de la capa pedida. Devuelve las cajas que el globo tiene que
    esquivar (hoy, la burbuja de pensamiento: es lo único que ocupa media hoja)."""
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


def _pipo_asoma(m, im, cuadro, rng):
    """Pipo no está en el cuadro pero habla: se pega su cabeza sola asomando por un borde."""
    spec = cuadro.get("pipo_asoma") or {}
    lado = spec.get("lado", "derecha")
    cara = "cara_" + spec.get("cara", CARAS_ASOMA.get(cuadro.get("escena"), "alegria_sarcastica"))
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

TEXTOS_MAGIA = {"enciende": "algo se enciende.", "medita": "por suerte descubrió la Pausa.",
                "pasea": "por suerte descubrió la Pausa.", "escribe": "escribió lo que importa.",
                "final": "y se le nota."}
TEO_MAGIA = 1.6


def cuadros_magia(esc):
    """Expande la escena `magia` en sus cuadros. Los tres huecos: accion, burbuja, final."""
    accion = esc.get("accion", "medita")
    if accion not in ("medita", "pasea"):
        raise SystemExit("la escena magia acepta accion: medita | pasea (llegó %r)" % accion)
    burbuja = esc.get("burbuja", "abuelos")
    if burbuja not in DIBUJOS:
        raise SystemExit("dibujo de burbuja desconocido: %s (hay: %s)" % (burbuja, ", ".join(DIBUJOS)))
    fin = esc.get("final") or {}
    txt = dict(TEXTOS_MAGIA, **(esc.get("textos") or {}))
    fondo1 = esc.get("fondo", "rincon")
    teo = {"x": 420, "y": 1100, "escala": TEO_MAGIA}
    pipo = {"cuerpo": "sentado", "x": 890, "y": 1300, "escala": 0.58}

    # momento 1 · el teléfono se enciende (fijo): el rincón → la hoja "acerca" → se endereza
    c = [{"hojas": 9, "fondo": fondo1,
          "teo": dict(teo, cuerpo="sentado", cara="abajo_plana",
                      prop={"nombre": "telefono_0", "dx": 12, "dy": -34, "rot": -24}),
          "pipo": dict(pipo, cara="en_serio"),
          "props": [{"nombre": "nube_garabatos", "x": 600, "y": 530, "escala": 2.0,
                     "disolucion": 0.0, "hacia_disolucion": 0.45}]},
         {"hojas": 7, "zoom": {"pieza": "props/telefono_1", "escala": 2.7, "rot": -12, "manos": True,
                               "ciclo": ["telefono_1", "telefono_2", "telefono_3", "telefono_2"]},
          "pipo_dice": txt["enciende"], "pipo_asoma": {"lado": "izquierda", "cara": "en_serio"}},
         {"hojas": 14, "fondo": fondo1,
          "teo": dict(teo, cuerpo="sentado_erguido", cara="frente_sonrisa",
                      prop={"ciclo": ["telefono_2", "telefono_3"], "nombre": "telefono_3", "dx": 12, "dy": -34, "rot": -24}),
          "pipo": dict(pipo, cara="en_serio"),
          "props": [{"nombre": "nube_garabatos", "x": 600, "y": 530, "escala": 2.0,
                     "disolucion": 0.45, "hacia_disolucion": 1.0}],
          "pipo_dice": txt["enciende"]}]

    # momento 2 · la pequeña acción, cargando el aura (hueco 1: medita | pasea)
    if accion == "medita":
        c.append({"hojas": 26, "fondo": esc.get("fondo_accion", "rincon"), "anillos": True,
                  "teo": dict(teo, cuerpo="medita", x=430, y=1180, aura="sube", pulso=True,
                              cara="cerrada_sonrisa"),
                  "pipo": dict(pipo, cara="orgullo"),
                  "pipo_dice": txt["medita"]})
    else:
        c.append({"hojas": 26, "fondo": esc.get("fondo_accion", "calle"), "parallax": 26,
                  "teo": dict(teo, cuerpo="camina", ciclo=True, cara="costado_sonrisa", x=400, y=1120,
                              aura="sube", pulso=True),
                  "pipo": {"cuerpo": "camina", "ciclo": True, "fase": 2, "cara": "orgullo",
                           "x": 790, "y": 1290, "escala": 0.7},
                  "pipo_dice": txt["pasea"]})

    # momento 3 · escribe: la burbuja es el descubrimiento del volumen (hueco 2)
    c.append({"hojas": 26, "fondo": "banco_plaza",
              "teo": dict(teo, cuerpo="sentado_erguido", cara="abajo_sonrisa", x=330, y=1090,
                          prop={"nombre": "cuadernito_0", "ciclo": ["cuadernito_0", "cuadernito_1", "cuadernito_2", "cuadernito_3"],
                                "dx": 30, "dy": -10, "rot": -10}),
              "pipo": dict(pipo, cara="orgullo"),
              "props": [{"nombre": "burbuja_pensamiento", "x": 740, "y": 430, "escala": 0.9,
                         "dibujo": burbuja, "punta": (370, 610), "delante": True}],
              "pipo_dice": txt["escribe"]})

    # momento 4 · la acción con el aura desplegada (hueco 3: lo que cambia por volumen)
    ultimo = {"hojas": 26, "fondo": fin.get("fondo", "mesa_familiar"),
              "teo": dict(teo, cuerpo="sentado_erguido", cara="costado_sonrisa", x=400, y=1100, aura=1.0, pulso=True),
              "pipo": {"cuerpo": "sentado", "cara": "orgullo", "x": 185, "y": 1345, "escala": 0.55},
              "secundarios": fin.get("secundarios", [{"tipo": "abuela", "x": 720, "y": 900},
                                                     {"tipo": "abuelo", "x": 920, "y": 890}]),
              "pipo_dice": fin.get("pipo_dice", txt["final"])}
    for clave in ("teo", "pipo", "props", "hojas"):
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


def aplanar(g):
    """Convierte el guion en una lista plana de cuadros, cada uno con sus hojas."""
    fuera = []
    for esc in g["escenas"]:
        tipo = esc.get("tipo", "problema")
        if tipo == "magia":
            cuadros = cuadros_magia(esc)
        else:
            cuadros = list(esc.get("cuadros") or [])
            if not cuadros:
                raise SystemExit("la escena %r no tiene cuadros" % tipo)
        for k, c in enumerate(cuadros):
            c = dict(c)
            c.setdefault("fondo", esc.get("fondo", "ninguno"))
            c.setdefault("parallax", esc.get("parallax", 0))
            c["escena"] = tipo
            if "duracion" in c:
                c["hojas"] = max(1, int(round(float(c["duracion"]) * HOJAS_POR_SEG)))
            c["hojas"] = int(c.get("hojas", 10))
            if c["fondo"] not in FONDOS:
                raise SystemExit("fondo desconocido: %s (hay: %s)" % (c["fondo"], ", ".join(sorted(FONDOS))))
            fuera.append(c)
    return fuera


# ---------------------------------------------------------------- B2 · el cartel de apertura

def imagen_cartel(im, m, rng, cx, cy, r):
    """Provisorio: Teo y Pipo trotando dentro de un círculo crema, con las piezas que hay.
    B1 (capa de detalle) va a reemplazar el cuerpo de esta función por un PNG ilustrado
    a lo Tintín; el círculo, el tamaño y el centro se quedan como están."""
    d = ImageDraw.Draw(im)
    R.circle(d, cx, cy, r, rng, width=9, color=R.UMBER, fill=R.CREAM)
    m.pegar(im, "teo", "camina_1", "cara_costado_sonrisa", cx - 85, cy + 40, escala=1.12, rng=rng)
    m.pegar(im, "pipo", "camina_2", "cara_alegria_sarcastica", cx + 140, cy + 175, escala=0.62, rng=rng)


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
    imagen_cartel(im, m, rng, R.W / 2, 1030, 340)
    d = ImageDraw.Draw(im)
    titulo = str(g.get("titulo", "SIN TÍTULO")).upper()
    d.text((R.W / 2, 1480), "en", fill=R.IVORY, font=R.font(52), anchor="mm")
    d.text((R.W / 2, 1600), titulo, fill=R.IVORY, font=font_que_entra(d, titulo, 900, 120), anchor="mm")
    d.text((R.W / 2, 1740), "Vol. %s" % g.get("volumen", 0), fill=mezcla(tinta, R.CREAM, 0.75),
           font=R.font(54), anchor="mm")
    return im


# ---------------------------------------------------------------- C · el cierre fijo

TEXTOS_CONTRATAPA = ["Teo y Pipo volverán", "próximamente",
                     "Dwellia", "una Pausa al día, fuera del teléfono", "link en la bio"]


CARA_CIERRE, ESC_CIERRE, POS_CIERRE, PIVOTE_CIERRE = "cara_alegria_sarcastica", 2.15, (R.W / 2, 1010), (200, 210)


def hoja_pipo_camara(m, i, n, rng):
    """C1: Pipo a cámara, cabeza grande, alegría sarcástica."""
    im = R.paper(rng)
    m.solo(im, "pipo", CARA_CIERRE, POS_CIERRE[0], POS_CIERRE[1], escala=ESC_CIERRE, rng=rng, pivote=PIVOTE_CIERRE)
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


def contratapa(rng):
    """C3: hoja salvia. Primero y GRANDE "Teo y Pipo volverán próximamente"; abajo y más chico el
    bloque de Dwellia con el ícono de la app (WS34, orden invertido por Tomás). Fija para todos los volúmenes."""
    im = R.paper(rng, base=R.SAGE_DEEP)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((80, 120, R.W - 80, R.H - 120), 30, outline=mezcla(R.SAGE_DEEP, R.CREAM, 0.45), width=5)
    d.text((R.W / 2, 560), TEXTOS_CONTRATAPA[0], fill=R.IVORY, font=font_que_entra(d, TEXTOS_CONTRATAPA[0], 880, 108, condensada=False), anchor="mm")
    d.text((R.W / 2, 690), TEXTOS_CONTRATAPA[1], fill=R.IVORY, font=font_que_entra(d, TEXTOS_CONTRATAPA[1], 880, 108, condensada=False), anchor="mm")
    R.stroke(d, [(400, 840), (680, 840)], rng, width=4, color=mezcla(R.SAGE_DEEP, R.CREAM, 0.5), amp=1.2)
    icono_dwellia(im, R.W / 2, 1110, 200)
    d = ImageDraw.Draw(im)
    d.text((R.W / 2, 1300), TEXTOS_CONTRATAPA[2], fill=R.IVORY, font=R.font(84, bold=True), anchor="mm")
    d.text((R.W / 2, 1385), TEXTOS_CONTRATAPA[3], fill=R.CREAM, font=R.font(40), anchor="mm")
    d.text((R.W / 2, 1660), TEXTOS_CONTRATAPA[4], fill=mezcla(R.SAGE_DEEP, R.CREAM, 0.78), font=R.font(38), anchor="mm")
    return im


# ---------------------------------------------------------------- el render

def render(ruta_guion, solo_cuadros=False):
    g = cargar(ruta_guion)
    nombre = g.get("nombre") or os.path.splitext(os.path.basename(ruta_guion))[0]
    m = Marioneta()
    cuadros = aplanar(g)
    total_hojas = sum(c["hojas"] for c in cuadros) + HOJAS_CIERRE

    pruebas = os.path.join(RAIZ, "pruebas")
    os.makedirs(pruebas, exist_ok=True)
    png = os.path.join(pruebas, "%s_cuadros.png" % nombre)
    hoja_de_cuadros(g, m, cuadros, total_hojas).save(png)
    print("cuadros ->", png)
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

    # el cartel (2 s, sin pasar página)
    seg_cartel = float((g.get("cartel") or {}).get("duracion", 2.0))
    n_cartel = max(1, int(seg_cartel * HOJAS_POR_SEG))
    previo = None
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
            emitir(R.page_turn(previo, im, 0.5), 1)
            emitir(im, R.HOLD - 1)
            previo = im
            desp += float(c.get("parallax", 0) or 0)

    # el cierre fijo
    for i in range(N_PIPO):
        pagina += 1
        rng = random.Random(pagina)
        im = R.chrome(hoja_pipo_camara(m, i, N_PIPO, rng), pagina, total_hojas, rng)
        emitir(R.page_turn(previo, im, 0.5), 1)
        emitir(im, R.HOLD - 1)
        previo = im
    cx, cy = centro_cierre(m)
    for im in frames_iris(previo, cx, cy, int(1.5 * R.FPS)):
        emitir(im, 1)
    tapa = contratapa(random.Random(77))
    cerrado = Image.new("RGB", (R.W, R.H), R.UMBER)          # el iris terminó en tinta tierra
    for i in range(R.FPS):
        emitir(R.close_book(cerrado, tapa, (i + 1) / R.FPS), 1)
    for i in range(int(3.0 * HOJAS_POR_SEG)):
        emitir(contratapa(random.Random(7000 + i)), R.HOLD)

    salida = os.path.join(pruebas, "%s.mp4" % nombre)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(R.FPS),
                    "-i", os.path.join(frames, "f%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "20", "-movflags", "+faststart", salida], check=True)
    print("hojas:", total_hojas, "cuadros de video:", k[0], "seg:", round(k[0] / R.FPS, 1), "->", salida)


N_PIPO = 6                                   # hojas del Pipo a cámara del cierre (0,6 s)
HOJAS_CIERRE = N_PIPO


def hoja_de_cuadros(g, m, cuadros, total_hojas, columnas=6, escala=0.30):
    """La hoja fija: un cuadro clave de cada cuadro del guion (más el cartel y el cierre),
    para revisar la lectura sin abrir el video."""
    piezas = [("cartel", cartel(g, m, 0, 1, random.Random(9000)))]
    pagina = 0
    for k, c in enumerate(cuadros):
        n = c["hojas"]
        i = int(n * 0.72)
        pagina += n
        rng = random.Random(pagina)
        piezas.append(("%d · %s" % (k + 1, c["escena"]), R.chrome(hoja_de(m, c, i, n, rng, 0.0), pagina, total_hojas, rng)))
    piezas.append(("cierre", R.chrome(hoja_pipo_camara(m, 0, N_PIPO, random.Random(5)), total_hojas, total_hojas, random.Random(5))))
    piezas.append(("contratapa", contratapa(random.Random(77))))

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

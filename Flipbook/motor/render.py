"""Boceto v1 (iteración 3): personaje inspirado en las fotos de referencia + historia abstracta.

Personaje (ficticio): pelo ondulado con volumen hacia un lado (3 bucles), cara alargada,
barba de pocos días (puntitos), anteojos de sol apoyados sobre el pelo (su prop fijo),
cuerpo delgado. Perro: un pug (cuerpo redondo, máscara negra sólida, orejas negras plegadas,
ojos grandes, cola enrulada, collar salvia = el acento de color).

Historia vol. 1 (concepto de Tomás, sin carta):
  1. lunes: encorvado sobre el teléfono, nube de garabatos
  2. toma algo parecido a un teléfono; se ilumina de verde; los garabatos se disuelven
  3. la actividad: sale a caminar con el pug
  4. escribe: sentado en un banco, cuadernito, el pug al lado
  5. el aura: camina erguido, con un halo salvia, y saluda a alguien que pasa
"""
import math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

# Personajes con marioneta en este motor (lo lee inventario.py)
PERSONAJES = ["teo", "pipo"]

W, H = 1080, 1920
FPS = 30
HOLD = 3
OUT = sys.argv[1] if len(sys.argv) > 1 else "flipbook_v3.mp4"
SHEET = sys.argv[2] if len(sys.argv) > 2 else "hoja_de_personajes.png"

CREAM = (247, 241, 231); SAND = (222, 211, 190); IVORY = (255, 248, 234); OAT = (239, 227, 208)
UMBER = (47, 41, 35); TAUPE = (117, 107, 94); DUST = (154, 143, 128)
LINE = (216, 203, 184); SAGE = (143, 165, 138); SAGE_DEEP = (111, 138, 105); SAGE_LIGHT = (200, 214, 196)
COVER = (196, 178, 150)

def font(size, bold=False):
    for p in ["/System/Library/Fonts/Supplemental/Georgia%s.ttf" % (" Bold" if bold else ""),
              "/System/Library/Fonts/Supplemental/Times New Roman.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def paper(rng, base=CREAM, size=(W, H)):
    w, h = size
    im = Image.new("RGB", (w, h), base)
    noise = Image.effect_noise((max(1, w // 4), max(1, h // 4)), 18).resize((w, h)).convert("L")
    grain = Image.new("RGB", (w, h), tuple(max(0, c - 12) for c in base))
    return Image.composite(grain, im, noise.point(lambda v: max(0, v - 118)))

def wobble(pts, rng, amp=2.2):
    return [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in pts]

def stroke(d, pts, rng, width=7, color=UMBER, amp=2.2):
    pts = wobble(pts, rng, amp)
    d.line(pts, fill=color, width=width, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=color)

def arc_pts(cx, cy, rx, ry, a0, a1, n=14):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]

def circle(d, cx, cy, r, rng, width=7, color=UMBER, fill=None, amp=1.5, ry=None):
    ry = ry or r
    pts = [(cx + r * math.cos(a) + rng.uniform(-amp, amp), cy + ry * math.sin(a) + rng.uniform(-amp, amp))
           for a in [i * 2 * math.pi / 40 for i in range(41)]]
    if fill:
        d.polygon(pts, fill=fill)
    if width:
        d.line(pts, fill=color, width=width, joint="curve")

def scribble(d, cx, cy, rng, r=70, color=TAUPE, width=4):
    pts = [(cx + rng.uniform(-r, r), cy + rng.uniform(-r * 0.6, r * 0.6)) for _ in range(18)]
    d.line(pts, fill=color, width=width, joint="curve")

def leaf(d, cx, cy, rng, s=1.0):
    pts = [(cx, cy - 60 * s), (cx + 40 * s, cy - 20 * s), (cx, cy + 40 * s), (cx - 40 * s, cy - 20 * s), (cx, cy - 60 * s)]
    pts = wobble(pts, rng, 2)
    d.polygon(pts, fill=SAGE_LIGHT)
    d.line(pts, fill=SAGE_DEEP, width=6, joint="curve")
    stroke(d, [(cx, cy - 55 * s), (cx, cy + 35 * s)], rng, width=4, color=SAGE_DEEP)

# ---------------- el personaje ----------------

def head(d, x, y, rng, look="front", mood="flat", s=1.0):
    """Cara alargada, pelo con volumen hacia la derecha, anteojos de sol sobre el pelo, barba de puntitos."""
    rx, ry = 40 * s, 52 * s
    circle(d, x, y, rx, rng, ry=ry, fill=CREAM)
    # pelo: masa ondulada que sube y se va a la derecha (3 bucles)
    hair = [(x - rx, y - 10 * s)]
    hair += arc_pts(x - 22 * s, y - 52 * s, 24 * s, 26 * s, math.pi, 1.75 * math.pi, 6)
    hair += arc_pts(x + 12 * s, y - 66 * s, 26 * s, 24 * s, math.pi * 1.05, 1.9 * math.pi, 6)
    hair += arc_pts(x + 44 * s, y - 52 * s, 22 * s, 22 * s, math.pi * 1.15, 2.05 * math.pi, 6)
    hair += [(x + rx + 4 * s, y - 20 * s)]
    pts = wobble(hair, rng, 2)
    d.polygon(pts + [(x + rx, y - 14 * s), (x - rx, y - 14 * s)], fill=(214, 200, 176))
    d.line(pts, fill=UMBER, width=int(6 * s), joint="curve")
    # anteojos de sol apoyados en el pelo (el prop fijo)
    gx, gy = x - 6 * s, y - 44 * s
    d.rounded_rectangle((gx - 30 * s, gy - 9 * s, gx - 4 * s, gy + 7 * s), 5 * s, fill=UMBER)
    d.rounded_rectangle((gx + 4 * s, gy - 9 * s, gx + 30 * s, gy + 7 * s), 5 * s, fill=UMBER)
    d.line((gx - 4 * s, gy - 2 * s, gx + 4 * s, gy - 2 * s), fill=UMBER, width=int(3 * s))
    # ojos según la mirada
    ex = {"down": 10, "front": 14, "up": 12, "side": 20}[look] * s
    ey = {"down": 10, "front": 0, "up": -8, "side": 0}[look] * s
    for dx in (-14 * s, 14 * s):
        d.ellipse((x + dx + ex * 0.4 - 3.5 * s, y + ey - 3.5 * s, x + dx + ex * 0.4 + 3.5 * s, y + ey + 3.5 * s), fill=UMBER)
    # boca: plana / sonrisa
    if mood == "smile":
        d.line(wobble(arc_pts(x + 4 * s, y + 22 * s, 14 * s, 8 * s, 0.15 * math.pi, 0.85 * math.pi, 6), rng, 1), fill=UMBER, width=int(4 * s), joint="curve")
    else:
        stroke(d, [(x - 6 * s, y + 26 * s), (x + 12 * s, y + 26 * s)], rng, width=int(4 * s), amp=1)
    # barba de pocos días: puntitos en mandíbula
    for k in range(14):
        a = 0.25 * math.pi + k * 0.5 * math.pi / 13
        px, py = x + (rx - 6 * s) * math.cos(a), y + (ry - 8 * s) * math.sin(a)
        d.ellipse((px - 1.5 * s, py - 1.5 * s, px + 1.5 * s, py + 1.5 * s), fill=TAUPE)

def body_walk(d, x, y, t, rng, upright=0.4, s=1.0, mood="flat", look="front"):
    """Cuerpo delgado caminando. upright 0 = encorvado, 1 = erguido. Devuelve la mano delantera."""
    sw = math.sin(t * 2 * math.pi)
    y = y - 6 * s * abs(math.cos(t * 2 * math.pi))
    lean = (1 - upright) * 40 * s
    hx, hy = x + lean, y - 262 * s + (1 - upright) * 20 * s
    head(d, hx, hy, rng, look=look, mood=mood, s=s)
    neck = (hx - 4 * s, hy + 50 * s)
    hip = (x + 10 * s, y - 70 * s)
    stroke(d, [neck, hip], rng, width=int(8 * s))
    stroke(d, [hip, (hip[0] + 55 * sw * s, y + 15 * s), (hip[0] + 10 * s + 70 * sw * s, y + 90 * s)], rng, width=int(7 * s))
    stroke(d, [hip, (hip[0] - 55 * sw * s, y + 15 * s), (hip[0] + 10 * s - 70 * sw * s, y + 90 * s)], rng, width=int(7 * s))
    sh = (neck[0] + 2 * s, neck[1] + 30 * s)
    stroke(d, [sh, (sh[0] - 45 * sw * s, sh[1] + 70 * s), (sh[0] - 60 * sw * s, sh[1] + 130 * s)], rng, width=int(6 * s))
    hand = (sh[0] + 110 * s, sh[1] + 95 * s)
    stroke(d, [sh, (sh[0] + 60 * s, sh[1] + 50 * s), hand], rng, width=int(6 * s))
    return hand

def body_sit(d, x, y, rng, hunch=1.0, look="down", mood="flat", s=1.0):
    """Sentado; devuelve dónde están las manos (para el objeto o el cuadernito)."""
    hx = x + 70 * hunch * s
    hy = y - 240 * s + 45 * hunch * s
    head(d, hx, hy, rng, look=look, mood=mood, s=s)
    neck = (hx - 6 * s, hy + 50 * s)
    stroke(d, [(x, y - 70 * s), (x + 10 * hunch * s, y - 150 * s), neck], rng, width=int(8 * s))
    stroke(d, [(x, y - 70 * s), (x + 95 * s, y - 70 * s), (x + 95 * s, y + 40 * s)], rng, width=int(7 * s))
    hands = (x + 150 * s, y - 130 * s + 25 * hunch * s)
    sh = (neck[0] + 2 * s, neck[1] + 28 * s)
    stroke(d, [sh, (sh[0] + 60 * s, sh[1] + 40 * s), hands], rng, width=int(6 * s))
    stroke(d, [sh, (sh[0] + 40 * s, sh[1] + 60 * s), (hands[0] - 10 * s, hands[1] + 12 * s)], rng, width=int(6 * s))
    return hands

# ---------------- el pug ----------------

def pug(d, x, y, t, rng, sit=False, s=1.0, mood="flat"):
    """Pug: cuerpo redondo, cabeza grande, máscara negra, orejas plegadas negras, cola enrulada, collar salvia."""
    sw = 0 if sit else math.sin(t * 2 * math.pi + 0.8)
    hop = 0 if sit else 4 * s * abs(math.sin(t * 2 * math.pi))
    y = y - hop
    # patas (detrás del cuerpo)
    for k, dx in enumerate((-26, -12, 16, 30)):
        sgn = sw if k % 2 == 0 else -sw
        stroke(d, [(x + dx * s, y - 10 * s), (x + (dx + 16 * sgn) * s, y + 28 * s)], rng, width=int(7 * s))
    # cola enrulada
    d.line(wobble(arc_pts(x - 48 * s, y - 62 * s, 14 * s, 14 * s, 0.5 * math.pi, 2.3 * math.pi, 10), rng, 1.5), fill=UMBER, width=int(6 * s), joint="curve")
    # cuerpo
    circle(d, x, y - 40 * s, 50 * s, rng, ry=42 * s, fill=CREAM)
    # cabeza grande, un poco adelante y arriba
    hx, hy = x + 50 * s, y - 78 * s
    circle(d, hx, hy, 40 * s, rng, ry=36 * s, fill=CREAM)
    # collar salvia (acento)
    d.line(wobble(arc_pts(hx - 10 * s, hy + 26 * s, 34 * s, 12 * s, 0.1 * math.pi, 0.9 * math.pi, 6), rng, 1), fill=SAGE, width=int(8 * s), joint="curve")
    # orejas negras plegadas (sólidas)
    for ex in (-30, 22):
        pts = wobble([(hx + ex * s, hy - 30 * s), (hx + (ex + 18) * s, hy - 40 * s), (hx + (ex + 14) * s, hy - 8 * s)], rng, 1.5)
        d.polygon(pts, fill=UMBER)
    # máscara negra (hocico chato) con arrugas
    mx, my = hx + 12 * s, hy + 8 * s
    circle(d, mx, my, 22 * s, rng, width=0, ry=18 * s, fill=UMBER)
    d.line(wobble(arc_pts(hx - 2 * s, hy - 14 * s, 26 * s, 8 * s, 1.15 * math.pi, 1.85 * math.pi, 6), rng, 1), fill=TAUPE, width=int(3 * s), joint="curve")
    # ojos grandes y redondos, muy expresivos
    for ex in (-14, 22):
        d.ellipse((hx + ex * s - 9 * s, hy - 6 * s - 9 * s, hx + ex * s + 9 * s, hy - 6 * s + 9 * s), fill=IVORY, outline=UMBER, width=int(3 * s))
        d.ellipse((hx + ex * s - 4 * s, hy - 5 * s - 4 * s, hx + ex * s + 4 * s, hy - 5 * s + 4 * s), fill=UMBER)
    if mood == "smile":
        d.line(wobble(arc_pts(mx, my + 6 * s, 10 * s, 5 * s, 0.1 * math.pi, 0.9 * math.pi, 5), rng, 1), fill=IVORY, width=int(3 * s), joint="curve")
    return (hx - 10 * s, hy + 34 * s)   # donde engancha la correa (el collar)

# ---------------- escenas ----------------

def room(d, rng):
    stroke(d, [(120, 1300), (960, 1300)], rng, width=6, color=TAUPE)
    stroke(d, [(700, 520), (980, 520), (980, 860), (700, 860), (700, 520)], rng, width=5, color=LINE)
    stroke(d, [(840, 520), (840, 860)], rng, width=4, color=LINE)

def device(d, x, y, rng, glow=0.0, pulse=0.0):
    """Algo parecido a un teléfono. Con glow > 0 se enciende de verde y respira."""
    if glow > 0:
        for k in range(3):
            r = (70 + 55 * k) * glow + 25 * pulse
            circle(d, x, y, r, rng, width=3, color=SAGE_LIGHT, amp=3)
    fill = (SAGE_LIGHT if glow > 0.5 else OAT)
    d.rounded_rectangle((x - 30, y - 52, x + 30, y + 52), 10, fill=fill, outline=UMBER, width=5)
    if glow > 0.5:
        d.rounded_rectangle((x - 22, y - 42, x + 22, y + 42), 6, fill=SAGE)

def sc_monday(i, n, rng):
    im = paper(rng); d = ImageDraw.Draw(im); p = i / n
    room(d, rng)
    hands = body_sit(d, 330, 1300, rng, hunch=1.0)
    device(d, hands[0] + 10, hands[1] - 10, rng)
    scribble(d, 470, 930, rng)
    if p > 0.2:
        d.text((W / 2, 400), "lunes.", fill=UMBER, font=font(72), anchor="mm")
    return im

def sc_glow(i, n, rng):
    im = paper(rng); d = ImageDraw.Draw(im); p = i / n
    room(d, rng)
    hunch = 1.0 - 0.6 * p
    hands = body_sit(d, 330, 1300, rng, hunch=hunch, look="down" if p < 0.6 else "front")
    glow = min(1.0, p * 1.6)
    device(d, hands[0] + 10, hands[1] - 10, rng, glow=glow, pulse=abs(math.sin(i * 0.9)))
    # la nube de garabatos se disuelve
    if p < 0.7:
        scribble(d, 470, 930 - 60 * p, rng, r=70 * (1 - p / 0.7) + 8, color=TAUPE, width=4)
    if p > 0.45:
        d.text((W / 2, 400), "algo se enciende.", fill=SAGE_DEEP, font=font(64), anchor="mm")
    return im

def sc_walk(i, n, rng):
    im = paper(rng); d = ImageDraw.Draw(im); p = i / n
    circle(d, 820, 420, 90, rng, width=8, color=SAGE)
    stroke(d, [(k * 40, 1300 + 40 * math.sin(k / 6 + p * 2)) for k in range(0, 28)], rng, width=6, color=TAUPE, amp=1.5)
    for tx in ((1500 - p * 1500) % 1500 - 200, (2200 - p * 1500) % 1500 - 200):
        stroke(d, [(tx, 1290), (tx, 1130)], rng, width=6, color=LINE)
        circle(d, tx, 1080, 70, rng, width=6, color=LINE)
    t = (i * 0.12) % 1.0
    hand = body_walk(d, 360 + 40 * p, 1300, t, rng, upright=0.5)
    col = pug(d, 660 + 40 * p, 1300, t, rng)
    stroke(d, [hand, ((hand[0] + col[0]) / 2, (hand[1] + col[1]) / 2 + 50), col], rng, width=4, color=TAUPE)
    if p > 0.15:
        d.text((W / 2, 640), "salir un rato", fill=UMBER, font=font(64), anchor="mm")
    return im

def sc_write(i, n, rng):
    im = paper(rng); d = ImageDraw.Draw(im); p = i / n
    circle(d, 820, 420, 90, rng, width=8, color=SAGE)
    stroke(d, [(k * 40, 1300 + 40 * math.sin(k / 6 + 2)) for k in range(0, 28)], rng, width=6, color=TAUPE, amp=1.5)
    # banco
    stroke(d, [(200, 1180), (620, 1180)], rng, width=8, color=TAUPE)
    stroke(d, [(230, 1180), (230, 1300)], rng, width=6, color=TAUPE); stroke(d, [(590, 1180), (590, 1300)], rng, width=6, color=TAUPE)
    hands = body_sit(d, 300, 1180, rng, hunch=0.5, look="down", mood="smile" if p > 0.5 else "flat")
    # cuadernito y lápiz que avanza
    d.rounded_rectangle((hands[0] - 20, hands[1] - 30, hands[0] + 90, hands[1] + 40), 6, fill=IVORY, outline=UMBER, width=4)
    for k in range(3):
        L = max(0, min(1, p * 3.5 - k))
        if L > 0:
            stroke(d, [(hands[0] - 8, hands[1] - 16 + k * 16), (hands[0] - 8 + 80 * L, hands[1] - 16 + k * 16)], rng, width=3, color=TAUPE, amp=1)
    stroke(d, [(hands[0] - 8 + 80 * max(0, min(1, p * 3.5 - 2)), hands[1] + 16), (hands[0] + 20 + 80 * max(0, min(1, p * 3.5 - 2)), hands[1] - 20)], rng, width=5)
    pug(d, 720, 1300, 0, rng, sit=True, mood="smile" if p > 0.5 else "flat")
    if p > 0.2:
        d.text((W / 2, 640), "escribir un poco", fill=UMBER, font=font(64), anchor="mm")
    return im

def sc_aura(i, n, rng):
    im = paper(rng); d = ImageDraw.Draw(im); p = i / n
    circle(d, 820, 420, 90, rng, width=8, color=SAGE)
    for k in range(8):
        a = k * math.pi / 4
        stroke(d, [(820 + 120 * math.cos(a), 420 + 120 * math.sin(a)), (820 + 145 * math.cos(a), 420 + 145 * math.sin(a))], rng, width=5, color=SAGE)
    stroke(d, [(k * 40, 1300 + 40 * math.sin(k / 6 + 1)) for k in range(0, 28)], rng, width=6, color=TAUPE, amp=1.5)
    t = (i * 0.12) % 1.0
    x = 360 + 30 * p
    # el aura: halos salvia que respiran alrededor del personaje
    for k in range(3):
        r = 170 + 45 * k + 12 * math.sin(i * 0.8 + k)
        circle(d, x + 20, 1120, r, rng, width=3, color=SAGE_LIGHT, amp=3, ry=r * 1.35)
    hand = body_walk(d, x, 1300, t, rng, upright=1.0, mood="smile", look="side")
    col = pug(d, x + 300, 1300, t, rng, mood="smile")
    stroke(d, [hand, ((hand[0] + col[0]) / 2, (hand[1] + col[1]) / 2 + 50), col], rng, width=4, color=TAUPE)
    # alguien que pasa; el personaje saluda (brazo libre en alto) cuando ya está cerca
    ox = 1250 - 600 * p
    stroke(d, [(ox, 1300), (ox, 1090)], rng, width=7, color=TAUPE); circle(d, ox, 1050, 38, rng, width=6, color=TAUPE)
    if p > 0.45:
        stroke(d, [(x - 2, 1100), (x - 60, 1040), (x - 80, 960)], rng, width=6)          # saluda
        stroke(d, [(ox, 1120), (ox - 50, 1060), (ox - 60, 990)], rng, width=6, color=TAUPE)  # le devuelve el saludo
    if p > 0.6:
        d.text((W / 2, 1560), "fin del capítulo 1", fill=DUST, font=font(48), anchor="mm")
    return im

# ---------------- libro ----------------

def cover(i, n, rng):
    im = paper(rng, base=COVER); d = ImageDraw.Draw(im)
    d.rounded_rectangle((90, 130, W - 90, H - 130), 30, outline=UMBER, width=6)
    d.rounded_rectangle((110, 150, W - 110, H - 150), 22, outline=(120, 104, 84), width=2)
    d.text((W / 2, 330), "VOLUMEN 1", fill=UMBER, font=font(54), anchor="mm")
    stroke(d, [(360, 390), (720, 390)], rng, width=4, amp=1)
    d.text((W / 2, 490), "Lunes", fill=UMBER, font=font(120, bold=True), anchor="mm")
    circle(d, W / 2, 1060, 330, rng, width=8, fill=CREAM)
    hand = body_walk(d, W / 2 - 170, 1300, 0.15, rng, upright=0.8, mood="smile")
    col = pug(d, W / 2 + 140, 1300, 0.15, rng)
    stroke(d, [hand, ((hand[0] + col[0]) / 2, (hand[1] + col[1]) / 2 + 50), col], rng, width=4, color=TAUPE)
    d.text((W / 2, 1520), "un libro para hojear", fill=(120, 104, 84), font=font(44), anchor="mm")
    d.text((W / 2, H - 230), "capítulo 1", fill=(120, 104, 84), font=font(40), anchor="mm")
    return im

def back_cover(rng):
    im = paper(rng, base=COVER); d = ImageDraw.Draw(im)
    d.rounded_rectangle((90, 130, W - 90, H - 130), 30, outline=UMBER, width=6)
    leaf(d, W / 2, 860, rng, s=1.4)
    d.text((W / 2, 1020), "Dwellia", fill=UMBER, font=font(96, bold=True), anchor="mm")
    d.text((W / 2, 1105), "una Pausa al día, fuera del teléfono", fill=(120, 104, 84), font=font(40), anchor="mm")
    d.text((W / 2, 1300), "continúa en el volumen 2", fill=UMBER, font=font(44), anchor="mm")
    d.text((W / 2, H - 230), "impulsado por Dwellia · link en la bio", fill=(120, 104, 84), font=font(36), anchor="mm")
    return im

def thumb(d, lift=0):
    d.ellipse((W - 330, H - 190 - lift, W + 120, H + 190 - lift), fill=(226, 206, 184), outline=(205, 182, 158), width=4)
    d.ellipse((W - 200, H - 120 - lift, W + 60, H + 120 - lift), fill=(233, 214, 194))

def chrome(im, page, total, rng):
    d = ImageDraw.Draw(im)
    left = int(18 * (1 - page / total)) + 4
    for k in range(left):
        y = H - 40 - k * 3; d.line((60 + k * 2, y, W - 60 - k * 2, y), fill=LINE, width=2)
        x = W - 40 - k * 3; d.line((x, 60 + k * 2, x, H - 60 - k * 2), fill=LINE, width=2)
    d.text((W - 150, H - 130), str(page), fill=DUST, font=font(40), anchor="mm")
    thumb(d)
    return im.transform(im.size, Image.AFFINE, (1, 0, rng.randint(-3, 3), 0, 1, rng.randint(-3, 3)), fillcolor=CREAM)

def page_turn(prev, nxt, k):
    out = nxt.copy(); d = ImageDraw.Draw(out, "RGBA")
    s = int(260 + 900 * k)
    d.polygon([(W, H - s - 60), (W - s - 60, H), (W, H)], fill=(60, 50, 40, 40))
    mask = Image.new("L", (W, H), 255)
    ImageDraw.Draw(mask).polygon([(W, H - s), (W - s, H), (W, H)], fill=0)
    out.paste(prev, (0, 0), mask)
    d.polygon([(W, H - s), (W - s, H), (W - s * 0.55, H - s * 0.55)], fill=(252, 247, 238, 255))
    d.line([(W, H - s), (W - s * 0.55, H - s * 0.55), (W - s, H)], fill=(200, 188, 168, 255), width=3)
    thumb(d, lift=int(40 * k))
    return out

def close_book(last, back, k):
    out = last.copy(); d = ImageDraw.Draw(out, "RGBA")
    ease = 1 - (1 - k) ** 2
    x = int(W - W * ease)
    d.rectangle((max(0, x - 120), 0, x, H), fill=(60, 50, 40, int(90 * ease)))
    if W - x > 0:
        out.paste(back.resize((max(1, W - x), H)), (x, 0))
    return out

def model_sheet():
    """Hoja de personajes: el protagonista en 4 poses + el pug en 2, para decidir el diseño."""
    rng = random.Random(3)
    im = paper(rng, size=(2400, 1100)); d = ImageDraw.Draw(im)
    d.text((1200, 70), "Hoja de personajes · v1 (nombres por definir)", fill=UMBER, font=font(48), anchor="mm")
    head(d, 300, 330, rng, look="front", mood="smile", s=2.2); d.text((300, 640), "cara", fill=DUST, font=font(30), anchor="mm")
    body_sit(d, 600, 900, rng, hunch=1.0); d.text((720, 980), "encorvado (lunes)", fill=DUST, font=font(30), anchor="mm")
    body_walk(d, 1050, 900, 0.2, rng, upright=0.5); d.text((1080, 1020), "camina", fill=DUST, font=font(30), anchor="mm")
    body_walk(d, 1400, 900, 0.7, rng, upright=1.0, mood="smile", look="side"); d.text((1430, 1020), "erguido (aura)", fill=DUST, font=font(30), anchor="mm")
    pug(d, 1900, 560, 0.3, rng, s=1.8); d.text((1950, 700), "el pug, camina", fill=DUST, font=font(30), anchor="mm")
    pug(d, 1900, 980, 0, rng, sit=True, s=1.4, mood="smile"); d.text((1950, 1040), "sentado", fill=DUST, font=font(30), anchor="mm")
    im.save(SHEET)

def main():
    model_sheet()
    story = [(sc_monday, 2.6), (sc_glow, 3.4), (sc_walk, 4.4), (sc_write, 3.6), (sc_aura, 4.0)]
    frames_dir = os.path.join(os.path.dirname(os.path.abspath(OUT)), "frames_v3")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))
    k = [0]
    def emit(im, times=1):
        for _ in range(times):
            im.save(os.path.join(frames_dir, "f%05d.png" % k[0])); k[0] += 1
    total_pages = sum(int(sec * FPS / HOLD) for _, sec in story)
    for i in range(int(2.0 * FPS / HOLD)):
        emit(cover(i, 10, random.Random(1000 + i)), HOLD)
    prev = None; page = 0
    for fn, sec in story:
        n = int(sec * FPS / HOLD)
        for i in range(n):
            page += 1; rng = random.Random(page)
            im = chrome(fn(i, n, rng), page, total_pages, rng)
            emit(page_turn(prev if prev is not None else cover(0, 10, rng), im, 0.5), 1)
            emit(im, HOLD - 1)
            prev = im
    emit(prev, FPS // 2)
    back = back_cover(random.Random(7))
    for i in range(FPS):
        emit(close_book(prev, back, (i + 1) / FPS), 1)
    for i in range(int(3.0 * FPS / HOLD)):
        emit(back_cover(random.Random(7000 + i)), HOLD)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames_dir, "f%05d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", OUT], check=True)
    print("hojas:", total_pages, "cuadros:", k[0], "seg:", round(k[0] / FPS, 1), "->", OUT)

if __name__ == "__main__":
    main()

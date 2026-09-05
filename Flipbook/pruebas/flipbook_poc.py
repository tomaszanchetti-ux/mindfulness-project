"""Prueba de concepto: flipbook animado en vertical (1080x1920) con la paleta Dwellia.

Mecánica que se prueba:
  - dibujos a 10 "dibujos por segundo", cada dibujo se sostiene 3 cuadros (30 fps) -> ritmo de flipbook
  - "boil" de línea: cada dibujo se traza con un temblor propio (como redibujado a mano)
  - papel, número de página, taco de hojas al pie y pulgar fijo en la esquina
  - la hoja salta un poco al pasar (registro imperfecto), típico del flipbook
  - remate: la carta del día de Dwellia
"""
import math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FPS = 30
HOLD = 3                # cuadros por dibujo (30/3 = 10 dibujos por segundo)
SEG_WALK = 6.0          # segundos de historia
SEG_CARD = 2.5          # segundos de remate
OUT = sys.argv[1] if len(sys.argv) > 1 else "flipbook_poc.mp4"
APP = "/Users/tzanchetti/Documents/Proyectos Claudio/mindfulness-project/apps/web/public/assets/categorias"

CREAM = (247, 241, 231); SAND = (222, 211, 190); IVORY = (255, 248, 234)
UMBER = (47, 41, 35); TAUPE = (117, 107, 94); DUST = (154, 143, 128)
LINE = (216, 203, 184); SAGE = (143, 165, 138); SAGE_DEEP = (111, 138, 105)

def font(size, bold=False):
    for p in ["/System/Library/Fonts/Supplemental/Georgia%s.ttf" % (" Bold" if bold else ""),
              "/System/Library/Fonts/Supplemental/Times New Roman.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def paper(rng):
    """Hoja de papel con grano suave (una por dibujo, así el grano también 'vive')."""
    im = Image.new("RGB", (W, H), CREAM)
    noise = Image.effect_noise((W // 4, H // 4), 18).resize((W, H)).convert("L")
    grain = Image.new("RGB", (W, H), (235, 226, 210))
    im = Image.composite(grain, im, noise.point(lambda v: max(0, v - 118)))
    return im

def wobble(pts, rng, amp=2.2):
    return [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in pts]

def stroke(d, pts, rng, width=7, color=UMBER, amp=2.2):
    pts = wobble(pts, rng, amp)
    d.line(pts, fill=color, width=width, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=color)

def circle(d, cx, cy, r, rng, width=7, color=UMBER, fill=None):
    pts = [(cx + r * math.cos(a) + rng.uniform(-1.5, 1.5), cy + r * math.sin(a) + rng.uniform(-1.5, 1.5))
           for a in [i * 2 * math.pi / 40 for i in range(41)]]
    if fill:
        d.polygon(pts, fill=fill)
    d.line(pts, fill=color, width=width, joint="curve")

def person(d, x, y, t, rng):
    """Figura de línea caminando. t = fase del paso (0..1)."""
    sw = math.sin(t * 2 * math.pi)
    bob = 6 * abs(math.cos(t * 2 * math.pi))
    y = y - bob
    # cabeza
    circle(d, x, y - 250, 46, rng)
    # torso levemente inclinado hacia adelante
    stroke(d, [(x, y - 204), (x + 10, y - 60)], rng)
    # piernas
    stroke(d, [(x + 10, y - 60), (x + 10 + 55 * sw, y + 20), (x + 20 + 70 * sw, y + 90)], rng)
    stroke(d, [(x + 10, y - 60), (x + 10 - 55 * sw, y + 20), (x + 20 - 70 * sw, y + 90)], rng)
    # brazo libre balancea al revés
    stroke(d, [(x + 6, y - 170), (x + 6 - 45 * sw, y - 100), (x + 10 - 60 * sw, y - 40)], rng)
    # brazo con la correa, hacia adelante y abajo
    stroke(d, [(x + 6, y - 170), (x + 70, y - 120), (x + 120, y - 70)], rng)
    return (x + 120, y - 70)

def dog(d, x, y, t, rng):
    sw = math.sin(t * 2 * math.pi + 0.8)
    hop = 5 * abs(math.sin(t * 2 * math.pi))
    y = y - hop
    # cuerpo
    circle(d, x, y - 40, 44, rng)
    # cabeza
    circle(d, x + 62, y - 68, 28, rng)
    # oreja (salvia, el único acento de color)
    stroke(d, [(x + 70, y - 92), (x + 88, y - 60)], rng, width=9, color=SAGE)
    # patas
    for k, dx in enumerate((-22, -8, 14, 28)):
        s = sw if k % 2 == 0 else -sw
        stroke(d, [(x + dx, y - 6), (x + dx + 18 * s, y + 30)], rng, width=6)
    # cola
    stroke(d, [(x - 40, y - 56), (x - 66, y - 92 + 10 * sw)], rng, width=6)
    return (x + 62, y - 96)

def scene_walk(i, n, rng):
    """Dibujo i de n: persona y perro caminan por una colina suave; el cielo trae un sol en salvia."""
    im = paper(rng)
    d = ImageDraw.Draw(im)
    p = i / n
    # sol
    circle(d, 820, 420, 90, rng, width=8, color=SAGE, fill=None)
    # colina (línea de suelo con leve ondulación)
    ground = [(0 + k * 40, 1300 + 40 * math.sin(k / 6 + p * 2)) for k in range(0, 28)]
    stroke(d, ground, rng, width=6, color=TAUPE, amp=1.5)
    # dos árboles lejanos, entran de derecha a izquierda (parallax mínimo)
    for tx in ((1500 - p * 1500) % 1500, (2200 - p * 1500) % 1500 + 0):
        tx = tx - 200
        stroke(d, [(tx, 1290), (tx, 1130)], rng, width=6, color=TAUPE)
        circle(d, tx, 1080, 70, rng, width=6, color=TAUPE)
    # personaje: casi quieto en X (camina "en el lugar" mientras el fondo pasa)
    t = (i * 0.12) % 1.0
    px = 380 + 60 * p
    leash_from = person(d, px, 1300, t, rng)
    leash_to = dog(d, px + 260, 1300, t, rng)
    # correa combada
    mid = ((leash_from[0] + leash_to[0]) / 2, (leash_from[1] + leash_to[1]) / 2 + 40)
    stroke(d, [leash_from, mid, leash_to], rng, width=4, color=TAUPE)
    # texto en pantalla (sin voz): aparece en dos tiempos
    f = font(64)
    if p > 0.15:
        d.text((W / 2, 640), "salir un rato", fill=UMBER, font=f, anchor="mm")
    if p > 0.55:
        d.text((W / 2, 730), "sin el teléfono", fill=SAGE_DEEP, font=f, anchor="mm")
    return im

def scene_card(i, n, rng):
    """Remate: la carta del día sobre el mismo papel."""
    im = paper(rng)
    d = ImageDraw.Draw(im)
    p = min(1.0, i / max(1, n * 0.35))          # entra en el primer tercio
    ease = 1 - (1 - p) ** 3
    cw, ch = 720, 1040
    cx, cy = W / 2, 900 + (1 - ease) * 300
    x0, y0 = cx - cw / 2, cy - ch / 2
    d.rounded_rectangle((x0 + 10, y0 + 14, x0 + cw + 10, y0 + ch + 14), 34, fill=SAND)
    d.rounded_rectangle((x0, y0, x0 + cw, y0 + ch), 34, fill=(239, 230, 211), outline=LINE, width=3)
    # dibujo del pilar (asset real de la app)
    pil = Image.open(os.path.join(APP, "cat_calma.png")).convert("RGBA")
    pil.thumbnail((520, 400))
    im.paste(pil, (int(cx - pil.width / 2), int(y0 + 90)), pil)
    d.text((cx, y0 + 560), "Calma", fill=DUST, font=font(36), anchor="mm")
    for k, line in enumerate(("Da la vuelta a la manzana", "sin mirar la pantalla.")):
        d.text((cx, y0 + 660 + k * 74), line, fill=UMBER, font=font(54), anchor="mm")
    d.rounded_rectangle((cx - 190, y0 + ch - 150, cx + 190, y0 + ch - 70), 40, fill=SAGE)
    d.text((cx, y0 + ch - 110), "Tu carta de hoy", fill=IVORY, font=font(38), anchor="mm")
    if i > n * 0.5:
        d.text((cx, y0 + ch + 120), "Dwellia", fill=UMBER, font=font(92, bold=True), anchor="mm")
        d.text((cx, y0 + ch + 200), "una Pausa al día · link en la bio", fill=TAUPE, font=font(40), anchor="mm")
    return im

def flipbook_chrome(im, page, total, rng):
    """Lo que hace que se lea como flipbook: taco de hojas, número, pulgar, registro imperfecto."""
    d = ImageDraw.Draw(im)
    # taco de hojas al pie y a la derecha: se achica a medida que avanzan las páginas
    left = int(18 * (1 - page / total)) + 4
    for k in range(left):
        y = H - 40 - k * 3
        d.line((60 + k * 2, y, W - 60 - k * 2, y), fill=LINE, width=2)
        x = W - 40 - k * 3
        d.line((x, 60 + k * 2, x, H - 60 - k * 2), fill=LINE, width=2)
    # número de página, esquina inferior derecha como en el cuadernito
    d.text((W - 150, H - 130), str(page), fill=DUST, font=font(40), anchor="mm")
    # pulgar fijo (el que pasa las hojas) en la esquina inferior derecha
    d.ellipse((W - 330, H - 190, W + 120, H + 190), fill=(226, 206, 184), outline=(205, 182, 158), width=4)
    d.ellipse((W - 200, H - 120, W + 60, H + 120), fill=(233, 214, 194))
    # registro imperfecto: la hoja entera salta 1-3 px
    dx, dy = rng.randint(-3, 3), rng.randint(-3, 3)
    im = im.transform(im.size, Image.AFFINE, (1, 0, dx, 0, 1, dy), fillcolor=CREAM)
    return im

def main():
    n_walk = int(SEG_WALK * FPS / HOLD)
    n_card = int(SEG_CARD * FPS / HOLD)
    total = n_walk + n_card
    frames_dir = os.path.join(os.path.dirname(os.path.abspath(OUT)), "frames")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))
    k = 0
    for page in range(total):
        rng = random.Random(page)          # cada dibujo tiene su temblor propio, reproducible
        im = scene_walk(page, n_walk, rng) if page < n_walk else scene_card(page - n_walk, n_card, rng)
        im = flipbook_chrome(im, page + 1, total, rng)
        for _ in range(HOLD):
            im.save(os.path.join(frames_dir, "f%05d.png" % k)); k += 1
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames_dir, "f%05d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", OUT], check=True)
    print("dibujos:", total, "cuadros:", k, "->", OUT)

if __name__ == "__main__":
    main()

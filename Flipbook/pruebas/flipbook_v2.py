"""Boceto v1 del "libro de animación" Dwellia (vertical 1080x1920, 30 fps).

Estructura de libro:
  PORTADA (Volumen 1)  ->  HISTORIA en hojas de flipbook  ->  CIERRE (el libro se cierra, contratapa Dwellia)

Historia del capítulo 1 "El paseo" (personaje provisorio, de línea):
  1. lunes: encorvado sobre el teléfono, nube de garabatos sobre la cabeza
  2. del teléfono sale una carta de papel (el elemento mágico = Dwellia dentro de la historia)
  3. lee la carta y deja el teléfono
  4. sale a caminar con el perro
  5. se detiene, mira el sol; la nube de garabatos se volvió una hoja salvia
"""
import math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
HOLD = 3
OUT = sys.argv[1] if len(sys.argv) > 1 else "flipbook_v2.mp4"
APP = "/Users/tzanchetti/Documents/Proyectos Claudio/mindfulness-project/apps/web/public/assets/categorias"

CREAM = (247, 241, 231); SAND = (222, 211, 190); IVORY = (255, 248, 234); OAT = (239, 227, 208)
UMBER = (47, 41, 35); TAUPE = (117, 107, 94); DUST = (154, 143, 128)
LINE = (216, 203, 184); SAGE = (143, 165, 138); SAGE_DEEP = (111, 138, 105)
COVER = (196, 178, 150); COVER_DARK = (160, 142, 116)

def font(size, bold=False):
    for p in ["/System/Library/Fonts/Supplemental/Georgia%s.ttf" % (" Bold" if bold else ""),
              "/System/Library/Fonts/Supplemental/Times New Roman.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def paper(rng, base=CREAM):
    im = Image.new("RGB", (W, H), base)
    noise = Image.effect_noise((W // 4, H // 4), 18).resize((W, H)).convert("L")
    grain = Image.new("RGB", (W, H), tuple(max(0, c - 12) for c in base))
    return Image.composite(grain, im, noise.point(lambda v: max(0, v - 118)))

def wobble(pts, rng, amp=2.2):
    return [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in pts]

def stroke(d, pts, rng, width=7, color=UMBER, amp=2.2):
    pts = wobble(pts, rng, amp)
    d.line(pts, fill=color, width=width, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=color)

def circle(d, cx, cy, r, rng, width=7, color=UMBER, fill=None, amp=1.5):
    pts = [(cx + r * math.cos(a) + rng.uniform(-amp, amp), cy + r * math.sin(a) + rng.uniform(-amp, amp))
           for a in [i * 2 * math.pi / 40 for i in range(41)]]
    if fill:
        d.polygon(pts, fill=fill)
    d.line(pts, fill=color, width=width, joint="curve")

def scribble(d, cx, cy, rng, r=70, color=TAUPE):
    """Nube de garabatos: el ruido mental."""
    pts = [(cx + rng.uniform(-r, r), cy + rng.uniform(-r * 0.6, r * 0.6)) for _ in range(18)]
    d.line(pts, fill=color, width=4, joint="curve")

def leaf(d, cx, cy, rng, s=1.0):
    pts = [(cx, cy - 60 * s), (cx + 40 * s, cy - 20 * s), (cx, cy + 40 * s), (cx - 40 * s, cy - 20 * s), (cx, cy - 60 * s)]
    pts = wobble(pts, rng, 2)
    d.polygon(pts, fill=(200, 214, 196))
    d.line(pts, fill=SAGE_DEEP, width=6, joint="curve")
    stroke(d, [(cx, cy - 55 * s), (cx, cy + 35 * s)], rng, width=4, color=SAGE_DEEP)

def head(d, x, y, rng, look="down"):
    circle(d, x, y, 46, rng)
    # un rasgo fijo: mechón de pelo (para que se reconozca de hoja a hoja)
    stroke(d, [(x - 30, y - 38), (x - 8, y - 60), (x + 18, y - 42)], rng, width=6)
    # ojo: un punto, mira hacia donde toque
    ex, ey = {"down": (x + 18, y + 10), "front": (x + 22, y - 2), "up": (x + 20, y - 12)}[look]
    d.ellipse((ex - 4, ey - 4, ex + 4, ey + 4), fill=UMBER)

def dog(d, x, y, t, rng, sit=False):
    sw = 0 if sit else math.sin(t * 2 * math.pi + 0.8)
    hop = 0 if sit else 5 * abs(math.sin(t * 2 * math.pi))
    y = y - hop
    circle(d, x, y - 40, 44, rng)
    circle(d, x + 62, y - 68, 28, rng)
    stroke(d, [(x + 70, y - 92), (x + 88, y - 60)], rng, width=9, color=SAGE)  # oreja salvia = su rasgo
    for k, dx in enumerate((-22, -8, 14, 28)):
        s = sw if k % 2 == 0 else -sw
        stroke(d, [(x + dx, y - 6), (x + dx + 18 * s, y + 30)], rng, width=6)
    stroke(d, [(x - 40, y - 56), (x - 66, y - 92 + 10 * sw)], rng, width=6)
    return (x + 62, y - 96)

def person_walk(d, x, y, t, rng):
    sw = math.sin(t * 2 * math.pi)
    y = y - 6 * abs(math.cos(t * 2 * math.pi))
    head(d, x, y - 250, rng, look="front")
    stroke(d, [(x, y - 204), (x + 10, y - 60)], rng)
    stroke(d, [(x + 10, y - 60), (x + 10 + 55 * sw, y + 20), (x + 20 + 70 * sw, y + 90)], rng)
    stroke(d, [(x + 10, y - 60), (x + 10 - 55 * sw, y + 20), (x + 20 - 70 * sw, y + 90)], rng)
    stroke(d, [(x + 6, y - 170), (x + 6 - 45 * sw, y - 100), (x + 10 - 60 * sw, y - 40)], rng)
    stroke(d, [(x + 6, y - 170), (x + 70, y - 120), (x + 120, y - 70)], rng)
    return (x + 120, y - 70)

def person_sit(d, x, y, rng, hunch=1.0, look="down"):
    """Sentado, encorvado sobre el teléfono (hunch 1 = muy encorvado, 0 = erguido)."""
    hx = x + 60 * hunch
    hy = y - 230 + 40 * hunch
    head(d, hx, hy, rng, look=look)
    stroke(d, [(x, y - 190 + 30 * hunch), (hx - 10, hy + 50)], rng)          # espalda curva
    stroke(d, [(x, y - 190 + 30 * hunch), (x, y - 60)], rng)                 # cadera
    stroke(d, [(x, y - 60), (x + 90, y - 60), (x + 90, y + 40)], rng)         # piernas sentadas
    # brazos hacia el teléfono
    px, py = x + 130, y - 120 + 30 * hunch
    stroke(d, [(x + 4, y - 150), (px - 20, py)], rng)
    return (px, py)

def phone(d, x, y, rng, glow=0.0):
    if glow > 0:
        r = 80 + 60 * glow
        circle(d, x, y, r, rng, width=4, color=(200, 214, 196), amp=3)
    d.rounded_rectangle((x - 28, y - 50, x + 28, y + 50), 10, fill=OAT, outline=UMBER, width=5)

def card(d, im, cx, cy, s, rng, angle=0.0):
    """La carta de Dwellia: papel, dibujo del pilar, una frase. s = escala."""
    cw, ch = 300 * s, 430 * s
    layer = Image.new("RGBA", (int(cw + 40), int(ch + 40)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((20, 20, 20 + cw, 20 + ch), 16 * s, fill=(239, 230, 211, 255), outline=UMBER, width=max(2, int(4 * s)))
    pil = Image.open(os.path.join(APP, "cat_calma.png")).convert("RGBA")
    pil.thumbnail((int(cw * 0.7), int(ch * 0.4)))
    layer.paste(pil, (int(20 + cw / 2 - pil.width / 2), int(20 + ch * 0.1)), pil)
    if s > 0.6:
        f = font(int(30 * s))
        for k, line in enumerate(("Da la vuelta", "a la manzana", "sin mirar", "la pantalla.")):
            ld.text((20 + cw / 2, 20 + ch * 0.58 + k * 34 * s), line, fill=UMBER, font=f, anchor="mm")
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    im.paste(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)), layer)

def room(d, rng):
    """Interior mínimo: mesa y ventana."""
    stroke(d, [(120, 1300), (960, 1300)], rng, width=6, color=TAUPE)          # mesa/suelo
    stroke(d, [(700, 520), (980, 520), (980, 860), (700, 860), (700, 520)], rng, width=5, color=LINE)  # ventana
    stroke(d, [(840, 520), (840, 860)], rng, width=4, color=LINE)

# ---------------- escenas ----------------

def sc_monday(i, n, rng):
    im = paper(rng); d = ImageDraw.Draw(im); p = i / n
    room(d, rng)
    px, py = person_sit(d, 330, 1300, rng, hunch=1.0)
    phone(d, px, py, rng)
    scribble(d, 430, 940, rng)
    if p > 0.2:
        d.text((W / 2, 400), "lunes.", fill=UMBER, font=font(72), anchor="mm")
    return im

def sc_card_out(i, n, rng):
    im = paper(rng); d = ImageDraw.Draw(im); p = i / n
    room(d, rng)
    px, py = person_sit(d, 330, 1300, rng, hunch=1.0 - 0.5 * p, look="down" if p < 0.5 else "front")
    phone(d, px, py, rng, glow=min(1.0, p * 2))
    ease = 1 - (1 - p) ** 2
    card(d, im, px + 60 * ease, py - 40 - 320 * ease, 0.35 + 0.65 * ease, rng, angle=-8 + 8 * ease)
    if p > 0.5:
        d.text((W / 2, 400), "una carta.", fill=SAGE_DEEP, font=font(72), anchor="mm")
    return im

def sc_read(i, n, rng):
    im = paper(rng); d = ImageDraw.Draw(im); p = i / n
    room(d, rng)
    px, py = person_sit(d, 330, 1300, rng, hunch=0.3, look="up")
    phone(d, 560, 1250, rng)                          # el teléfono quedó en la mesa
    card(d, im, 560, 820, 1.0, rng)
    if p > 0.4:
        d.text((W / 2, 400), "el teléfono se queda.", fill=UMBER, font=font(64), anchor="mm")
    return im

def sc_walk(i, n, rng):
    im = paper(rng); d = ImageDraw.Draw(im); p = i / n
    circle(d, 820, 420, 90, rng, width=8, color=SAGE)
    ground = [(k * 40, 1300 + 40 * math.sin(k / 6 + p * 2)) for k in range(0, 28)]
    stroke(d, ground, rng, width=6, color=TAUPE, amp=1.5)
    for tx in ((1500 - p * 1500) % 1500 - 200, (2200 - p * 1500) % 1500 - 200):
        stroke(d, [(tx, 1290), (tx, 1130)], rng, width=6, color=LINE)
        circle(d, tx, 1080, 70, rng, width=6, color=LINE)
    t = (i * 0.12) % 1.0
    a = person_walk(d, 380 + 60 * p, 1300, t, rng)
    b = dog(d, 640 + 60 * p, 1300, t, rng)
    stroke(d, [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 40), b], rng, width=4, color=TAUPE)
    if p > 0.15:
        d.text((W / 2, 640), "salir un rato", fill=UMBER, font=font(64), anchor="mm")
    return im

def sc_sun(i, n, rng):
    im = paper(rng); d = ImageDraw.Draw(im); p = i / n
    circle(d, 820, 420, 90 + 10 * p, rng, width=8, color=SAGE)
    for k in range(8):
        a = k * math.pi / 4
        stroke(d, [(820 + 120 * math.cos(a), 420 + 120 * math.sin(a)), (820 + (140 + 30 * p) * math.cos(a), 420 + (140 + 30 * p) * math.sin(a))], rng, width=5, color=SAGE)
    stroke(d, [(k * 40, 1300 + 40 * math.sin(k / 6 + 2)) for k in range(0, 28)], rng, width=6, color=TAUPE, amp=1.5)
    x, y = 440, 1300
    head(d, x, y - 250, rng, look="up")
    stroke(d, [(x, y - 204), (x, y - 60)], rng)
    stroke(d, [(x, y - 60), (x - 20, y + 90)], rng); stroke(d, [(x, y - 60), (x + 25, y + 90)], rng)
    stroke(d, [(x, y - 170), (x - 50, y - 60)], rng); stroke(d, [(x, y - 170), (x + 70, y - 120), (x + 120, y - 70)], rng)
    b = dog(d, x + 260, 1300, 0, rng, sit=True)
    stroke(d, [(x + 120, y - 70), (x + 190, y - 40), b], rng, width=4, color=TAUPE)
    # la nube de garabatos se volvió hoja
    if p < 0.35:
        scribble(d, x + 60, y - 380, rng, r=40 * (1 - p / 0.35) + 10)
    else:
        leaf(d, x + 60, y - 380, rng, s=min(1.0, (p - 0.35) / 0.3))
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
    d.text((W / 2, 490), "El paseo", fill=UMBER, font=font(120, bold=True), anchor="mm")
    # viñeta: el personaje y el perro, en una ventana redonda
    circle(d, W / 2, 1060, 330, rng, width=8, fill=CREAM)
    a = person_walk(d, W / 2 - 150, 1300, 0.15, rng)
    b = dog(d, W / 2 + 120, 1300, 0.15, rng)
    stroke(d, [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 40), b], rng, width=4, color=TAUPE)
    d.text((W / 2, 1520), "un libro para hojear", fill=(120, 104, 84), font=font(44), anchor="mm")
    d.text((W / 2, H - 230), "capítulo 1 · lunes", fill=(120, 104, 84), font=font(40), anchor="mm")
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

def chrome(im, page, total, rng, jitter=True):
    """Taco de hojas, número de página, pulgar y registro imperfecto."""
    d = ImageDraw.Draw(im)
    left = int(18 * (1 - page / total)) + 4
    for k in range(left):
        y = H - 40 - k * 3; d.line((60 + k * 2, y, W - 60 - k * 2, y), fill=LINE, width=2)
        x = W - 40 - k * 3; d.line((x, 60 + k * 2, x, H - 60 - k * 2), fill=LINE, width=2)
    d.text((W - 150, H - 130), str(page), fill=DUST, font=font(40), anchor="mm")
    thumb(d)
    if jitter:
        im = im.transform(im.size, Image.AFFINE, (1, 0, rng.randint(-3, 3), 0, 1, rng.randint(-3, 3)), fillcolor=CREAM)
    return im

def thumb(d, lift=0):
    d.ellipse((W - 330, H - 190 - lift, W + 120, H + 190 - lift), fill=(226, 206, 184), outline=(205, 182, 158), width=4)
    d.ellipse((W - 200, H - 120 - lift, W + 60, H + 120 - lift), fill=(233, 214, 194))

def page_turn(prev, nxt, k):
    """Cuadro de transición: la hoja anterior se levanta desde la esquina del pulgar.
    k = 0..1 cuánto se levantó. Se ve el dorso (más claro) y una sombra sobre la hoja nueva."""
    out = nxt.copy()
    d = ImageDraw.Draw(out, "RGBA")
    # tamaño del pliegue: crece con k
    s = int(260 + 900 * k)
    # sombra suave sobre la hoja nueva
    d.polygon([(W, H - s - 60), (W - s - 60, H), (W, H)], fill=(60, 50, 40, 40))
    # la parte de la hoja vieja que todavía está apoyada: todo menos el triángulo
    mask = Image.new("L", (W, H), 255)
    ImageDraw.Draw(mask).polygon([(W, H - s), (W - s, H), (W, H)], fill=0)
    out.paste(prev, (0, 0), mask)
    # dorso de la hoja levantada
    d.polygon([(W, H - s), (W - s, H), (W - s * 0.55, H - s * 0.55)], fill=(252, 247, 238, 255))
    d.line([(W, H - s), (W - s * 0.55, H - s * 0.55), (W - s, H)], fill=(200, 188, 168, 255), width=3)
    thumb(d, lift=int(40 * k))
    return out

def close_book(last, back, k):
    """La tapa entra desde la derecha y cubre la última hoja; después queda la contratapa."""
    out = last.copy()
    d = ImageDraw.Draw(out, "RGBA")
    ease = 1 - (1 - k) ** 2
    x = int(W - W * ease)
    # sombra que precede a la tapa
    d.rectangle((max(0, x - 120), 0, x, H), fill=(60, 50, 40, int(90 * ease)))
    cov = back.crop((0, 0, W - x, H)) if W - x > 0 else None
    if cov:
        # la tapa se ve "de canto" al principio: la comprimimos horizontalmente
        cov = back.resize((max(1, W - x), H))
        out.paste(cov, (x, 0))
    return out

def main():
    story = [(sc_monday, 2.6), (sc_card_out, 3.0), (sc_read, 2.6), (sc_walk, 5.0), (sc_sun, 3.4)]
    frames_dir = os.path.join(os.path.dirname(os.path.abspath(OUT)), "frames_v2")
    os.makedirs(frames_dir, exist_ok=True)
    for f in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, f))
    k = [0]
    def emit(im, times=1):
        for _ in range(times):
            im.save(os.path.join(frames_dir, "f%05d.png" % k[0])); k[0] += 1

    total_pages = sum(int(sec * FPS / HOLD) for _, sec in story)
    # PORTADA: 2 s, respira (boil) sin pasar página
    for i in range(int(2.0 * FPS / HOLD)):
        emit(cover(i, 10, random.Random(1000 + i)), HOLD)
    # HISTORIA
    prev = None; page = 0
    for fn, sec in story:
        n = int(sec * FPS / HOLD)
        for i in range(n):
            page += 1
            rng = random.Random(page)
            im = chrome(fn(i, n, rng), page, total_pages, rng)
            if prev is not None:
                emit(page_turn(prev, im, 0.5), 1)     # 1 cuadro de hoja en vuelo = el "peso" del pase
                emit(im, HOLD - 1)
            else:
                emit(page_turn(cover(0, 10, rng), im, 0.6), 1); emit(im, HOLD - 1)
            prev = im
    # CIERRE: la última hoja se sostiene, la tapa se cierra en 1 s, contratapa 3 s
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

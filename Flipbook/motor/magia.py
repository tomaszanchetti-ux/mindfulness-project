"""La escena de la magia (escena 4 de todos los volúmenes) como prueba de piezas (D1.2 · F · WS33).

    python3 Flipbook/motor/magia.py                # hoja fija de los 5 cuadros clave + mp4
    python3 Flipbook/motor/magia.py --solo-hoja    # solo la hoja

Los cuatro momentos (Tomás, WS33: menos acciones, que no maree): (1) el teléfono se pone
verde a nivel pantalla y el ruido se disuelve · (2) Teo medita con los ojos cerrados y el aura
aparece · (3) escribe en el diario con la burbuja de lo que importa (el descubrimiento de
cada volumen) · (4) con el aura, la acción que muestra el cambio (cambia por volumen; acá la
cena familiar de Vínculos). La pequeña acción de (2) es un menú por volumen: medita o pasea
(`sc_paseo` queda como alternativa, fuera de la secuencia).

Hoja fija → `personajes/hoja_magia.png`. Video → `pruebas/magia.mp4` (los mp4 no van al repo).
Todo lo de acá es un GUION DE PRUEBA: los fondos y la burbuja son capa simple (línea) y en
D1.2-A pasan al motor que lee guiones; las piezas nuevas (teléfono, cuadernito, medita,
camina, cara cerrada, aura) son el ASSET.
"""
import math, os, random, subprocess, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
from marioneta import Marioneta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = 1.6          # escala de Teo en la hoja (el cuerpo mide 640 px)
PISO = 1420

def prop(m, im, nombre, x, y, escala_personaje, rng, rot=0.0):
    """Pega una pieza de utilería con su escala relativa al personaje que la sostiene."""
    a = m.anclas("props", nombre)
    m.solo(im, "props", nombre, x, y, escala=escala_personaje * a["escala_rel"], rng=rng, rot=rot)

def ancla(m, personaje, cuerpo, nombre, x, y, escala):
    """Coordenadas en la hoja de un ancla del cuerpo (manos, pecho, mano)."""
    ax, ay = m.anclas(personaje, "cuerpo_" + cuerpo)[nombre]
    return x + (ax - 200) * escala, y + (ay - 200) * escala

def texto(d, s, y=420, color=R.UMBER):
    d.text((R.W / 2, y), s, fill=color, font=R.font(64), anchor="mm")

def burbuja(d, x, y, rng, hacia):
    """Burbuja de pensamiento con un dibujo simple adentro: los abuelos (capa simple)."""
    for k, (bx, by, r) in enumerate(((hacia[0] + (x - hacia[0]) * 0.25, hacia[1] + (y - hacia[1]) * 0.3, 14),
                                     (hacia[0] + (x - hacia[0]) * 0.5, hacia[1] + (y - hacia[1]) * 0.6, 24))):
        R.circle(d, bx, by, r, rng, width=5, fill=R.IVORY)
    R.circle(d, x, y, 210, rng, width=6, fill=R.IVORY, ry=150, amp=3)
    for cx, abuela in ((x - 70, True), (x + 70, False)):
        R.circle(d, cx, y + 10, 46, rng, width=5, fill=R.CREAM, ry=52)
        if abuela:
            R.circle(d, cx, y - 46, 18, rng, width=5, fill=R.SAND)             # el rodete
        else:
            for k in range(3):                                                  # tres pelitos
                R.stroke(d, [(cx - 14 + 14 * k, y - 40), (cx - 18 + 14 * k, y - 58)], rng, width=4, color=R.TAUPE)
            R.stroke(d, [(cx - 16, y + 22), (cx + 16, y + 22)], rng, width=5, color=R.TAUPE)   # el bigote
        for dx in (-16, 16):
            d.ellipse((cx + dx - 4, y - 4, cx + dx + 4, y + 4), fill=R.UMBER)
        d.line(R.wobble(R.arc_pts(cx, y + 16, 16, 9, 0.15 * math.pi, 0.85 * math.pi, 6), rng, 1), fill=R.UMBER, width=4, joint="curve")

def piso(d, rng):
    R.stroke(d, [(120, PISO), (960, PISO)], rng, width=6, color=R.TAUPE)

# ---------------- los cinco momentos ----------------

def sc_enciende(m, i, n, rng):
    """F1: encorvado en el rincón con el teléfono; la pantalla se pone verde; el ruido se va.
    Entre p 0.30 y 0.55 el libro se ACERCA (2-3 hojas de primer plano del teléfono, REGLAS §2)."""
    im = R.paper(rng); d = ImageDraw.Draw(im); p = i / n
    if 0.30 <= p < 0.56:
        # la hoja "acerca": el teléfono grande entre las manos, la pantalla entera se enciende
        nivel = 1 if p < 0.36 else (2 if p < 0.44 else (3 if (i // 2) % 2 == 0 else 2))
        x, y = 540, 960
        m.solo(im, "props", "telefono_%d" % nivel, x, y, escala=3.2, rng=rng, rot=-12)
        for hx, hy in ((x - 210, y + 300), (x + 250, y + 250)):       # las manos, simples
            R.circle(d, hx, hy, 92, rng, width=7, fill=R.CREAM, ry=76)
            R.stroke(d, [(hx - 20, hy - 60), (hx + 24, hy - 110)], rng, width=7)
        texto(d, "algo se enciende.", y=380, color=R.SAGE_DEEP)
        return im
    piso(d, rng)
    R.stroke(d, [(380, 1180), (700, 1180), (700, PISO)], rng, width=6, color=R.TAUPE)   # el banquito del rincón
    R.stroke(d, [(400, 1180), (400, PISO)], rng, width=6, color=R.TAUPE)
    x, y = 540, 1100
    if p < 0.6:
        cuerpo, cara = "sentado", "abajo_plana"
    else:
        cuerpo, cara = "sentado_erguido", ("frente_plana" if p < 0.8 else "frente_sonrisa")
    m.pegar(im, "teo", cuerpo, cara, x, y, escala=E, rng=rng)
    mx, my = ancla(m, "teo", cuerpo, "manos", x, y, E)
    nivel = 0 if p < 0.3 else (2 if (i // 3) % 2 == 0 else 3)
    prop(m, im, "telefono_%d" % nivel, mx + 12, my - 34, E, rng, rot=-24)
    if p < 0.3:                                     # la nube de garabatos, antes del zoom
        R.scribble(d, 560, 640, rng, r=80, color=R.TAUPE, width=4)
    if p > 0.56:
        texto(d, "algo se enciende.", color=R.SAGE_DEEP)
    return im

def sc_medita(m, i, n, rng):
    """F2: sentado con las piernas cruzadas, ojos cerrados; el aura aparece mientras respira."""
    im = R.paper(rng); d = ImageDraw.Draw(im); p = i / n
    piso(d, rng)
    x, y = 540, 1160
    px, py = ancla(m, "teo", "medita", "pecho", x, y, E)
    for k in range(2):                              # dos anillos que crecen desde el pecho
        r = 170 + 120 * k + 40 * math.sin(i * 0.45 - k * 0.9)
        R.circle(d, px, py, r, rng, width=(4 if k == 0 else 3), color=R.SAGE_LIGHT, amp=3, ry=r * 1.1)
    pulso = 0.5 + 0.5 * math.sin(i * 0.5)
    m.pegar(im, "teo", "medita", "cerrada_sonrisa", x, y, escala=E, rng=rng, aura=min(1.0, max(0.0, (p - 0.15) * 1.6)), pulso=pulso)
    if p > 0.2:
        texto(d, "por suerte descubrió la Pausa.")
    return im

def sc_paseo(m, i, n, rng):
    """F2 alternativa (menú por volumen: medita o pasea): el paseo erguido con parallax y Pipo
    trotando adelante. No está en la secuencia de prueba (Tomás, WS33: menos acciones)."""
    im = R.paper(rng); d = ImageDraw.Draw(im); p = i / n
    R.circle(d, 820, 420, 90, rng, width=8, color=R.SAGE)
    R.stroke(d, [(k * 40, PISO + 30 * math.sin(k / 6 + p * 2)) for k in range(0, 28)], rng, width=6, color=R.TAUPE, amp=1.5)
    for tx in ((1500 - p * 1500) % 1500 - 200, (2200 - p * 1500) % 1500 - 200):
        R.stroke(d, [(tx, PISO - 10), (tx, PISO - 170)], rng, width=6, color=R.LINE)
        R.circle(d, tx, PISO - 220, 70, rng, width=6, color=R.LINE)
    m.pegar(im, "teo", "camina_%d" % (i % 4), "costado_sonrisa", 420, 1120, escala=E, rng=rng)
    m.pegar(im, "pipo", "camina_%d" % ((i + 2) % 4), "alegria_sarcastica", 800, 1290, escala=0.72, rng=rng)
    if p > 0.15:
        texto(d, "y salió a caminar.", y=300)
    return im

def sc_escribe(m, i, n, rng):
    """F3: en el banco, escribe en el cuadernito; la burbuja muestra lo que importa."""
    im = R.paper(rng); d = ImageDraw.Draw(im); p = i / n
    piso(d, rng)
    R.stroke(d, [(300, 1180), (760, 1180)], rng, width=8, color=R.TAUPE)               # el banco
    R.stroke(d, [(330, 1180), (330, PISO)], rng, width=6, color=R.TAUPE); R.stroke(d, [(730, 1180), (730, PISO)], rng, width=6, color=R.TAUPE)
    x, y = 500, 1100
    m.pegar(im, "teo", "sentado_erguido", "abajo_sonrisa", x, y, escala=E, rng=rng)
    mx, my = ancla(m, "teo", "sentado_erguido", "manos", x, y, E)
    avance = min(3, int(p * 4))
    prop(m, im, "cuadernito_%d" % avance, mx + 30, my - 10, E, rng, rot=-10)
    m.pegar(im, "pipo", "sentado", "orgullo", 880, 1280, escala=0.62, rng=rng)
    if p > 0.25:
        hx, hy = ancla(m, "teo", "sentado_erguido", "cabeza", x, y, E)
        burbuja(d, 700, 560, rng, hacia=(hx + 40, hy - 60))
    if p > 0.15:
        texto(d, "escribió lo que importa.", y=300)
    return im

def familiar(d, x, y, rng, abuela, s=1.9):
    """Un secundario de línea simple sentado a la mesa, a la escala de Teo (capa simple; en D2
    se detalla el de cada volumen)."""
    R.circle(d, x, y, 44 * s, rng, width=6, color=R.TAUPE, fill=R.CREAM, ry=50 * s)
    if abuela:
        R.circle(d, x, y - 50 * s, 18 * s, rng, width=5, color=R.TAUPE, fill=R.SAND)
    else:
        for k in range(3):
            R.stroke(d, [(x + (-14 + 14 * k) * s, y - 40 * s), (x + (-18 + 14 * k) * s, y - 60 * s)], rng, width=4, color=R.TAUPE)
        R.stroke(d, [(x - 16 * s, y + 14 * s), (x + 16 * s, y + 14 * s)], rng, width=6, color=R.TAUPE)
    for dx in (-15 * s, 15 * s):
        d.ellipse((x + dx - 5, y - 10, x + dx + 5, y), fill=R.UMBER)
    d.line(R.wobble(R.arc_pts(x, y + 6 * s, 16 * s, 9 * s, 0.15 * math.pi, 0.85 * math.pi, 6), rng, 1), fill=R.UMBER, width=5, joint="curve")
    R.stroke(d, [(x, y + 50 * s), (x, y + 120 * s)], rng, width=8, color=R.TAUPE)                  # el cuerpo
    R.stroke(d, [(x, y + 70 * s), (x - 60 * s, y + 105 * s)], rng, width=7, color=R.TAUPE)        # los brazos a la mesa
    R.stroke(d, [(x, y + 70 * s), (x + 50 * s, y + 105 * s)], rng, width=7, color=R.TAUPE)

def sc_accion(m, i, n, rng):
    """F4: la acción que muestra el cambio, con el aura. Cambia por volumen; acá el ejemplo de
    Vínculos: la cena familiar, Teo presente y de frente a los abuelos (antes, en el rincón)."""
    im = R.paper(rng); d = ImageDraw.Draw(im); p = i / n
    piso(d, rng)
    familiar(d, 720, 900, rng, abuela=True)
    familiar(d, 920, 890, rng, abuela=False)
    # la mesa, delante de la familia
    R.stroke(d, [(470, 1130), (1000, 1130)], rng, width=8, color=R.TAUPE)
    R.stroke(d, [(520, 1130), (520, PISO)], rng, width=6, color=R.TAUPE); R.stroke(d, [(950, 1130), (950, PISO)], rng, width=6, color=R.TAUPE)
    for cx in (620, 780, 900):                                                          # platos
        R.circle(d, cx, 1122, 34, rng, width=4, color=R.TAUPE, fill=R.IVORY, ry=10)
    # Teo en su silla, erguido, mirando a la familia, con el aura que respira
    R.stroke(d, [(300, 1180), (460, 1180), (460, PISO)], rng, width=6, color=R.TAUPE); R.stroke(d, [(320, 1180), (320, PISO)], rng, width=6, color=R.TAUPE)
    pulso = 0.5 + 0.5 * math.sin(i * 0.6)
    m.pegar(im, "teo", "sentado_erguido", ("costado_sonrisa" if p < 0.6 else "costado_abierta"), 400, 1100, escala=E, rng=rng, aura=1.0, pulso=pulso)
    m.pegar(im, "pipo", "sentado", "orgullo", 200, 1300, escala=0.6, rng=rng)
    if p > 0.2:
        texto(d, "y se le nota.")
    return im

# la secuencia de prueba: 4 momentos (Tomás, WS33: menos acciones). El paseo queda como alternativa.
ESCENAS = [(sc_enciende, 3.0), (sc_medita, 2.6), (sc_escribe, 2.4), (sc_accion, 2.4)]

# ---------------- salidas ----------------

def hoja_fija(m):
    """Los cinco cuadros clave, uno al lado del otro, para mirar sin el video."""
    cuadros = []
    for k, (fn, sec) in enumerate(ESCENAS):
        n = int(sec * R.FPS / R.HOLD)
        i = int(n * 0.85)
        rng = random.Random(100 + k)
        cuadros.append(R.chrome(fn(m, i, n, rng), 30 + k, 60, rng))
    esc = 0.42
    w, h = int(R.W * esc), int(R.H * esc)
    im = Image.new("RGB", (w * len(cuadros) + (len(cuadros) + 1) * 30, h + 60 + 60), (222, 211, 190))
    d = ImageDraw.Draw(im)
    d.text((im.width / 2, 34), "La escena de la magia · piezas de D1.2 (F) · se enciende · medita con aura · escribe · la acción con aura", fill=R.UMBER, font=R.font(30), anchor="mm")
    for k, c in enumerate(cuadros):
        im.paste(c.resize((w, h), Image.LANCZOS), (30 + k * (w + 30), 70))
    return im

def video(m, salida):
    frames = os.path.join(RAIZ, "pruebas", "frames_magia")
    os.makedirs(frames, exist_ok=True)
    for f in os.listdir(frames):
        os.remove(os.path.join(frames, f))
    k = [0]
    def emit(im, veces=1):
        for _ in range(veces):
            im.save(os.path.join(frames, "f%05d.png" % k[0])); k[0] += 1
    total = sum(int(sec * R.FPS / R.HOLD) for _, sec in ESCENAS)
    prev = None; page = 0
    for fn, sec in ESCENAS:
        n = int(sec * R.FPS / R.HOLD)
        for i in range(n):
            page += 1; rng = random.Random(page)
            im = R.chrome(fn(m, i, n, rng), page, total, rng)
            if prev is not None:
                emit(R.page_turn(prev, im, 0.5), 1)
                emit(im, R.HOLD - 1)
            else:
                emit(im, R.HOLD)
            prev = im
    emit(prev, R.FPS)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(R.FPS), "-i", os.path.join(frames, "f%05d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", salida], check=True)
    print("hojas:", total, "cuadros:", k[0], "seg:", round(k[0] / R.FPS, 1), "->", salida)

if __name__ == "__main__":
    m = Marioneta()
    destino = os.path.join(RAIZ, "personajes", "hoja_magia.png")
    hoja_fija(m).save(destino)
    print("hoja ->", destino)
    if "--solo-hoja" not in sys.argv:
        os.makedirs(os.path.join(RAIZ, "pruebas"), exist_ok=True)
        video(m, os.path.join(RAIZ, "pruebas", "magia.mp4"))

"""Hoja de personajes v2 + video de prueba de las piezas ilustradas (D1.1 · WS32).

    python3 Flipbook/motor/hoja.py                 # hoja PNG + mp4 de prueba
    python3 Flipbook/motor/hoja.py --sin-rotulos   # la hoja sin nombres (el test de Tomás)

La hoja va a `personajes/hoja_de_personajes_v2.png`; el video a `pruebas/caras_pipo.mp4`
(los mp4 no van al repo).
"""
import os, random, subprocess, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
from marioneta import Marioneta

RAIZ = R.os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARAS = ["fastidio", "resignacion", "sospecha", "en_serio", "alegria_sarcastica", "orgullo"]
ROTULOS = {"fastidio": "fastidio", "resignacion": "resignación", "sospecha": "sospecha", "en_serio": "¿en serio?",
           "alegria_sarcastica": "alegría sarcástica", "orgullo": "orgullo"}

def hoja_de_personajes(m, rotulos=True):
    rng = random.Random(5)
    im = R.paper(rng, size=(2600, 1750)); d = ImageDraw.Draw(im)
    d.text((1300, 70), "Hoja de personajes · v2 · Teo y Pipo", fill=R.UMBER, font=R.font(52), anchor="mm")
    d.text((1300, 125), "Pipo: las seis caras · Teo: el pelo y los cuerpos base", fill=R.DUST, font=R.font(30), anchor="mm")
    # fila 1: las 6 caras de Pipo, cabeza sola en primer plano
    for k, cara in enumerate(CARAS):
        x = 260 + k * 420
        m.solo(im, "pipo", "cara_" + cara, x, 360, escala=0.78, rng=rng, pivote=(200, 230))
        d.text((x, 560), (ROTULOS[cara] if rotulos else str(k + 1)), fill=R.DUST, font=R.font(30), anchor="mm")
    # fila 2: las poses de Pipo con una cara cada una, y Teo
    poses = [("sentado", "sospecha"), ("camina", "alegria_sarcastica"), ("panza_arriba", "orgullo"), ("plantado", "fastidio"), ("cae", "resignacion")]
    for k, (cuerpo, cara) in enumerate(poses):
        x = 240 + k * 330
        m.pegar(im, "pipo", cuerpo, cara, x, 1050, escala=0.62, rng=rng)
        d.text((x, 1260), (cuerpo.replace("_", " ") if rotulos else ""), fill=R.DUST, font=R.font(28), anchor="mm")
    # Teo: cara grande + tres cuerpos
    m.solo(im, "teo", "cara_frente_plana", 1930, 880, escala=0.95, rng=rng, pivote=(200, 210))
    m.pegar(im, "teo", "encorvado", "cara_abajo_plana", 2200, 1080, escala=0.9, rng=rng)
    m.pegar(im, "teo", "parado", "cara_frente_sonrisa", 2440, 1080, escala=0.9, rng=rng)
    m.pegar(im, "teo", "sentado", "cara_abajo_plana", 1950, 1520, escala=0.8, rng=rng)
    m.pegar(im, "teo", "sentado_erguido", "cara_costado_sonrisa", 2300, 1520, escala=0.8, rng=rng)
    if rotulos:
        d.text((1930, 1290), "Teo", fill=R.DUST, font=R.font(28), anchor="mm")
        d.text((2200, 1290), "encorvado", fill=R.DUST, font=R.font(28), anchor="mm")
        d.text((2440, 1290), "erguido", fill=R.DUST, font=R.font(28), anchor="mm")
        d.text((2000, 1700), "sentado (teléfono)", fill=R.DUST, font=R.font(28), anchor="mm")
        d.text((2340, 1700), "sentado (cuadernito)", fill=R.DUST, font=R.font(28), anchor="mm")
    return im

# ---------------- el video de prueba: las caras pasando ----------------

def hoja_cara(m, cara, i, n, rng, texto=None):
    im = R.paper(rng); d = ImageDraw.Draw(im)
    R.stroke(d, [(120, 1420), (960, 1420)], rng, width=6, color=R.TAUPE)
    m.pegar(im, "pipo", "sentado", cara, 540, 1200, escala=1.5, rng=rng)
    if texto and i > 2:
        d.text((R.W / 2, 420), texto, fill=R.UMBER, font=R.font(64), anchor="mm")
    return im

def hoja_pose(m, cuerpo, cara, i, n, rng, texto=None, camina=False, espejo=False):
    im = R.paper(rng); d = ImageDraw.Draw(im)
    R.stroke(d, [(120, 1420), (960, 1420)], rng, width=6, color=R.TAUPE)
    if camina:
        cuerpo = "camina_%d" % (i % 4)
    m.pegar(im, "pipo", cuerpo, cara, 540, 1160, escala=1.0, rng=rng, espejo=espejo)
    if texto and i > 2:
        d.text((R.W / 2, 420), texto, fill=R.UMBER, font=R.font(64), anchor="mm")
    return im

def hoja_teo(m, cuerpo, cara, i, n, rng, texto=None):
    im = R.paper(rng); d = ImageDraw.Draw(im)
    R.stroke(d, [(120, 1420), (960, 1420)], rng, width=6, color=R.TAUPE)
    m.pegar(im, "teo", cuerpo, cara, 540, 1060, escala=1.6, rng=rng)
    if texto and i > 2:
        d.text((R.W / 2, 380), texto, fill=R.UMBER, font=R.font(64), anchor="mm")
    return im

def video(m, salida):
    frames = os.path.join(RAIZ, "pruebas", "frames_caras")
    os.makedirs(frames, exist_ok=True)
    for f in os.listdir(frames):
        os.remove(os.path.join(frames, f))
    k = [0]
    def emit(im, veces=1):
        for _ in range(veces):
            im.save(os.path.join(frames, "f%05d.png" % k[0])); k[0] += 1
    escenas = [(lambda i, n, rng, c=c: hoja_cara(m, c, i, n, rng), 1.4) for c in CARAS]
    escenas += [(lambda i, n, rng: hoja_pose(m, "camina", "alegria_sarcastica", i, n, rng, camina=True), 1.6),
                (lambda i, n, rng: hoja_pose(m, "panza_arriba", "orgullo", i, n, rng), 1.2),
                (lambda i, n, rng: hoja_pose(m, "plantado", "fastidio", i, n, rng), 1.2),
                (lambda i, n, rng: hoja_pose(m, "cae", "resignacion", i, n, rng), 1.2),
                (lambda i, n, rng: hoja_teo(m, "encorvado", "cara_abajo_plana", i, n, rng), 1.2),
                (lambda i, n, rng: hoja_teo(m, "parado", "cara_frente_sonrisa", i, n, rng), 1.2),
                (lambda i, n, rng: hoja_teo(m, "sentado", "cara_abajo_plana", i, n, rng), 1.2)]
    total = sum(int(sec * R.FPS / R.HOLD) for _, sec in escenas)
    prev = None; page = 0
    for fn, sec in escenas:
        n = int(sec * R.FPS / R.HOLD)
        for i in range(n):
            page += 1; rng = random.Random(page)
            im = R.chrome(fn(i, n, rng), page, total, rng)
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
    rotulos = "--sin-rotulos" not in sys.argv
    destino = os.path.join(RAIZ, "personajes", "hoja_de_personajes_v2%s.png" % ("" if rotulos else "_sin_rotulos"))
    hoja_de_personajes(m, rotulos).save(destino)
    print("hoja ->", destino)
    if "--solo-hoja" not in sys.argv:
        os.makedirs(os.path.join(RAIZ, "pruebas"), exist_ok=True)
        video(m, os.path.join(RAIZ, "pruebas", "caras_pipo.mp4"))

"""Compone las piezas ilustradas (partes.py) sobre una hoja: cuerpo + cabeza con anclas,
temblor y registro imperfecto. Es la capa de detalle que el motor usa en cada hoja.

    from marioneta import Marioneta
    m = Marioneta()                      # lee personajes/partes/partes.json
    m.pegar(hoja, "pipo", "sentado", "cara_sospecha", x=540, y=1300, escala=0.7, rng=rng)

x, y = dónde apoya el cuerpo (el centro del lienzo del cuerpo, 200,200 en unidades).
escala = píxeles de la hoja por unidad de lienzo (0.7 → el cuerpo mide 280 px).
"""
import json, math, os, random
from PIL import Image, ImageFilter

SAGE = (143, 165, 138); SAGE_LIGHT = (185, 203, 179)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # Flipbook/

class Marioneta:
    def __init__(self, ruta=None):
        ruta = ruta or os.path.join(RAIZ, "personajes", "partes", "partes.json")
        with open(ruta) as f:
            self.indice = json.load(f)
        self._cache = {}

    def _png(self, personaje, pieza):
        clave = (personaje, pieza)
        if clave not in self._cache:
            self._cache[clave] = Image.open(os.path.join(RAIZ, self.indice[personaje][pieza]["png"])).convert("RGBA")
        return self._cache[clave]

    def anclas(self, personaje, pieza):
        return self.indice[personaje][pieza]

    def _pieza(self, personaje, pieza, escala, rot, pivote, rng, temblor):
        """Devuelve (imagen, offset) lista para pegar con el pivote en (0,0)."""
        a = self.anclas(personaje, pieza)
        im = self._png(personaje, pieza)
        k = escala / a["escala_png"]
        im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
        px, py = pivote[0] * escala, pivote[1] * escala
        # lienzo grande centrado en el pivote, para rotar sin recortar
        lado = int(2.2 * max(im.width, im.height))
        big = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
        big.paste(im, (int(lado / 2 - px), int(lado / 2 - py)), im)
        ang = rot + (rng.uniform(-1.2, 1.2) if temblor else 0)
        if abs(ang) > 0.01:
            big = big.rotate(-ang, resample=Image.BICUBIC, center=(lado / 2, lado / 2))
        return big, (lado / 2, lado / 2)

    def pegar(self, hoja, personaje, cuerpo, cara, x, y, escala=1.0, rng=None, temblor=True, rot=0.0, espejo=False,
              aura=0.0, pulso=0.0, rot_cabeza=0.0):
        """Pega cuerpo + cabeza. cuerpo/cara son nombres de pieza sin el prefijo o con él.
        aura 0..1 = el halo salvia alrededor de la silueta (F4, la escena de la magia): se calcula
        de la silueta del personaje ya compuesto, así sirve para cualquier pose. pulso 0..1 lo
        hace respirar hoja a hoja. rot_cabeza = grados extra SOLO de la cabeza (el cabeceo de la
        vida del cuadro, WS34): el cuerpo no se mueve."""
        if aura > 0:
            capa = Image.new("RGBA", hoja.size, (0, 0, 0, 0))
            punto = self.pegar(capa, personaje, cuerpo, cara, x, y, escala, rng, temblor, rot, espejo,
                               rot_cabeza=rot_cabeza)
            self.halo(hoja, capa, aura, pulso)
            hoja.paste(capa, (0, 0), capa)
            return punto
        rng = rng or random.Random(0)
        cuerpo = cuerpo if cuerpo.startswith("cuerpo_") else "cuerpo_" + cuerpo
        cara = cara if cara.startswith("cara_") else "cara_" + cara
        ac = self.anclas(personaje, cuerpo)
        jx, jy = (rng.uniform(-2, 2), rng.uniform(-2, 2)) if temblor else (0, 0)
        # cuerpo, pivote en su centro (200, 200)
        big, (cx, cy) = self._pieza(personaje, cuerpo, escala, rot, (200, 200), rng, temblor)
        if espejo:
            big = big.transpose(Image.FLIP_LEFT_RIGHT)
        cuerpo_img, cuerpo_pos = big, (int(x - cx + jx), int(y - cy + jy))
        # cabeza: su cuello cae en el ancla "cabeza" del cuerpo (rotada junto con el cuerpo)
        hx, hy = ac["cabeza"]
        dx, dy = (hx - 200) * escala, (hy - 200) * escala
        if espejo:
            dx = -dx
        r = math.radians(rot)
        ax = x + dx * math.cos(r) - dy * math.sin(r)
        ay = y + dx * math.sin(r) + dy * math.cos(r)
        acab = self.anclas(personaje, cara)
        rot_cab = rot + (-ac["rot"] if espejo else ac["rot"]) + rot_cabeza
        big, (cx, cy) = self._pieza(personaje, cara, escala * ac["escala"], rot_cab, acab["cuello"], rng, temblor)
        if espejo:
            big = big.transpose(Image.FLIP_LEFT_RIGHT)
        cabeza_img, cabeza_pos = big, (int(ax - cx + jx), int(ay - cy + jy))
        # z_cabeza "detras" (WS34): el cuerpo tapa a la cabeza (las patas en Y delante de la cara)
        orden = [(cuerpo_img, cuerpo_pos), (cabeza_img, cabeza_pos)]
        if ac.get("z_cabeza") == "detras":
            orden.reverse()
        for img, pos in orden:
            hoja.paste(img, pos, img)
        return (ax, ay)

    def halo(self, hoja, capa, fuerza=1.0, pulso=0.0):
        """El aura salvia: dos halos (uno pegado al cuerpo, uno ancho y suave) sacados de la
        silueta de `capa` (RGBA del tamaño de la hoja). Se pinta DEBAJO del personaje, así que
        se llama antes de pegar la capa. Sin color nuevo: solo salvia."""
        alpha = capa.split()[3]
        caja = alpha.getbbox()
        if not caja:
            return
        m = 90
        caja = (max(0, caja[0] - m), max(0, caja[1] - m), min(hoja.width, caja[2] + m), min(hoja.height, caja[3] + m))
        recorte = alpha.crop(caja)
        for radio, color, opacidad in ((30 + 10 * pulso, SAGE_LIGHT, 120), (12 + 5 * pulso, SAGE, 150)):
            mask = recorte.filter(ImageFilter.GaussianBlur(radio)).point(lambda v: min(255, v * 3))
            mask = mask.filter(ImageFilter.GaussianBlur(radio * 0.5)).point(lambda v, o=opacidad * fuerza: int(v * o / 255))
            tinta = Image.new("RGBA", recorte.size, color + (255,))
            tinta.putalpha(mask)
            hoja.paste(tinta, (caja[0], caja[1]), tinta)

    def solo(self, hoja, personaje, pieza, x, y, escala=1.0, rng=None, rot=0.0, temblor=True, pivote=(200, 200)):
        """Pega una pieza suelta (una cabeza sola en primer plano, por ejemplo)."""
        rng = rng or random.Random(0)
        big, (cx, cy) = self._pieza(personaje, pieza, escala, rot, pivote, rng, temblor)
        hoja.paste(big, (int(x - cx), int(y - cy)), big)

"""Compone las piezas ilustradas (partes.py) sobre una hoja: cuerpo + cabeza con anclas,
temblor y registro imperfecto. Es la capa de detalle que el motor usa en cada hoja.

    from marioneta import Marioneta
    m = Marioneta()                      # lee personajes/partes/partes.json
    m.pegar(hoja, "pipo", "sentado", "cara_sospecha", x=540, y=1300, escala=0.7, rng=rng)

x, y = dónde apoya el cuerpo (el centro del lienzo del cuerpo, 200,200 en unidades).
escala = píxeles de la hoja por unidad de lienzo (0.7 → el cuerpo mide 280 px).
"""
import json, math, os, random
from PIL import Image

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

    def pegar(self, hoja, personaje, cuerpo, cara, x, y, escala=1.0, rng=None, temblor=True, rot=0.0, espejo=False):
        """Pega cuerpo + cabeza. cuerpo/cara son nombres de pieza sin el prefijo o con él."""
        rng = rng or random.Random(0)
        cuerpo = cuerpo if cuerpo.startswith("cuerpo_") else "cuerpo_" + cuerpo
        cara = cara if cara.startswith("cara_") else "cara_" + cara
        ac = self.anclas(personaje, cuerpo)
        jx, jy = (rng.uniform(-2, 2), rng.uniform(-2, 2)) if temblor else (0, 0)
        # cuerpo, pivote en su centro (200, 200)
        big, (cx, cy) = self._pieza(personaje, cuerpo, escala, rot, (200, 200), rng, temblor)
        if espejo:
            big = big.transpose(Image.FLIP_LEFT_RIGHT)
        hoja.paste(big, (int(x - cx + jx), int(y - cy + jy)), big)
        # cabeza: su cuello cae en el ancla "cabeza" del cuerpo (rotada junto con el cuerpo)
        hx, hy = ac["cabeza"]
        dx, dy = (hx - 200) * escala, (hy - 200) * escala
        if espejo:
            dx = -dx
        r = math.radians(rot)
        ax = x + dx * math.cos(r) - dy * math.sin(r)
        ay = y + dx * math.sin(r) + dy * math.cos(r)
        acab = self.anclas(personaje, cara)
        rot_cab = rot + (-ac["rot"] if espejo else ac["rot"])
        big, (cx, cy) = self._pieza(personaje, cara, escala * ac["escala"], rot_cab, acab["cuello"], rng, temblor)
        if espejo:
            big = big.transpose(Image.FLIP_LEFT_RIGHT)
        hoja.paste(big, (int(ax - cx + jx), int(ay - cy + jy)), big)
        return (ax, ay)

    def solo(self, hoja, personaje, pieza, x, y, escala=1.0, rng=None, rot=0.0, temblor=True, pivote=(200, 200)):
        """Pega una pieza suelta (una cabeza sola en primer plano, por ejemplo)."""
        rng = rng or random.Random(0)
        big, (cx, cy) = self._pieza(personaje, pieza, escala, rot, pivote, rng, temblor)
        hoja.paste(big, (int(x - cx), int(y - cy)), big)

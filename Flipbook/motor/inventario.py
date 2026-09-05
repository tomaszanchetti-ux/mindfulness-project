"""Inventario de personajes del flipbook: qué fotos hay, quién tiene ficha, quién está dibujado.

Uso:  python3 Flipbook/motor/inventario.py
"""
import os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BANDEJA = os.path.join(RAIZ, "Tiktok")
FICHAS = os.path.join(RAIZ, "Flipbook", "personajes")
MOTOR = os.path.join(RAIZ, "Flipbook", "motor", "render.py")
IMG = (".jpg", ".jpeg", ".png", ".heic", ".webp", ".gif")
NO_SON_PERSONAJES = {"ideas", "referencias", "estilos", "estilo", "musica", "música"}   # carpetas de material general

def main():
    motor = open(MOTOR, encoding="utf-8").read() if os.path.exists(MOTOR) else ""
    m = re.search(r"PERSONAJES\s*=\s*\[([^\]]*)\]", motor)
    dibujados = {s.strip().strip("\"'").lower() for s in m.group(1).split(",") if s.strip()} if m else set()
    nombres = set()
    if os.path.isdir(BANDEJA):
        nombres |= {n for n in os.listdir(BANDEJA) if os.path.isdir(os.path.join(BANDEJA, n)) and not n.startswith(".") and n.lower() not in NO_SON_PERSONAJES}
    if os.path.isdir(FICHAS):
        nombres |= {f[:-3] for f in os.listdir(FICHAS) if f.endswith(".md") and not f.startswith("_")}
    if not nombres:
        print("No hay personajes. Dejá fotos en Tiktok/<nombre>/ y una ficha en Flipbook/personajes/<nombre>.md")
        return
    print("%-12s %-8s %-8s %-10s %s" % ("personaje", "fotos", "ficha", "dibujado", "pendiente"))
    general = [n for n in (os.listdir(BANDEJA) if os.path.isdir(BANDEJA) else []) if n.lower() in NO_SON_PERSONAJES]
    for n in sorted(nombres):
        carpeta = os.path.join(BANDEJA, n)
        fotos = [f for f in os.listdir(carpeta) if f.lower().endswith(IMG)] if os.path.isdir(carpeta) else []
        ficha = os.path.exists(os.path.join(FICHAS, n + ".md"))
        dibujado = n.lower() in dibujados
        pendiente = []
        if not fotos: pendiente.append("fotos en Tiktok/%s/" % n)
        if not ficha: pendiente.append("ficha personajes/%s.md" % n)
        if not dibujado: pendiente.append("marioneta en motor/render.py")
        print("%-12s %-8s %-8s %-10s %s" % (n, len(fotos), "sí" if ficha else "no", "sí" if dibujado else "no", " · ".join(pendiente) or "listo"))
    for g in general:
        k = len([f for f in os.listdir(os.path.join(BANDEJA, g)) if f.lower().endswith(IMG)])
        print("\nMaterial general en Tiktok/%s/: %d imágenes (no es un personaje)" % (g, k))

if __name__ == "__main__":
    main()

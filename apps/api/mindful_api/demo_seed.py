"""WS25 · Q/A visual — siembra Pausas de VERDAD para los usuarios `demo|` locales.

Tomás abre la app en su navegador y tiene que ver el Baúl lleno, con reflexiones de
largos distintos, estrellas, fotos, fichas compartidas y links ya enviados. Este
módulo crea exactamente eso, pasando por los mismos servicios que usa la API (fotos
por `services/fotos`, links por `services/compartir`), para que lo sembrado sea
indistinguible de lo vivido: mismo `storage_path` canónico, mismo cupo por plan.

Uso:  make demo-seed        (o: python -m mindful_api.demo_seed desde apps/api)

Tres candados:
1. SOLO LOCAL: aborta si `settings.auth_mode == "firebase"` (o sea, si esta config
   apunta a un despliegue real). Sembrar Pausas falsas en producción sería mentirle
   al usuario sobre su propia historia.
2. SOLO USUARIOS `demo|`: nadie más se toca. Es la misma frontera que respeta el
   `conftest` de los tests y los targets `premium-demo` / `free-demo`.
3. IDEMPOTENTE: cada Pausa sembrada queda marcada en `descartadas` con `MARCA`.
   Correrlo dos veces no duplica nada (y `descartadas` con un id inexistente lo
   ignora el motor de selección, así que la marca no ensucia el historial).

Las fotos son PNG generados acá con la biblioteca estándar (`zlib` + `struct`): un
color plano por foto. Sin Pillow — no queremos una dependencia para el Q/A.
"""

from __future__ import annotations

import struct
import sys
import zlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db.base import SessionLocal
from .db.models import Carta, Entrega, Usuario
from .services.compartir import crear_compartido
from .services.fotos import subir_foto
from .services.plan import limites

# La huella que hace idempotente al seed. Va en `descartadas` (JSON): no es un id de
# carta real, así que `historial_motor` la saltea sin enterarse.
MARCA = "__demo_seed_ws25__"

# El usuario que se crea si el navegador local todavía no dejó ninguno: el seed
# siempre tiene que dejar algo para mirar.
DEMO_UID = "demo|qa"
DEMO_EMAIL = "demo@dwellia.local"
DEMO_APODO = "Tomito"


# ─────────────────────────────────────────────────────────────────────────────
# Los textos. En español neutro, cálidos y creíbles: es lo que Tomás va a leer
# en pantalla, así que se escriben como los escribiría una persona.
# ─────────────────────────────────────────────────────────────────────────────
REFLEXION_CORTA = "Frené dos minutos antes de contestar el mensaje. Contesté mejor."

REFLEXION_MEDIA_1 = (
    "Salí a caminar sin auriculares. Al principio me incomodó el silencio, pero a "
    "las tres cuadras empecé a escuchar cosas que hace meses no escuchaba: los "
    "pájaros del parque, mis propios pasos."
)

REFLEXION_LARGA = (
    "Hoy me costó empezar. Estuve dando vueltas por la casa buscando cualquier "
    "excusa, hasta que me senté en la silla de la ventana y me quedé quieto un rato. "
    "Pensé en mi hermana, en lo poco que la llamo y en las ganas que tengo de "
    "contarle cómo estoy sin que suene a queja. Me di cuenta de que hace tiempo "
    "confundo estar ocupado con estar bien. No resolví nada, pero salí de la Pausa "
    "con la sensación de haberme escuchado, que es más de lo que venía haciendo en "
    "todo el mes. Mañana la llamo."
)

REFLEXION_MEDIA_2 = (
    "Le agradecí a mi compañera por algo chico que hizo la semana pasada. Se le "
    "iluminó la cara. Me quedé pensando en cuántas veces lo noto y no lo digo."
)

REFLEXION_BREVE = "Respiré hondo tres veces antes de entrar a la reunión. Alcanzó."

REFLEXION_MEDIA_3 = (
    "Me miré al espejo y en vez de buscar qué corregir me dije que estoy haciendo lo "
    "que puedo con lo que tengo. Sonó raro decirlo en voz alta, pero se sintió justo. "
    "Lo voy a repetir mañana, a ver si deja de sonar raro."
)


# ─────────────────────────────────────────────────────────────────────────────
# El guion de las 9 Pausas. Fijo a propósito: mismas fechas y mismos contenidos
# en cada corrida ⇒ nada que comparar "a ojo" entre una corrida y la siguiente.
#   6 con reflexión (largos variados, una de ~480) · 5 con estrellas 1-5 ·
#   4 con fotos (1 a 3, recortadas al cupo del plan) · 4 compartidas / 5 privadas.
# ─────────────────────────────────────────────────────────────────────────────
PAUSAS = [
    # (días atrás, reflexión, estrellas, fotos, visibilidad)
    (2,  REFLEXION_CORTA,    5, 2, "compartida"),
    (4,  REFLEXION_MEDIA_1,  4, 0, "compartida"),
    (6,  REFLEXION_LARGA,    3, 3, "compartida"),
    (8,  None,            None, 1, "privada"),
    (10, REFLEXION_MEDIA_2,  2, 0, "compartida"),
    (12, REFLEXION_BREVE,    1, 1, "privada"),
    (14, None,            None, 0, "privada"),
    (16, REFLEXION_MEDIA_3, None, 0, "privada"),
    (18, None,            None, 0, "privada"),
]

# Un color plano distinto por foto, para distinguirlas de un vistazo en el Baúl.
COLORES = [
    (122, 154, 128),  # verde salvia
    (214, 199, 176),  # arena
    (150, 168, 190),  # azul apagado
    (196, 156, 148),  # terracota suave
    (176, 168, 196),  # lavanda
    (140, 160, 148),  # verde grisáceo
]

ANCHO, ALTO = 320, 240


def png_plano(ancho: int, alto: int, rgb: tuple) -> bytes:
    """Un PNG válido de color plano, armado a mano con `zlib` + `struct`.

    Es el formato mínimo: firma + IHDR (RGB de 8 bits) + IDAT (los píxeles zlibeados,
    con el byte de filtro 0 al principio de cada fila) + IEND. Sirve para que el Q/A
    visual tenga imágenes reales sin sumar Pillow a las dependencias.
    """
    fila = b"\x00" + bytes(rgb) * ancho          # 0 = filtro "None" para esa fila
    crudo = fila * alto

    def _chunk(tipo: bytes, datos: bytes) -> bytes:
        return (
            struct.pack(">I", len(datos))
            + tipo
            + datos
            + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0)  # 8 bits, color type 2 (RGB)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(crudo, 9))
        + _chunk(b"IEND", b"")
    )


def _cartas_variadas(s: Session, cuantas: int) -> list:
    """`cuantas` cartas DISTINTAS, repartidas entre los 6 pilares (round-robin).

    Determinístico (todo ordenado por slug/id): el Baúl sembrado se ve igual siempre,
    y con los seis colores en pantalla en vez de nueve cartas del mismo pilar.
    """
    todas = s.scalars(select(Carta).order_by(Carta.categoria_slug, Carta.id)).all()
    por_pilar: dict = {}
    for c in todas:
        por_pilar.setdefault(c.categoria_slug, []).append(c)

    elegidas: list = []
    vuelta = 0
    while len(elegidas) < cuantas:
        sumo_alguna = False
        for slug in sorted(por_pilar):
            if vuelta < len(por_pilar[slug]):
                elegidas.append(por_pilar[slug][vuelta])
                sumo_alguna = True
                if len(elegidas) == cuantas:
                    break
        if not sumo_alguna:
            break                                  # el mazo es más chico que `cuantas`
        vuelta += 1
    return elegidas


def _ya_sembrado(s: Session, usuario: Usuario) -> int:
    """Cuántas Pausas sembradas tiene ya este usuario (por la marca en `descartadas`)."""
    filas = s.scalars(
        select(Entrega).where(Entrega.usuario_id == usuario.id)
    ).all()
    return sum(1 for e in filas if e.descartadas and MARCA in e.descartadas)


def _usuarios_demo(s: Session) -> list:
    return list(s.scalars(
        select(Usuario).where(Usuario.firebase_uid.like("demo|%")).order_by(Usuario.created_at)
    ).all())


def _crear_usuario_demo(s: Session) -> Usuario:
    """Sin usuarios `demo|` no habría nada que mirar: creamos uno, ya onboardeado."""
    u = Usuario(
        firebase_uid=DEMO_UID,
        email=DEMO_EMAIL,
        apodo=DEMO_APODO,
        terminos_aceptados_at=datetime.now(timezone.utc),
    )
    s.add(u)
    s.commit()
    s.refresh(u)
    return u


def sembrar_usuario(s: Session, usuario: Usuario) -> dict:
    """Las 9 Pausas de UN usuario. Devuelve el resumen (o `saltado` si ya estaban)."""
    ya = _ya_sembrado(s, usuario)
    if ya:
        return {"uid": usuario.firebase_uid, "saltado": True, "pausas": ya}

    fotos_max = limites(usuario).fotos_max          # free = 1 · premium = 3
    cartas = _cartas_variadas(s, len(PAUSAS))
    if len(cartas) < len(PAUSAS):
        raise SystemExit(
            f"El mazo tiene {len(cartas)} cartas y hacen falta {len(PAUSAS)}: "
            "corré `make api-seed` antes."
        )

    ahora = datetime.now(timezone.utc)
    resumen = {"uid": usuario.firebase_uid, "saltado": False, "plan": limites(usuario).plan,
               "pausas": 0, "reflexiones": 0, "estrellas": 0,
               "fotos": 0, "pausas_con_fotos": 0, "compartidas": 0, "links": []}
    color = 0
    ids_por_indice: list = []

    for i, (dias, reflexion, estrellas, cuantas_fotos, visibilidad) in enumerate(PAUSAS):
        # 09:30 UTC de ese día: nunca hoy (la más reciente es de hace 2 días), así
        # que el seed no le pisa al usuario la carta del día que le toca vivir.
        fecha = (ahora - timedelta(days=dias)).replace(
            hour=9, minute=30, second=0, microsecond=0
        )
        entrega = Entrega(
            usuario_id=usuario.id,
            carta_id=cartas[i].id,
            fecha=fecha,
            estrellas=estrellas,
            completada=True,
            reflexion=reflexion,
            visibilidad=visibilidad,
            descartadas=[MARCA],                    # la huella que hace idempotente al seed
        )
        s.add(entrega)
        s.commit()
        s.refresh(entrega)
        ids_por_indice.append(entrega.id)

        resumen["pausas"] += 1
        resumen["reflexiones"] += 1 if reflexion else 0
        resumen["estrellas"] += 1 if estrellas else 0
        resumen["compartidas"] += 1 if visibilidad == "compartida" else 0

        # Las fotos por la puerta de siempre: `subir_foto` aplica el cupo del plan y
        # escribe el `storage_path` canónico. Si el usuario es free, entra 1 sola.
        cuantas = min(cuantas_fotos, fotos_max)
        for _ in range(cuantas):
            subir_foto(s, usuario, entrega.id,
                       png_plano(ANCHO, ALTO, COLORES[color % len(COLORES)]), "image/png")
            color += 1
            resumen["fotos"] += 1
        resumen["pausas_con_fotos"] += 1 if cuantas else 0

    # Dos links ya enviados: uno de una Pausa escrita (viaja entera) y otro de una
    # Pausa en blanco (viaja la carta sola). El modo lo deriva el servicio.
    for indice, nota in ((0, "Me acordé de vos con esta."), (8, None)):
        link = crear_compartido(s, usuario, ids_por_indice[indice], nota=nota)
        resumen["links"].append(link["modo"])

    return resumen


def sembrar() -> list:
    if settings.auth_mode == "firebase":
        raise SystemExit(
            "demo_seed es SOLO local: con MINDFUL_AUTH_MODE=firebase esta config "
            "apunta a un despliegue real y no se siembra nada."
        )

    with SessionLocal() as s:
        usuarios = _usuarios_demo(s)
        creado = None
        if not usuarios:
            creado = _crear_usuario_demo(s)
            usuarios = [creado]

        resumenes = [sembrar_usuario(s, u) for u in usuarios]

    print("Seed de Q/A visual (WS25) — usuarios demo|:")
    if creado is not None:
        print(f"  · no había ninguno: creé {creado.firebase_uid} "
              f"(apodo {DEMO_APODO}, términos aceptados)")
    for r in resumenes:
        if r["saltado"]:
            print(f"  · {r['uid']}: ya tenía {r['pausas']} Pausas sembradas — no toqué nada")
            continue
        print(
            f"  · {r['uid']} ({r['plan']}): {r['pausas']} Pausas · "
            f"{r['reflexiones']} con reflexión · {r['estrellas']} con estrellas · "
            f"{r['fotos']} fotos en {r['pausas_con_fotos']} Pausas · "
            f"{r['compartidas']} compartidas / {r['pausas'] - r['compartidas']} privadas · "
            f"links: {', '.join(r['links'])}"
        )
    return resumenes


def main() -> int:
    sembrar()
    return 0


if __name__ == "__main__":
    sys.exit(main())

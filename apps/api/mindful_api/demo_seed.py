"""WS25 + WS27 · Q/A visual — siembra Pausas y cartas de comunidad de VERDAD
para los usuarios `demo|` locales.

Tomás abre la app en su navegador y tiene que ver el Baúl lleno, con reflexiones de
largos distintos, estrellas, fotos, fichas compartidas y links ya enviados. Este
módulo crea exactamente eso, pasando por los mismos servicios que usa la API (fotos
por `services/fotos`, links por `services/compartir`), para que lo sembrado sea
indistinguible de lo vivido: mismo `storage_path` canónico, mismo cupo por plan.

WS27 · B2.1 suma el Bloque B: por cada usuario demo, CUATRO cartas propuestas —
una por estado visible (en evaluación · necesita un retoque · no aprobada ·
cargada a la comunidad)—, cada una con su historial de redacciones para el funnel
del adminland, la carta aprobada ya publicada en el mazo con su firma, los avisos
de cada transición (uno sin leer, para que la campana muestre un 1) y tres
comentarios privados de cartas para /admin › comentarios.

Uso:  make demo-seed        (o: python -m mindful_api.demo_seed desde apps/api)

Tres candados:
1. SOLO LOCAL: aborta si `settings.auth_mode == "firebase"` (o sea, si esta config
   apunta a un despliegue real). Sembrar Pausas falsas en producción sería mentirle
   al usuario sobre su propia historia.
2. SOLO USUARIOS `demo|`: nadie más se toca. Es la misma frontera que respeta el
   `conftest` de los tests y los targets `premium-demo` / `free-demo`.
3. IDEMPOTENTE: cada Pausa sembrada queda marcada en `descartadas` con `MARCA`.
   Correrlo dos veces no duplica nada (y `descartadas` con un id inexistente lo
   ignora el motor de selección, así que la marca no ensucia el historial). Las
   cartas de la comunidad tienen su propia marca (`MARCA_CC` en el `concepto`),
   así que se siembran aunque las Pausas ya estuvieran — y si la suite de tests
   borró del mazo la carta publicada (limpia todo `origen != dwellia` para volver
   a 77), el seed la republica sin re-sembrar el resto.

Las fotos son PNG generados acá con la biblioteca estándar (`zlib` + `struct`): un
color plano por foto. Sin Pillow — no queremos una dependencia para el Q/A.
"""

from __future__ import annotations

import secrets
import struct
import sys
import zlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .db.base import SessionLocal
from .db.models import (
    AVISO_CARTA_ESTADO,
    AVISO_REENVIO,
    VINCULO_ACEPTADA,
    VINCULO_PENDIENTE,
    Guardada,
    PausaProgramada,
    Reenvio,
    Vinculo,
    ESTADO_A_REVISAR,
    ESTADO_APROBADA,
    ESTADO_RECHAZADA,
    ESTADO_REVISION_DWELLIA,
    FIRMA_ANONIMA,
    FIRMA_APODO,
    ORIGEN_COMUNIDAD,
    Aviso,
    Carta,
    CartaComunidad,
    Entrega,
    Usuario,
)
from .services.avisos import TEXTOS_ESTADO
from .services.compartir import crear_compartido
from .services.fotos import subir_foto
from .services.plan import activar_premium, limites

# La huella que hace idempotente al seed. Va en `descartadas` (JSON): no es un id de
# carta real, así que `historial_motor` la saltea sin enterarse.
MARCA = "__demo_seed_ws25__"

# WS27 · B2.1 · la huella de las cartas de comunidad sembradas. Va en el
# `concepto` de la propuesta (una etiqueta, no un texto visible) y en el id de la
# carta publicada: se ve de un vistazo en la base y no se pisa con nada real.
MARCA_CC = "demo-seed-"
PREFIJO_CARTA_DEMO = "com-demo-"

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

# ─────────────────────────────────────────────────────────────────────────────
# WS27 · B2.1 · Las cartas de la comunidad del Q/A visual.
#
# Tomás abre la pestaña Crear y tiene que ver LOS CUATRO estados visibles a la
# vez, cada uno con lo que le corresponde (la sugerencia del juez, el motivo del
# rechazo, la carta ya cargada al mazo con su firma), y en /admin el funnel de
# cada una: v1 lo que escribió → v2 lo que dijo el juez → vFinal la decisión.
#
# Los textos respetan los límites REALES del contrato (frase ≤60, prompt 100-220)
# porque el panel los vuelve a medir al aprobar: una carta sembrada fuera de
# rango le daría un 422 a Tomás en pleno Q/A.
#
# Cada entrada: (clave, estado, categoría, acción, frase, prompt, motivo,
#                veredicto, redacciones anteriores, días atrás).
# `redacciones anteriores` son las vueltas VIEJAS (la actual se arma sola con el
# texto de la fila): solo la de `a_revisar` tiene una, así que su funnel muestra
# dos versiones.
# ─────────────────────────────────────────────────────────────────────────────
_PROMPT_REVISION = (
    "Escribe en tu diario tres cosas que hoy te sostuvieron sin que las nombraras, "
    "y a cuál le darías las gracias mañana en voz alta."
)
_PROMPT_A_REVISAR_V1 = (
    "Escribe en tu diario todo lo que no pudiste terminar hoy y proponte un plan "
    "para recuperar el tiempo perdido durante el fin de semana que viene."
)
_PROMPT_A_REVISAR_V2 = (
    "Escribe en tu diario lo que quedó sin terminar hoy y arma un plan corto para "
    "recuperar el tiempo perdido antes de que arranque el fin de semana."
)
# Lo que el juez PROPONE en la segunda vuelta (la sugerencia que el autor ve).
_PROMPT_FIX = (
    "Escribe en tu diario una cosa que hoy te pesó y otra que igual pudiste "
    "sostener. Léelas juntas antes de dormir y mira cuál ocupa más lugar."
)
_PROMPT_RECHAZADA = (
    "Escribe en tu diario los tres objetivos que vas a cumplir sí o sí este mes y "
    "el castigo que te vas a poner si llegas al domingo sin haberlos cumplido."
)
_PROMPT_APROBADA = (
    "Escribe en tu diario el mensaje que hoy estuviste por mandar y no mandaste. "
    "Léelo mañana y decide si sigue haciendo falta que llegue."
)

CARTAS_COMUNIDAD = [
    (
        "revision", ESTADO_REVISION_DWELLIA, "gratitud", "contemplar",
        "Lo que te sostiene no hace ruido.",
        _PROMPT_REVISION,
        None,
        {"resultado": "aprueba", "hallazgos": [], "concepto": "gratitud-callada",
         "fix_sugerido": None, "motivo": None, "fuente": "juez"},
        [], 3,
    ),
    (
        "retoque", ESTADO_A_REVISAR, "resiliencia", "respirar",
        "Planifica hoy para no agotarte.",
        _PROMPT_A_REVISAR_V2,
        "La carta sigue pidiendo un plan. Prueba con algo que se pueda mirar hoy, "
        "sin tarea pendiente al final.",
        {"resultado": "requiere_revision",
         "hallazgos": [{"regla": "R1.3", "mayor": True,
                        "detalle": "El prompt pide un plan, no una mirada."},
                       {"regla": "R7", "mayor": False,
                        "detalle": "«el tiempo perdido» es una muletilla."}],
         "concepto": "peso-del-dia",
         "fix_sugerido": {"frase": "Hoy no tienes que poder con todo.",
                          "prompt": _PROMPT_FIX},
         "motivo": "El prompt pide un plan, no una mirada.", "fuente": "juez"},
        [("Organiza tu semana para no agotarte.",
          _PROMPT_A_REVISAR_V1)], 9,
    ),
    (
        "rechazada", ESTADO_RECHAZADA, "perspectiva", "caminar",
        "Si no lo cumples hoy, no lo harás nunca.",
        _PROMPT_RECHAZADA,
        "Dwellia no exige ni castiga: invita a mirar. Esta carta pone una condena "
        "donde tendría que haber una pregunta.",
        {"resultado": "rechaza",
         "hallazgos": [{"regla": "S3", "mayor": True,
                        "detalle": "Propone castigarse a uno mismo."},
                       {"regla": "R2.1", "mayor": True,
                        "detalle": "Da una orden en lugar de abrir una mirada."}],
         "concepto": "meta-del-mes", "fix_sugerido": None,
         "motivo": "Propone castigarse a uno mismo.", "fuente": "juez"},
        [], 16,
    ),
    (
        "aprobada", ESTADO_APROBADA, "vinculos", "hacer",
        "Hay un mensaje que estás por no mandar.",
        _PROMPT_APROBADA,
        None,
        {"resultado": "aprueba", "hallazgos": [], "concepto": "mensaje-sin-mandar",
         "fix_sugerido": None, "motivo": None, "fuente": "juez"},
        [], 24,
    ),
]

# Los comentarios privados de las cartas (lo que se escribe debajo de las
# estrellas). Van sobre Pausas YA sembradas, por posición en el Baúl ordenado de
# la más nueva a la más vieja: la 1.ª (5 ⭐), la 5.ª (2 ⭐) y la 6.ª (1 ⭐), para
# que /admin › comentarios muestre las dos puntas y no solo elogios.
COMENTARIOS = [
    (0, "Me llegó justo el día que la necesitaba. Gracias por esta."),
    (4, "Me hubiese gustado algo para hacer con alguien, no a solas."),
    (5, "Hoy no me representó. Prefiero cartas más cortas por la mañana."),
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


# ─────────────────────────────────────────────────────────────────────────────
# WS27 · B2.1 · Las cartas de la comunidad, sus avisos y los comentarios
# ─────────────────────────────────────────────────────────────────────────────
def _redaccion(version: int, frase: str, prompt: str, categoria: str, accion: str,
               firma: str, fecha: datetime) -> dict:
    """Una vuelta del historial, con la MISMA forma que escribe B1.1 en runtime."""
    return {
        "version": version, "frase": frase, "prompt": prompt,
        "categoria": categoria, "accion": accion, "firma": firma,
        "fecha": fecha.isoformat(), "por": "usuario",
    }


def _propuestas_sembradas(s: Session, usuario: Usuario) -> list:
    """Las propuestas que puso ESTE seed (por la marca en `concepto`)."""
    return list(s.scalars(
        select(CartaComunidad)
        .where(CartaComunidad.usuario_id == usuario.id)
        .where(CartaComunidad.concepto.like(MARCA_CC + "%"))
    ).all())


def _publicar_carta_demo(s: Session, usuario: Usuario, propuesta: CartaComunidad,
                         firma: str) -> Carta:
    """La carta de la propuesta aprobada, ya en el mazo (Mundo 1, origen comunidad).

    Es lo que hace `services/admin.aprobar` cuando Tomás aprueba, con la misma
    forma: id propio, `origen=comunidad`, autor y la firma CONGELADA (el apodo de
    hoy, o None si el autor eligió anónima).
    """
    carta = Carta(
        id=PREFIJO_CARTA_DEMO + secrets.token_hex(4),
        categoria_slug=propuesta.categoria_slug,
        accion_slug=propuesta.accion_slug,
        concepto=propuesta.concepto,
        frase=propuesta.frase,
        prompt=propuesta.prompt,
        origen=ORIGEN_COMUNIDAD,
        autor_usuario_id=usuario.id,
        firma_publica=(usuario.apodo if firma == FIRMA_APODO else None),
    )
    s.add(carta)
    s.flush()                       # la FK `carta_id` necesita la fila escrita
    return carta


def _sembrar_impacto(s: Session, carta: Carta, autor: Usuario) -> int:
    """WS28 · B2.2 · el impacto de la carta cargada: a quién le llegó y qué puntaje tuvo.

    Hasta tres lectores (otros usuarios `demo|`; si no hay, el propio autor, que
    también puede recibir su carta) con estrellas 5, 4 y una sin puntuar, así la
    pestaña Crear muestra "3 personas la recibieron · ★ 4,5 · 2 valoraciones".
    Idempotente: si la carta ya tiene entregas, no se toca. Fechas de hace 40+
    días para no chocar con las 9 Pausas sembradas de cada usuario.
    """
    ya = s.scalar(select(func.count(Entrega.id)).where(Entrega.carta_id == carta.id))
    if ya:
        return 0
    otros = [u for u in _usuarios_demo(s) if u.id != autor.id][:3]
    lectores = otros or [autor]
    puntajes = [5, 4, None]
    ahora = datetime.now(timezone.utc)
    for i, lector in enumerate(lectores):
        s.add(Entrega(
            usuario_id=lector.id, carta_id=carta.id,
            fecha=ahora - timedelta(days=40 + i),
            estrellas=puntajes[i], completada=True,
            descartadas=[MARCA],
        ))
    s.commit()
    return len(lectores)


def sembrar_comunidad(s: Session, usuario: Usuario) -> dict:
    """Las 4 propuestas (una por estado visible), sus avisos y 3 comentarios.

    Idempotente por la marca `demo-seed-` en `concepto`. Y ADEMÁS se auto-repara:
    la suite de tests limpia del mazo toda carta con `origen != dwellia` (para que
    el mazo vuelva a 77), así que después de correr los tests la propuesta
    aprobada se queda sin su carta publicada. En ese caso el seed no re-siembra
    todo: republica solo la carta que falta y vuelve a apuntarla.
    """
    ya = _propuestas_sembradas(s, usuario)
    resumen = {"propuestas": 0, "avisos": 0, "comentarios": 0, "lectores": 0,
               "carta_publicada": None, "republicada": False, "saltado": False}

    firma = FIRMA_APODO if (usuario.apodo or "").strip() else FIRMA_ANONIMA
    ahora = datetime.now(timezone.utc)

    if ya:
        resumen["saltado"] = True
        resumen["propuestas"] = len(ya)
        # ¿Le falta la carta al aprobado? (los tests la borran)
        for propuesta in ya:
            if propuesta.estado != ESTADO_APROBADA:
                continue
            carta = (s.get(Carta, propuesta.carta_id) if propuesta.carta_id else None)
            if carta is None:
                carta = _publicar_carta_demo(s, usuario, propuesta, propuesta.firma)
                propuesta.carta_id = carta.id
                s.add(propuesta)
                s.commit()
                resumen["republicada"] = True
            resumen["carta_publicada"] = carta.id
            resumen["lectores"] = _sembrar_impacto(s, carta, usuario)
        return resumen

    for (clave, estado, categoria, accion, frase, prompt, motivo, veredicto,
         anteriores, dias) in CARTAS_COMUNIDAD:
        creada = ahora - timedelta(days=dias)
        propuesta = CartaComunidad(
            usuario_id=usuario.id,
            categoria_slug=categoria, accion_slug=accion,
            frase=frase, prompt=prompt,
            firma=firma, estado=estado,
            veredicto=veredicto, motivo=motivo,
            concepto=MARCA_CC + clave,
            cesion_aceptada_at=creada,      # sin cesión, aprobar responde 409
            created_at=creada,
            updated_at=creada,
        )
        # El funnel: primero las vueltas viejas, después la redacción de AHORA.
        historial = [
            _redaccion(i + 1, f, p, categoria, accion, firma,
                       creada - timedelta(days=len(anteriores) - i))
            for i, (f, p) in enumerate(anteriores)
        ]
        historial.append(_redaccion(len(anteriores) + 1, frase, prompt,
                                    categoria, accion, firma, creada))
        propuesta.historial = historial
        s.add(propuesta)
        s.commit()
        s.refresh(propuesta)
        resumen["propuestas"] += 1

        if estado == ESTADO_APROBADA:
            carta = _publicar_carta_demo(s, usuario, propuesta, firma)
            propuesta.carta_id = carta.id
            s.add(propuesta)
            s.commit()
            resumen["carta_publicada"] = carta.id
            resumen["lectores"] = _sembrar_impacto(s, carta, usuario)

        # El aviso, con el MISMO texto canónico que escribe la app
        # (`services/avisos.TEXTOS_ESTADO`). La fila se arma acá y no con
        # `crear_aviso` por dos razones: el seed elige la fecha (para que la
        # campana tenga un orden creíble) y no manda un push por algo que nunca
        # pasó de verdad. `revision_dwellia` no avisa: para el autor sigue "en
        # proceso de evaluación".
        texto = TEXTOS_ESTADO.get(estado)
        if texto:
            s.add(Aviso(
                usuario_id=usuario.id, tipo=AVISO_CARTA_ESTADO,
                referencia_id=propuesta.id, texto=texto,
                # Solo el último (la carta cargada) queda SIN LEER: la campana
                # tiene que mostrar un 1, no una lista entera en negrita.
                leido=(estado != ESTADO_APROBADA),
                created_at=creada,
            ))
            s.commit()
            resumen["avisos"] += 1

    # Los comentarios privados de las cartas, sobre Pausas ya sembradas.
    sembradas = [
        e for e in s.scalars(
            select(Entrega)
            .where(Entrega.usuario_id == usuario.id)
            .order_by(Entrega.fecha.desc())
        ).all()
        if e.descartadas and MARCA in e.descartadas
    ]
    for indice, texto in COMENTARIOS:
        if indice >= len(sembradas):
            continue
        entrega = sembradas[indice]
        if entrega.comentario_carta:            # ya tiene uno: no se pisa
            continue
        entrega.comentario_carta = texto
        s.add(entrega)
        resumen["comentarios"] += 1
    if resumen["comentarios"]:
        s.commit()

    return resumen


# ─────────────────────────────────────────────────────────────────────────────
# WS29 · Bloque C · Dos personas fijas y la comunidad de cada usuario demo|
# ─────────────────────────────────────────────────────────────────────────────
# uid · email · apodo · nombre · apellido · perfil público · premium
PERSONAS_DEMO = (
    ("demo|lu", "lu@dwellia.local", "Lu", "Lucía", "Pérez", True, True),
    ("demo|mar", "mar@dwellia.local", "Mar", "Martín", "Sosa", False, False),
)
UIDS_PERSONAS = {p[0] for p in PERSONAS_DEMO}
TEXTO_REENVIO = "Lu te envió una Pausa."


def _personas_demo(s: Session) -> list:
    """Lu (pública, premium) y Mar (privado, free): existen siempre, con sus datos
    fijos. Sus Pausas las siembra `sembrar_usuario` como a cualquier demo|."""
    ahora = datetime.now(timezone.utc)
    personas = []
    for uid, email, apodo, nombre, apellido, publico, premium in PERSONAS_DEMO:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == uid))
        if u is None:
            u = Usuario(firebase_uid=uid, email=email, terminos_aceptados_at=ahora)
            s.add(u)
        u.apodo, u.nombre, u.apellido, u.perfil_publico = apodo, nombre, apellido, publico
        if premium and not limites(u).plan == "premium":
            activar_premium(u, ahora + timedelta(days=365))
        s.commit()
        s.refresh(u)
        personas.append(u)
    return personas


def _compartidas_de(s: Session, usuario: Usuario) -> list:
    return s.scalars(
        select(Entrega)
        .where(Entrega.usuario_id == usuario.id, Entrega.completada.is_(True),
               Entrega.visibilidad == "compartida", Entrega.extra.is_(False))
        .order_by(Entrega.fecha.desc())
    ).all()


def _vinculo(s: Session, a: Usuario, b: Usuario, estado: str) -> bool:
    """Crea el vínculo a→b si no hay ninguno entre los dos. True si lo creó."""
    existe = s.scalar(select(Vinculo).where(
        ((Vinculo.solicitante_id == a.id) & (Vinculo.destinatario_id == b.id))
        | ((Vinculo.solicitante_id == b.id) & (Vinculo.destinatario_id == a.id))
    ))
    if existe is not None:
        return False
    ahora = datetime.now(timezone.utc)
    s.add(Vinculo(solicitante_id=a.id, destinatario_id=b.id, estado=estado,
                  aceptada_at=ahora if estado == VINCULO_ACEPTADA else None))
    s.commit()
    return True


def sembrar_vinculos(s: Session, usuario: Usuario, lu: Usuario, mar: Usuario) -> dict:
    """Para UN usuario demo| del navegador: Lu es su comunidad (aceptada), Mar le
    pidió (pendiente, recibida), Lu le reenvió una Pausa (sin leer), tiene una
    Pausa de Lu guardada y una programada de Lu como próxima carta. Idempotente:
    cada pieza se crea solo si falta."""
    r = {"vinculo": False, "solicitud": False, "reenvio": False, "guardada": False,
         "programada": False}
    if usuario.firebase_uid in UIDS_PERSONAS:
        return r
    r["vinculo"] = _vinculo(s, usuario, lu, VINCULO_ACEPTADA)
    r["solicitud"] = _vinculo(s, mar, usuario, VINCULO_PENDIENTE)

    de_lu = _compartidas_de(s, lu)
    if len(de_lu) < 3:
        return r                                   # Lu todavía sin Pausas: nada que reenviar
    ahora = datetime.now(timezone.utc)

    # Reenvío (la primera compartida de Lu) + su aviso, sin leer.
    if s.scalar(select(Reenvio).where(Reenvio.a_usuario_id == usuario.id,
                                      Reenvio.de_usuario_id == lu.id)) is None:
        s.add(Reenvio(de_usuario_id=lu.id, a_usuario_id=usuario.id,
                      entrega_id=de_lu[0].id, created_at=ahora - timedelta(hours=3)))
        s.add(Aviso(usuario_id=usuario.id, tipo=AVISO_REENVIO, referencia_id=de_lu[0].id,
                    texto=TEXTO_REENVIO, leido=False,
                    created_at=ahora - timedelta(hours=3)))
        s.commit()
        r["reenvio"] = True

    # Guardada (la segunda).
    if s.scalar(select(Guardada).where(Guardada.usuario_id == usuario.id,
                                       Guardada.entrega_id == de_lu[1].id)) is None:
        s.add(Guardada(usuario_id=usuario.id, entrega_id=de_lu[1].id))
        s.commit()
        r["guardada"] = True

    # Programada (la tercera): será la próxima carta del día de este usuario.
    if s.scalar(select(PausaProgramada).where(PausaProgramada.usuario_id == usuario.id,
                                              PausaProgramada.servida_at.is_(None))) is None:
        s.add(PausaProgramada(usuario_id=usuario.id, carta_id=de_lu[2].carta_id,
                              de_usuario_id=lu.id, entrega_origen_id=de_lu[2].id))
        s.commit()
        r["programada"] = True
    return r


def sembrar() -> list:
    if settings.auth_mode == "firebase":
        raise SystemExit(
            "demo_seed es SOLO local: con MINDFUL_AUTH_MODE=firebase esta config "
            "apunta a un despliegue real y no se siembra nada."
        )

    with SessionLocal() as s:
        lu, mar = _personas_demo(s)              # WS29: siempre existen
        usuarios = _usuarios_demo(s)
        creado = None
        if all(u.firebase_uid in UIDS_PERSONAS for u in usuarios):
            creado = _crear_usuario_demo(s)
            usuarios = _usuarios_demo(s)

        resumenes = []
        for u in usuarios:
            resumen = sembrar_usuario(s, u)
            # WS27 · B2.1: las cartas de la comunidad tienen su PROPIA marca de
            # idempotencia, así que se siembran aunque las Pausas ya estuvieran.
            resumen["comunidad"] = sembrar_comunidad(s, u)
            resumenes.append(resumen)
        # WS29 · Bloque C: recién ahora, con las Pausas de Lu ya sembradas.
        for u, resumen in zip(usuarios, resumenes):
            resumen["vinculos"] = sembrar_vinculos(s, u, lu, mar)

    print("Seed de Q/A visual (WS25 + WS27 + WS29) — usuarios demo|:")
    if creado is not None:
        print(f"  · no había ninguno: creé {creado.firebase_uid} "
              f"(apodo {DEMO_APODO}, términos aceptados)")
    for r in resumenes:
        if r["saltado"]:
            print(f"  · {r['uid']}: ya tenía {r['pausas']} Pausas sembradas — no toqué nada")
        else:
            print(
                f"  · {r['uid']} ({r['plan']}): {r['pausas']} Pausas · "
                f"{r['reflexiones']} con reflexión · {r['estrellas']} con estrellas · "
                f"{r['fotos']} fotos en {r['pausas_con_fotos']} Pausas · "
                f"{r['compartidas']} compartidas / {r['pausas'] - r['compartidas']} privadas · "
                f"links: {', '.join(r['links'])}"
            )
        c = r["comunidad"]
        if c["saltado"]:
            extra = (f" — republiqué la carta del mazo ({c['carta_publicada']}), "
                     "se la habían borrado" if c["republicada"] else " — no toqué nada")
            print(f"      comunidad: ya tenía {c['propuestas']} cartas propuestas{extra}")
        else:
            print(
                f"      comunidad: {c['propuestas']} cartas propuestas "
                f"(en evaluación · necesita un retoque · no aprobada · cargada) · "
                f"{c['avisos']} avisos (1 sin leer) · {c['comentarios']} comentarios · "
                f"carta en el mazo: {c['carta_publicada']}"
            )
        v = r.get("vinculos") or {}
        if any(v.values()):
            piezas = [k for k, ok in v.items() if ok]
            print(f"      comunidad C: creé {', '.join(piezas)} (Lu pública+premium · Mar privado)")
        elif r["uid"] not in UIDS_PERSONAS:
            print("      comunidad C: ya tenía vínculo, solicitud, reenvío, guardada y programada")
    return resumenes


def main() -> int:
    sembrar()
    return 0


if __name__ == "__main__":
    sys.exit(main())

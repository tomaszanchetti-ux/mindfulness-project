#!/usr/bin/env python3
"""Motor de validación de cartas (WS17) — el gate de calidad de M0.

Valida cartas contra el canon ejecutable (`M0_Motor_de_Contenido/canon_cartas.md`)
en dos capas:

  CAPA 1 · determinística (siempre, gratis, sin dependencias):
    estructura, matriz de afinidad, diario presente, longitudes, localismos,
    muletillas de mazo, conectores de diario, similitud entre cartas, conceptos.

  CAPA 2 · LLM-judge (opcional, `--judge`): Claude evalúa cada carta contra el
    rubric completo (coherencia frase↔prompt, poética, clichés, cuidado emocional,
    concepto, safety) con salida estructurada `aprueba / requiere_revision / rechaza`.
    Necesita ANTHROPIC_API_KEY y `pip install anthropic`.

Desde la WS27 (B1.2) las DOS capas viven en el backend — `mindful_api.services.canon`
y `mindful_api.services.juez` — y este script es su interfaz de línea de comandos:
una regla, un solo lugar. El runtime de las cartas de la comunidad usa exactamente
el mismo código (`juez.evaluar`).

Usos (desde la raíz del repo, con el intérprete del backend — el motor vive ahí):
  apps/api/.venv/bin/python scripts/validar_cartas.py                 # capa 1, mazo
  apps/api/.venv/bin/python scripts/validar_cartas.py --judge         # capa 1 + judge
  apps/api/.venv/bin/python scripts/validar_cartas.py --carta x.json  # UNA candidata
                                                     # (el flujo premium de cartas
                                                     # de usuarios entra por acá)

`--carta` corre la MISMA capa 1 que el runtime (`canon.validar_candidata`): los
límites de la comunidad (frase ≤60 · prompt 100-220), sin pedir `concepto` —el
autor no lo escribe, lo sugiere el juez— y con los parecidos contra el mazo real.

Salida: informe legible + exit code 1 si algo frena la carta (errores duros, o un
parecido por encima del umbral en el camino `--carta`), 2 si el JSON de `--carta`
está mal formado. Sirve de gate en CI.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATA = RAIZ / "M0_Motor_de_Contenido" / "data"

# El motor vive en el backend (WS27 · B1.2): se importa desde `apps/api`.
sys.path.insert(0, str(RAIZ / "apps" / "api"))

from mindful_api.services.canon import (  # noqa: E402
    validar_candidata,
    validar_deterministica,
)
from mindful_api.services.juez import ESQUEMA_VEREDICTO, juzgar_lote  # noqa: E402,F401

CAMPOS_CANDIDATA = ("categoria", "accion", "frase", "prompt")


def _morir(mensaje: str) -> "SystemExit":
    """Un mensaje legible en stderr y exit 2. Nunca un traceback en la cara."""
    print(f"🔴 {mensaje}", file=sys.stderr)
    return SystemExit(2)


def _leer_candidata(ruta: str) -> dict:
    """El JSON de la candidata, o un mensaje claro y exit 2.

    El `concepto` NO se pide: el autor no lo escribe, lo sugiere el juez.
    """
    try:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise _morir(f"no existe el archivo: {ruta}")
    except json.JSONDecodeError as e:
        raise _morir(f"{ruta} no es un JSON válido: {e}")
    if not isinstance(datos, dict):
        raise _morir(f"{ruta} tiene que ser un objeto JSON con los campos "
                     + ", ".join(CAMPOS_CANDIDATA))
    return datos


def _informe_candidata(candidata: dict, mazo: list, categorias: set,
                       acciones: set) -> dict:
    """La CAPA 1 DEL RUNTIME sobre una candidata: la misma que corre el juez.

    Una regla, un solo lugar: acá se aplican los límites de la comunidad (frase
    ≤60 · prompt 100-220), no los del mazo propio (75/300), y no se exige
    `concepto`. Un parecido por encima del umbral frena la carta igual que un
    error duro — es lo que hace `InformeCandidata.limpia()` en el runtime.
    """
    inf = validar_candidata(candidata, mazo, categorias, acciones)
    return {
        "errores": [f"[{e['regla']}] {e['detalle']}" for e in inf.errores],
        "avisos": [f"[{a['regla']}] {a['detalle']}" for a in inf.avisos],
        "similares": [
            "se parece a la carta {id} ({campo}, {pct:.0%} de coincidencia)".format(
                id=s["id"], campo=s["campo"], pct=s["similitud"])
            for s in inf.similares
        ],
        "frena": not inf.limpia(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Validador de cartas Dwellia (canon WS17)")
    ap.add_argument("--carta", help="JSON con UNA carta candidata (modo alta de carta nueva)")
    ap.add_argument("--judge", action="store_true", help="correr también la capa LLM-judge")
    ap.add_argument("--model", default="claude-opus-4-8", help="modelo del judge")
    ap.add_argument("--json", action="store_true", help="salida JSON (para integrar)")
    args = ap.parse_args()

    mazo = json.loads((DATA / "cartas.json").read_text(encoding="utf-8"))
    categorias = {c["slug"] for c in json.loads((DATA / "categorias.json").read_text(encoding="utf-8"))}
    acciones = {a["slug"] for a in json.loads((DATA / "acciones.json").read_text(encoding="utf-8"))}

    if args.carta:
        # UNA candidata de la comunidad → la capa 1 DEL RUNTIME (`validar_candidata`),
        # exactamente la que corre `juez.evaluar`: mismos límites, mismas reglas.
        candidata = _leer_candidata(args.carta)
        candidata.setdefault("id", "(candidata)")
        a_validar = [candidata]
        informe = _informe_candidata(candidata, mazo, categorias, acciones)
    else:
        a_validar = mazo
        inf = validar_deterministica(mazo, categorias, acciones)
        informe = {
            "errores": list(inf.errores), "avisos": list(inf.avisos),
            "similares": [], "observaciones": list(inf.observaciones),
            "frena": bool(inf.errores),
        }
    informe.setdefault("observaciones", [])

    veredictos = []
    if args.judge:
        # Sin --carta = mazo aprobado → modo regresión. Con --carta = alta nueva.
        modo_regresion = not args.carta
        etiqueta = "regresión sobre el mazo" if modo_regresion else "alta de candidata"
        print(f"— capa judge ({args.model}) · modo {etiqueta} · {len(a_validar)} carta(s) —")
        veredictos = juzgar_lote(a_validar, mazo, args.model, modo_regresion=modo_regresion)

    if args.json:
        print(json.dumps({
            "errores": informe["errores"], "avisos": informe["avisos"],
            "similares": informe["similares"],
            "observaciones": informe["observaciones"], "judge": veredictos,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"\n=== VALIDADOR DE CARTAS · {len(a_validar)} carta(s) ===")
        secciones = [("ERRORES (gate)", informe["errores"], "🔴"),
                     ("AVISOS (revisar)", informe["avisos"], "🟡")]
        if args.carta:   # los parecidos son del camino de la candidata
            secciones.append(("PARECIDOS (R5 · frenan)", informe["similares"], "🟠"))
        secciones.append(("OBSERVACIONES", informe["observaciones"], "·"))
        for titulo, lista, marca in secciones:
            print(f"\n{titulo}: {len(lista)}")
            for item in lista:
                print(f"  {marca} {item}")
        if args.judge and veredictos:
            problematicas = [v for v in veredictos if v["veredicto"] != "aprueba"]
            print(f"\nJUDGE: {len(veredictos) - len(problematicas)} aprueban · "
                  f"{len(problematicas)} con reparos")
            for v in problematicas:
                print(f"\n  {v['id']} → {v['veredicto']}")
                for h in v["hallazgos"]:
                    print(f"    [{h['regla']}{' · mayor' if h['mayor'] else ''}] {h['detalle']}")
                if v.get("fix_sugerido"):
                    print(f"    fix → frase: «{v['fix_sugerido']['frase']}»")
                    print(f"          prompt: «{v['fix_sugerido']['prompt']}»")

    rechazadas = [v for v in veredictos if v["veredicto"] == "rechaza"]
    return 1 if (informe["frena"] or rechazadas) else 0


if __name__ == "__main__":
    sys.exit(main())

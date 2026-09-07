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

Salida: informe legible + exit code 1 si hay errores (sirve de gate en CI).
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

from mindful_api.services.canon import validar_deterministica  # noqa: E402
from mindful_api.services.juez import ESQUEMA_VEREDICTO, juzgar_lote  # noqa: E402,F401


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
        candidata = json.loads(Path(args.carta).read_text(encoding="utf-8"))
        candidata.setdefault("id", "(candidata)")
        a_validar = [candidata]
        universo = mazo + [candidata]  # similitud/conceptos contra el mazo real
    else:
        a_validar = mazo
        universo = mazo

    inf = validar_deterministica(universo, categorias, acciones)

    veredictos = []
    if args.judge:
        # Sin --carta = mazo aprobado → modo regresión. Con --carta = alta nueva.
        modo_regresion = not args.carta
        etiqueta = "regresión sobre el mazo" if modo_regresion else "alta de candidata"
        print(f"— capa judge ({args.model}) · modo {etiqueta} · {len(a_validar)} carta(s) —")
        veredictos = juzgar_lote(a_validar, mazo, args.model, modo_regresion=modo_regresion)

    if args.json:
        print(json.dumps({
            "errores": inf.errores, "avisos": inf.avisos,
            "observaciones": inf.observaciones, "judge": veredictos,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"\n=== VALIDADOR DE CARTAS · {len(a_validar)} carta(s) ===")
        for titulo, lista, marca in (("ERRORES (gate)", inf.errores, "🔴"),
                                     ("AVISOS (revisar)", inf.avisos, "🟡"),
                                     ("OBSERVACIONES", inf.observaciones, "·")):
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
    return 1 if (inf.errores or rechazadas) else 0


if __name__ == "__main__":
    sys.exit(main())

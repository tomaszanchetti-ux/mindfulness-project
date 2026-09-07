// WS27 · B2.2 · La carta en miniatura de una lista.
//
// Mismo gesto que la ficha del Baúl (`.ficha-mini` en EntryDetail): se ve el
// pilar por su banda y su dibujo, y al tocarla la carta se abre en grande con su
// giro de siempre — el mismo componente `Card`, nunca un render aparte.
//
// Vive como componente porque la usan la pestaña Crear (tus cartas) y el
// adminland (la cola de aprobación).

import { useState } from "react";
import { Card } from "./Card";
import { assetUrl } from "../lib/api";
import type { Carta } from "../lib/types";

interface Props {
  carta: Carta;
  /** Etiqueta accesible; por defecto, la de siempre. */
  etiqueta?: string;
}

export function CartaMini({ carta, etiqueta = "Ver la carta en grande" }: Props) {
  const [abierta, setAbierta] = useState(false);
  // En grande arranca por el DORSO: lo que importa de una carta es su frase.
  const [flipped, setFlipped] = useState(true);
  const accent = carta.categoria?.color_accent || "var(--sand-line)";

  return (
    <>
      <button
        type="button"
        className="carta-mini"
        aria-label={etiqueta}
        onClick={() => {
          setFlipped(true);
          setAbierta(true);
        }}
      >
        <span className="carta-mini-band" style={{ background: accent }} />
        {carta.categoria?.img && (
          <img className="carta-mini-dibujo" src={assetUrl(carta.categoria.img)} alt="" />
        )}
      </button>

      {abierta && (
        <div className="lightbox" onClick={() => setAbierta(false)}>
          <div className="lightbox-carta" onClick={(e) => e.stopPropagation()}>
            <Card carta={carta} flipped={flipped} onFlip={() => setFlipped((f) => !f)} />
          </div>
          <button className="lightbox-close" aria-label="Cerrar">
            ×
          </button>
        </div>
      )}
    </>
  );
}

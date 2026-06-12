// La carta — el objeto central del sistema (doc §11).
// Frente: pilar · dibujo · acción.  Dorso (canon WS22, los dos tiempos):
// frase (la puerta) · acción inicial (glifo + nombre) · prompt · pluma (el
// sello del cierre: toda pausa termina escribiendo en el diario).
// El giro es la metáfora de "descubrir": lento, suave, sin rebote (§11.6).

import { assetUrl } from "../lib/api";
import type { Carta } from "../lib/types";

interface CardProps {
  carta: Carta;
  flipped: boolean;
  onFlip?: () => void;
}

export function Card({ carta, flipped, onFlip }: CardProps) {
  const accent = carta.categoria.color_accent;
  const catText = carta.categoria.color_text;

  return (
    <div className="card-scene">
      <div
        className={`card-flip ${flipped ? "is-flipped" : ""}`}
        role={onFlip ? "button" : undefined}
        tabIndex={onFlip ? 0 : undefined}
        aria-label={onFlip ? (flipped ? "Ver el frente de la carta" : "Ver el dorso de la carta") : undefined}
        onClick={onFlip}
        onKeyDown={(e) => {
          if (onFlip && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            onFlip();
          }
        }}
      >
        {/* —— Frente —— */}
        <div className="card-face card-front">
          <div className="card-band" style={{ background: accent }} />
          <div className="card-cat" style={{ color: catText }}>
            {carta.categoria.nombre.toLowerCase()}
          </div>
          <div className="card-draw">
            <img src={assetUrl(carta.categoria.img)} alt="" />
          </div>
          <div className="card-action">{carta.accion.nombre.toLowerCase()}</div>
        </div>

        {/* —— Dorso (los dos tiempos de la pausa) —— */}
        <div className="card-face card-back">
          <div className="card-band" style={{ background: accent }} />
          <div className="frase card-frase">{carta.frase}</div>
          <div className="card-accion-inicial" aria-hidden>
            <div
              className="card-glyph"
              style={{
                background: accent,
                WebkitMaskImage: `url(${assetUrl(carta.accion.glifo)})`,
                maskImage: `url(${assetUrl(carta.accion.glifo)})`,
              }}
            />
            <span className="card-accion-nombre">
              {carta.accion.nombre.toLowerCase()}
            </span>
          </div>
          <div className="card-prompt">{carta.prompt}</div>
          <div
            className="card-sello"
            style={{
              background: accent,
              WebkitMaskImage: `url(${assetUrl("assets/acciones/act_escribir.svg")})`,
              maskImage: `url(${assetUrl("assets/acciones/act_escribir.svg")})`,
            }}
            aria-hidden
          />
        </div>
      </div>
    </div>
  );
}

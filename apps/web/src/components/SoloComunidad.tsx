// WS27 · B2.2 · El pop-up "esto es de la comunidad".
//
// Aparece cuando alguien free toca algo que sostienen las personas que son parte
// (hoy: escribir cartas · en el Bloque C: las recomendaciones del Baúl). Por eso
// es un componente y no un texto pegado en la pantalla de Crear.
//
// Tono de `Premium.tsx`: se INVITA, nunca se exige. Sin urgencia, sin precio en
// el botón, sin "mejora ya". Y siempre con una salida tranquila ("Ahora no").

import { useNavigate } from "react-router-dom";
import { Button } from "./Button";

interface Props {
  /** El título del pop-up. Nombra lo que se está tocando, no lo que falta. */
  titulo?: string;
  /** Una línea de porqué. Cuenta qué sostiene ser parte. */
  cuerpo?: string;
  onClose: () => void;
}

export function SoloComunidad({
  titulo = "Escribir cartas es parte de la comunidad",
  cuerpo = "Las cartas de Dwellia las escriben personas que sostienen este lugar sin anuncios. Si eres parte, tus palabras pueden ser la Pausa de alguien más.",
  onClose,
}: Props) {
  const navigate = useNavigate();

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        onClick={(e) => e.stopPropagation()}
      >
        <h3>{titulo}</h3>
        <p>{cuerpo}</p>
        <div className="modal-actions">
          <Button variant="primary" full onClick={() => navigate("/premium")}>
            Quiero ser parte
          </Button>
          <Button variant="tertiary" onClick={onClose}>
            Ahora no
          </Button>
        </div>
      </div>
    </div>
  );
}

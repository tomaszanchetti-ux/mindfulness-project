// Mini instructivo para instalar la PWA en iPhone (WS19). En iOS no existe el
// prompt nativo de instalación: hay que hacerlo a mano desde Safari, y casi
// nadie conoce el camino. Tres pasos ilustrados, espejo del que tenía el Prode.

import { Button } from "./Button";

type Props = {
  onClose: () => void;
};

export function InstallIOSModal({ onClose }: Props) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Instala Dwellia en tu iPhone</h3>
        <p>Tres pasos desde Safari:</p>
        <ol className="install-steps">
          <li className="install-step">
            <span className="install-step-n">1</span>
            <IconCompartir />
            <span>
              Toca el botón <b>Compartir</b> en la barra de Safari.
            </span>
          </li>
          <li className="install-step">
            <span className="install-step-n">2</span>
            <IconAnadir />
            <span>
              Desliza y elige <b>Añadir a pantalla de inicio</b>.
            </span>
          </li>
          <li className="install-step">
            <span className="install-step-n">3</span>
            <IconListo />
            <span>
              Toca <b>Añadir</b> arriba a la derecha. Listo.
            </span>
          </li>
        </ol>
        <p className="install-note">
          ¿No ves el botón Compartir? Abre dwellia-app.web.app en <b>Safari</b>
          {" "}(en iPhone, otros navegadores no permiten instalar).
        </p>
        <div className="modal-actions">
          <Button variant="primary" full onClick={onClose}>
            Entendido
          </Button>
        </div>
      </div>
    </div>
  );
}

// Íconos en línea fina, mismo trazo que StoryArt (stroke currentColor).
const iconProps = {
  width: 22,
  height: 22,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

function IconCompartir() {
  return (
    <svg {...iconProps}>
      <path d="M12 3v12" />
      <path d="m7 8 5-5 5 5" />
      <path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7" />
    </svg>
  );
}

function IconAnadir() {
  return (
    <svg {...iconProps}>
      <rect x="3" y="3" width="18" height="18" rx="4" />
      <path d="M12 8v8" />
      <path d="M8 12h8" />
    </svg>
  );
}

function IconListo() {
  return (
    <svg {...iconProps}>
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

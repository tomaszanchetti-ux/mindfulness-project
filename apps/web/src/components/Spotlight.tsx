// Spotlight: oscurece la pantalla, recorta/resalta el elemento objetivo y muestra
// el globo explicativo al lado. Si no hay objetivo, centra el globo (paso final).
// Patrón de "product tour": el resto de la pantalla queda inerte (el overlay captura
// los clics); solo se avanza con los botones del globo.

import { useEffect, useLayoutEffect, useState } from "react";
import { Button } from "./Button";

interface SpotlightProps {
  targetSelector: string | null;
  titulo: string;
  cuerpo: string;
  paso: number; // índice 0-based
  total: number;
  esFinal: boolean;
  ctaSiguiente: string;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
}

interface Rect {
  top: number;
  left: number;
  width: number;
  height: number;
}

const PAD = 8; // aire alrededor del elemento resaltado

// Busca el elemento y devuelve su rect; reintenta hasta que aparezca (tras navegar)
// y se reposiciona en resize/scroll. La key cambia con el selector → re-mide por paso.
function useTargetRect(selector: string | null): Rect | null {
  const [rect, setRect] = useState<Rect | null>(null);

  useLayoutEffect(() => {
    if (!selector) {
      setRect(null);
      return;
    }
    let raf = 0;
    let tries = 0;
    let cancelado = false;

    const medir = () => {
      const el = document.querySelector(selector);
      if (el) {
        const r = el.getBoundingClientRect();
        setRect({ top: r.top, left: r.left, width: r.width, height: r.height });
        return true;
      }
      return false;
    };

    const loop = () => {
      if (cancelado) return;
      if (!medir() && tries++ < 90) raf = requestAnimationFrame(loop);
    };
    loop();

    const onMove = () => medir();
    window.addEventListener("resize", onMove);
    window.addEventListener("scroll", onMove, true);
    return () => {
      cancelado = true;
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onMove);
      window.removeEventListener("scroll", onMove, true);
    };
  }, [selector]);

  return rect;
}

export function Spotlight({
  targetSelector,
  titulo,
  cuerpo,
  paso,
  total,
  esFinal,
  ctaSiguiente,
  onNext,
  onPrev,
  onSkip,
}: SpotlightProps) {
  const rect = useTargetRect(targetSelector);
  const [vh, setVh] = useState(() => window.innerHeight);

  useEffect(() => {
    const onR = () => setVh(window.innerHeight);
    window.addEventListener("resize", onR);
    return () => window.removeEventListener("resize", onR);
  }, []);

  // hueco resaltado (con aire), acotado a la pantalla.
  const hole = rect
    ? {
        x: Math.max(rect.left - PAD, 4),
        y: Math.max(rect.top - PAD, 4),
        w: rect.width + PAD * 2,
        h: rect.height + PAD * 2,
      }
    : null;

  // El globo va del lado con más lugar (arriba o abajo del objetivo), acotado en alto
  // para que nunca se salga de pantalla. Sin objetivo, centrado.
  const espacioArriba = hole ? hole.y : 0;
  const espacioAbajo = hole ? vh - (hole.y + hole.h) : 0;
  const ponerAbajo = hole ? espacioAbajo >= espacioArriba : true;
  const maxAlto = hole
    ? Math.max(140, (ponerAbajo ? espacioAbajo : espacioArriba) - 26)
    : undefined;

  return (
    <div className="spot" role="dialog" aria-modal="true">
      {/* Capa oscura con recorte (o plena, en el paso final) */}
      <svg className="spot-mask" width="100%" height="100%" aria-hidden>
        <defs>
          <mask id="spot-hole">
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            {hole && (
              <rect
                x={hole.x}
                y={hole.y}
                width={hole.w}
                height={hole.h}
                rx="16"
                fill="black"
              />
            )}
          </mask>
        </defs>
        <rect
          x="0"
          y="0"
          width="100%"
          height="100%"
          fill="rgba(36, 30, 22, 0.62)"
          mask="url(#spot-hole)"
        />
      </svg>

      {/* Anillo de resaltado sobre el elemento */}
      {hole && (
        <div
          className="spot-ring"
          style={{ top: hole.y, left: hole.x, width: hole.w, height: hole.h }}
        />
      )}

      {/* Globo explicativo */}
      <div
        className={`spot-tip ${hole ? (ponerAbajo ? "below" : "above") : "center"}`}
        style={
          hole
            ? ponerAbajo
              ? { top: hole.y + hole.h + 14, maxHeight: maxAlto }
              : { bottom: vh - hole.y + 14, maxHeight: maxAlto }
            : undefined
        }
      >
        <div className="spot-dots">
          {Array.from({ length: total }).map((_, i) => (
            <span key={i} className={`coach-dot ${i === paso ? "on" : ""}`} />
          ))}
        </div>
        <h3 className="coach-title">{titulo}</h3>
        <p className="coach-body">{cuerpo}</p>
        <div className="spot-actions">
          <Button variant="primary" full onClick={onNext}>
            {ctaSiguiente}
          </Button>
          <div className="spot-subnav">
            {paso > 0 && !esFinal && (
              <button className="spot-link" onClick={onPrev}>
                Atrás
              </button>
            )}
            {!esFinal && (
              <button className="spot-link" onClick={onSkip}>
                Saltar
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

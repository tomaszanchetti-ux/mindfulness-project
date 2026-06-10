// Spotlight: desatura la pantalla (gris) y deja a color SOLO el elemento objetivo,
// con el globo explicativo al lado. Si no hay objetivo, centra el globo (paso final).
// Patrón de "product tour": el resto de la pantalla queda inerte (el overlay captura
// los clics); solo se avanza con los botones del globo.
//
// El gris se logra con 4 paneles `backdrop-filter: grayscale()` alrededor del hueco
// (no con mask/clip-path: combinarlos con backdrop-filter tiene bugs en Safari iOS).
// Los paneles comparten aristas exactas — sin gaps ni solapes que dupliquen el tinte.

import { useEffect, useLayoutEffect, useState } from "react";
import type { CSSProperties } from "react";
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
    let cancelado = false;

    const medir = () => {
      if (cancelado) return;
      const el = document.querySelector(selector);
      if (!el) return;
      const r = el.getBoundingClientRect();
      // Solo actualiza si de verdad se movió (evita renders inútiles).
      setRect((prev) =>
        prev &&
        Math.abs(prev.top - r.top) < 0.5 &&
        Math.abs(prev.left - r.left) < 0.5 &&
        Math.abs(prev.width - r.width) < 0.5 &&
        Math.abs(prev.height - r.height) < 0.5
          ? prev
          : { top: r.top, left: r.left, width: r.width, height: r.height },
      );
    };

    // 1) Medición sincrónica (el caso común: el elemento ya está en la pantalla).
    medir();
    // 2) Re-mide cada 200ms mientras el recuadro está abierto. Clave: en la primera
    //    carga la fuente Fraunces aún se descarga; al terminar, el texto reacomoda y
    //    el elemento baja → el recuadro lo sigue. (setInterval corre aun con la
    //    pestaña en segundo plano; requestAnimationFrame no.)
    const iv = setInterval(medir, 200);
    // 3) Disparo explícito cuando terminan de cargar las fuentes.
    if (document.fonts?.ready) document.fonts.ready.then(medir);
    // 4) Y ante scroll/resize, para seguirlo en vivo.
    window.addEventListener("resize", medir);
    window.addEventListener("scroll", medir, true);

    return () => {
      cancelado = true;
      clearInterval(iv);
      window.removeEventListener("resize", medir);
      window.removeEventListener("scroll", medir, true);
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
  const [vw, setVw] = useState(() => window.innerWidth);

  useEffect(() => {
    const onR = () => {
      setVh(window.innerHeight);
      setVw(window.innerWidth);
    };
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

  // Caret del globo: apunta al centro del hueco. El globo está centrado en la
  // pantalla (left:50%), así que la posición del caret dentro del globo es el
  // centro del hueco menos el borde izquierdo del globo, acotada a sus bordes.
  const tipW = Math.min(vw * 0.92, 360);
  const caretX = hole
    ? Math.min(Math.max(hole.x + hole.w / 2 - (vw - tipW) / 2, 18), tipW - 18)
    : undefined;

  return (
    <div className="spot" role="dialog" aria-modal="true">
      {/* Velo gris alrededor del hueco (o pleno, en el paso final) */}
      {hole ? (
        <>
          <div className="spot-veil" style={{ top: 0, left: 0, right: 0, height: hole.y }} />
          <div className="spot-veil" style={{ top: hole.y, left: 0, width: hole.x, height: hole.h }} />
          <div
            className="spot-veil"
            style={{ top: hole.y, left: hole.x + hole.w, right: 0, height: hole.h }}
          />
          <div className="spot-veil" style={{ top: hole.y + hole.h, left: 0, right: 0, bottom: 0 }} />
        </>
      ) : (
        <div className="spot-veil" style={{ inset: 0 }} />
      )}

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
            ? {
                ...(ponerAbajo
                  ? { top: hole.y + hole.h + 14, maxHeight: maxAlto }
                  : { bottom: vh - hole.y + 14, maxHeight: maxAlto }),
                ...(caretX !== undefined
                  ? ({ "--caret-x": `${caretX}px` } as CSSProperties)
                  : {}),
              }
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

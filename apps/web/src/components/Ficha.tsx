// WS29 · C0 · La FICHA de una Pausa — el componente compartido.
//
// Nació dentro de `screens/EntryDetail.tsx` (WS25) como una página del pager del
// Baúl. Desde el Bloque C la misma ficha se lee en dos lugares, y por eso vive
// acá:
//
//  · modo "propia" → la Pausa del dueño. Lleva el switch "Compartir con tu
//    Comunidad" (la única puerta al Bloque C), Enviar, Eliminar y las estrellas.
//  · modo "ajena"  → la Pausa de otra persona. NO lleva el switch, ni Enviar, ni
//    Eliminar, ni las estrellas: la puntuación nunca sale de la cuenta del dueño.
//    Los botones que correspondan los pone la pantalla que la usa (C2).
//
// Todo lo demás es idéntico en los dos modos: título = el pilar, la acción
// inicial, el héroe (carta en miniatura con lightbox + fotos con zoom, o el
// texto de la Pausa si no hay fotos) y la reflexión en su caja con degradado.

import { useLayoutEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Card } from "./Card";
import { Button } from "./Button";
import { Stars } from "./Stars";
import { FotoPrivada } from "./FotoPrivada";
import { assetUrl } from "../lib/api";
import { fechaCorta } from "../lib/format";
import type { ItemBaul, Visibilidad } from "../lib/types";

export type FichaProps = {
  item: ItemBaul;
  modo: "propia" | "ajena";
  /** Modo ajena: el apodo del dueño. Sin apodo, "alguien". */
  de?: string | null;
  hayMas?: boolean;
  // —— modo propia ——
  onShare?: () => void;
  onDelete?: () => void;
  onVisibilidad?: (v: Visibilidad) => Promise<void>;
  // —— modo ajena: las acciones las define la pantalla que la usa ——
  acciones?: ReactNode;
};

export function Ficha({
  item,
  modo,
  de,
  hayMas = false,
  onShare,
  onDelete,
  onVisibilidad,
  acciones,
}: FichaProps) {
  const [verCarta, setVerCarta] = useState(false); // la carta en grande
  const [flipped, setFlipped] = useState(true); // en grande arranca por el dorso (la frase)
  const [zoom, setZoom] = useState<string | null>(null); // foto a pantalla completa
  const [cambiando, setCambiando] = useState(false);
  const [desborda, setDesborda] = useState(false); // la reflexión no entra en la caja
  const reflRef = useRef<HTMLDivElement>(null);

  const propia = modo === "propia";
  const compartida = item.visibilidad === "compartida";
  const cat = item.carta.categoria;
  const fotos = item.fotos.slice(0, 3);

  useLayoutEffect(() => {
    const el = reflRef.current;
    if (el) setDesborda(el.scrollHeight > el.clientHeight + 2);
  }, [item.reflexion]);

  const alternar = async (quiere: boolean) => {
    if (cambiando || !onVisibilidad) return;
    setCambiando(true);
    try {
      await onVisibilidad(quiere ? "compartida" : "privada");
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setCambiando(false);
    }
  };

  return (
    <div className="baul-page-inner ficha">
      {/* Modo ajena: de quién es esta Pausa, arriba del pilar y en voz baja. */}
      {!propia && <p className="ficha-de">Pausa de {de || "alguien"}</p>}

      <div className="ficha-head">
        <h2 className="ficha-titulo" style={{ color: cat.color_text }}>
          <span className="ficha-titulo-punto" style={{ background: cat.color_accent }} />
          {cat.nombre}
        </h2>
        <span className="ficha-fecha">{fechaCorta(item.fecha)}</span>
      </div>
      {/* La acción inicial, sutil, alineada con el título. */}
      <p className="ficha-accion">
        <img src={assetUrl(item.carta.accion.glifo)} alt="" />
        <span>{item.carta.accion.nombre}</span>
      </p>

      <div className="ficha-hero">
        <button
          type="button"
          className="ficha-mini"
          aria-label="Ver la carta en grande"
          onClick={() => setVerCarta(true)}
        >
          <span className="ficha-mini-band" style={{ background: cat.color_accent }} />
          <span className="ficha-mini-frase">{item.carta.frase}</span>
          {/* El dibujo del pilar: la identidad de la carta, a la vista. */}
          <img className="ficha-mini-dibujo" src={assetUrl(cat.img)} alt="" />
          <span className="ficha-mini-ver">ver carta ↗</span>
        </button>

        {fotos.length > 0 ? (
          <div className={`ficha-fotos n${fotos.length}`}>
            {fotos.map((src) => (
              <button
                key={src}
                type="button"
                className="ficha-foto"
                aria-label="Ver la foto en grande"
                onClick={() => setZoom(src)}
              >
                <FotoPrivada src={src} />
              </button>
            ))}
          </div>
        ) : (
          <div className="ficha-pausa">
            <span className="ficha-lbl">La Pausa</span>
            <p>{item.carta.prompt}</p>
          </div>
        )}
      </div>

      <div className={`ficha-refl ${item.reflexion ? "" : "is-empty"}`}>
        <span className="ficha-lbl">{propia ? "Tu reflexión" : "Su reflexión"}</span>
        <div className="ficha-refl-txt" ref={reflRef}>
          {item.reflexion ||
            (propia
              ? "Esta Pausa la guardaste sin reflexión."
              : "Esta Pausa se guardó sin reflexión.")}
        </div>
        {desborda && <span className="ficha-refl-fade" aria-hidden />}
        {desborda && <span className="ficha-refl-more" aria-hidden>⌄</span>}
      </div>

      {/* —— Modo propia: la puerta a la comunidad y las acciones del dueño —— */}
      {propia && (
        <>
          {/* Sin subtexto: el rótulo alcanza. */}
          <label className="toggle-row visibilidad-row">
            <span className="visibilidad-label">Compartir con tu Comunidad</span>
            <span className="switch">
              <input
                type="checkbox"
                checked={compartida}
                disabled={cambiando}
                onChange={(e) => alternar(e.target.checked)}
              />
              <span className="slider" />
            </span>
          </label>

          <div className="baul-page-actions">
            <Button variant="secondary" full onClick={onShare}>
              Enviar
            </Button>
            <button className="link" onClick={onDelete}>
              Eliminar esta Pausa
            </button>
            {/* Las estrellas: siempre tuyas, al pie y discretas. */}
            {item.estrellas != null && (
              <span className="ficha-estrellas stars-sm">
                <Stars value={item.estrellas} readOnly />
              </span>
            )}
          </div>
        </>
      )}

      {/* —— Modo ajena: lo que ponga la pantalla que la usa (C2) —— */}
      {!propia && acciones && <div className="baul-page-actions">{acciones}</div>}

      {hayMas && <div className="baul-more" aria-hidden>⌄</div>}

      {/* La carta en grande: frente y dorso como siempre; toca afuera para volver. */}
      {verCarta && (
        <div className="lightbox" onClick={() => setVerCarta(false)}>
          <div className="lightbox-carta" onClick={(e) => e.stopPropagation()}>
            <Card carta={item.carta} flipped={flipped} onFlip={() => setFlipped((f) => !f)} />
          </div>
          <button className="lightbox-close" aria-label="Cerrar">×</button>
        </div>
      )}

      {/* La foto en grande: toca cualquier lado para volver. */}
      {zoom && (
        <div className="lightbox" onClick={() => setZoom(null)}>
          <FotoPrivada className="lightbox-img" src={zoom} />
          <button className="lightbox-close" aria-label="Cerrar">×</button>
        </div>
      )}
    </div>
  );
}

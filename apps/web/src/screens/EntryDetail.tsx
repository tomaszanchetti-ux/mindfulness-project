// Detalle del Baúl como PAGER a pantalla completa (§12.4 / §20).
// Cada experiencia entra entera en una pantalla (carta + reflexión + CTAs, sin
// scroll); el scroll-snap te lleva a la siguiente pausa guardada, como pasar cartas.
// No hay endpoint de una sola entrada: leemos el Baúl y arrancamos en la elegida.

import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Stars } from "../components/Stars";
import { api } from "../lib/api";
import { FotoPrivada } from "../components/FotoPrivada";
import { fechaLarga } from "../lib/format";
import type { ItemBaul } from "../lib/types";

export function EntryDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [items, setItems] = useState<ItemBaul[] | null>(null);
  const [aBorrar, setABorrar] = useState<ItemBaul | null>(null);
  const [borrando, setBorrando] = useState(false);
  const pagerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    api.baul("reciente").then(setItems).catch(() => setItems([]));
  }, []);

  // Arrancar en la entrada elegida (sin animación, ya posicionado).
  useEffect(() => {
    if (items && pagerRef.current) {
      const el = pageRefs.current[id];
      if (el) pagerRef.current.scrollTop = el.offsetTop;
    }
  }, [items, id]);

  const eliminar = async () => {
    if (!aBorrar) return;
    setBorrando(true);
    try {
      await api.borrarEntrada(aBorrar.id);
      const restantes = (items || []).filter((x) => x.id !== aBorrar.id);
      setABorrar(null);
      setBorrando(false);
      if (restantes.length === 0) navigate("/baul", { replace: true });
      else setItems(restantes);
    } catch (e) {
      setBorrando(false);
      alert((e as Error).message);
    }
  };

  if (items === null) return <div className="center-note">…</div>;
  if (items.length === 0)
    return (
      <div>
        <button className="back-link" onClick={() => navigate("/baul")}>← Baúl</button>
        <div className="center-note">No encontramos esta pausa.</div>
      </div>
    );

  return (
    <div className="baul-detail">
      <button className="back-link" onClick={() => navigate("/baul")}>← Baúl</button>

      <div className="baul-pager" ref={pagerRef}>
        {items.map((it, i) => (
          <div
            key={it.id}
            className="baul-page"
            ref={(el) => (pageRefs.current[it.id] = el)}
          >
            <BaulPage
              item={it}
              hayMas={i < items.length - 1}
              onShare={() => navigate(`/compartir/${it.id}`)}
              onDelete={() => setABorrar(it)}
            />
          </div>
        ))}
      </div>

      {aBorrar && (
        <div className="modal-backdrop" onClick={() => setABorrar(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>¿Eliminar esta pausa?</h3>
            <p>
              Se borra para siempre, junto con su reflexión y fotos. Esto no se puede
              deshacer.
            </p>
            <div className="modal-actions">
              <Button variant="primary" className="btn-danger" full disabled={borrando} onClick={eliminar}>
                {borrando ? "Eliminando…" : "Sí, eliminar"}
              </Button>
              <Button variant="tertiary" onClick={() => setABorrar(null)}>
                Conservar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// —— Una página del pager: una experiencia completa, centrada. ——
function BaulPage({
  item,
  hayMas,
  onShare,
  onDelete,
}: {
  item: ItemBaul;
  hayMas: boolean;
  onShare: () => void;
  onDelete: () => void;
}) {
  const [flipped, setFlipped] = useState(true); // mostramos el dorso (la frase)
  const [zoom, setZoom] = useState<string | null>(null); // foto a pantalla completa

  return (
    <div className="baul-page-inner">
      <div className="detail-meta">
        <span>{fechaLarga(item.fecha)}</span>
        {item.estrellas != null && (
          <span className="stars-sm"><Stars value={item.estrellas} readOnly /></span>
        )}
      </div>

      <Card carta={item.carta} flipped={flipped} onFlip={() => setFlipped((f) => !f)} />

      {item.reflexion && (
        <div className="detail-block">
          <h4>Tu reflexión</h4>
          <p>{item.reflexion}</p>
        </div>
      )}

      {item.fotos.length > 0 && (
        <div className="detail-photos">
          {item.fotos.map((src) => (
            <button
              key={src}
              type="button"
              className="detail-photo-btn"
              aria-label="Ver la foto en grande"
              onClick={() => setZoom(src)}
            >
              <FotoPrivada src={src} />
            </button>
          ))}
        </div>
      )}

      {/* La foto en grande: toca cualquier lado para volver. */}
      {zoom && (
        <div className="lightbox" onClick={() => setZoom(null)}>
          <FotoPrivada className="lightbox-img" src={zoom} />
          <button className="lightbox-close" aria-label="Cerrar">×</button>
        </div>
      )}

      <div className="baul-page-actions">
        <Button variant="secondary" full onClick={onShare}>
          Enviar a alguien
        </Button>
        <button className="link" onClick={onDelete}>
          Eliminar esta pausa
        </button>
      </div>

      {hayMas && <div className="baul-more" aria-hidden>⌄</div>}
    </div>
  );
}

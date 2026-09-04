// Detalle del Baúl como PAGER a pantalla completa (§12.4 / §20).
// Cada experiencia entra entera en una pantalla (carta + reflexión + CTAs, sin
// scroll); el scroll-snap te lleva a la siguiente Pausa guardada, como pasar cartas.
// No hay endpoint de una sola entrada: leemos el Baúl y arrancamos en la elegida.
//
// WS25 · cada página lleva el switch "Compartida con tu comunidad"
// (PUT /api/baul/{id}/visibilidad). Es la única puerta entre el Baúl privado y
// la comunidad: las estrellas nunca salen de acá.

import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Stars } from "../components/Stars";
import { api } from "../lib/api";
import { FotoPrivada } from "../components/FotoPrivada";
import { fechaLarga } from "../lib/format";
import type { ItemBaul, Visibilidad } from "../lib/types";

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

  // El switch se resuelve en el padre para que el cambio quede en la lista: si
  // el usuario pasa a otra página y vuelve, sigue viendo el estado real.
  const cambiarVisibilidad = async (item: ItemBaul, v: Visibilidad) => {
    const actualizado = await api.setVisibilidad(item.id, v);
    setItems((cur) =>
      (cur || []).map((x) => (x.id === item.id ? { ...x, visibilidad: actualizado.visibilidad } : x)),
    );
  };

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
        <div className="center-note">No encontramos esta Pausa.</div>
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
              onVisibilidad={(v) => cambiarVisibilidad(it, v)}
            />
          </div>
        ))}
      </div>

      {aBorrar && (
        <div className="modal-backdrop" onClick={() => setABorrar(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>¿Eliminar esta Pausa?</h3>
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
  onVisibilidad,
}: {
  item: ItemBaul;
  hayMas: boolean;
  onShare: () => void;
  onDelete: () => void;
  onVisibilidad: (v: Visibilidad) => Promise<void>;
}) {
  const [flipped, setFlipped] = useState(true); // mostramos el dorso (la frase)
  const [zoom, setZoom] = useState<string | null>(null); // foto a pantalla completa
  const [cambiando, setCambiando] = useState(false);

  const compartida = item.visibilidad === "compartida";

  const alternar = async (quiere: boolean) => {
    if (cambiando) return;
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

      {/* La puerta a la comunidad. Se ve siempre, en el mismo lugar de cada página. */}
      <div className="visibilidad-box">
        <label className="toggle-row visibilidad-row">
          <span className="visibilidad-label">Compartida con tu comunidad</span>
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
        <p className="visibilidad-nota">
          Solo tu comunidad la ve. Las estrellas siempre son tuyas.
        </p>
      </div>

      <div className="baul-page-actions">
        <Button variant="secondary" full onClick={onShare}>
          Enviar
        </Button>
        <button className="link" onClick={onDelete}>
          Eliminar esta Pausa
        </button>
      </div>

      {hayMas && <div className="baul-more" aria-hidden>⌄</div>}
    </div>
  );
}

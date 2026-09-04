// Detalle del Baúl como PAGER a pantalla completa (§12.4 / §20).
// Cada experiencia entra entera en una pantalla (carta + reflexión + CTAs, sin
// scroll); el scroll-snap te lleva a la siguiente Pausa guardada, como pasar cartas.
// No hay endpoint de una sola entrada: leemos el Baúl y arrancamos en la elegida.
//
// WS25 · cada página lleva el switch "Compartida con tu comunidad"
// (PUT /api/baul/{id}/visibilidad). Es la única puerta entre el Baúl privado y
// la comunidad: las estrellas nunca salen de acá.

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Stars } from "../components/Stars";
import { api, assetUrl } from "../lib/api";
import { FotoPrivada } from "../components/FotoPrivada";
import { fechaCorta } from "../lib/format";
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

// —— Una página del pager: la FICHA de una Pausa, entera en una pantalla (WS25). ——
// Título = el pilar. Héroe = la carta en miniatura (tocarla la abre en grande) +
// las fotos (o el texto de la Pausa si no hay fotos). La reflexión va en una caja
// de altura fija que se desliza por dentro. Visibilidad, Enviar y Eliminar quedan
// siempre a la vista. Esta misma ficha es la que verá la comunidad.
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
  const [verCarta, setVerCarta] = useState(false); // la carta en grande
  const [flipped, setFlipped] = useState(true); // en grande arranca por el dorso (la frase)
  const [zoom, setZoom] = useState<string | null>(null); // foto a pantalla completa
  const [cambiando, setCambiando] = useState(false);
  const [desborda, setDesborda] = useState(false); // la reflexión no entra en la caja
  const reflRef = useRef<HTMLDivElement>(null);

  const compartida = item.visibilidad === "compartida";
  const cat = item.carta.categoria;
  const fotos = item.fotos.slice(0, 3);

  useLayoutEffect(() => {
    const el = reflRef.current;
    if (el) setDesborda(el.scrollHeight > el.clientHeight + 2);
  }, [item.reflexion]);

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
    <div className="baul-page-inner ficha">
      <div className="ficha-head">
        <h2 className="ficha-titulo" style={{ color: cat.color_text }}>
          <span className="ficha-titulo-punto" style={{ background: cat.color_accent }} />
          {cat.nombre}
        </h2>
        <div className="ficha-meta">
          <span>{fechaCorta(item.fecha)}</span>
          {item.estrellas != null && (
            <span className="stars-sm"><Stars value={item.estrellas} readOnly /></span>
          )}
        </div>
      </div>

      <div className="ficha-hero">
        <button
          type="button"
          className="ficha-mini"
          aria-label="Ver la carta en grande"
          onClick={() => setVerCarta(true)}
        >
          <span className="ficha-mini-band" style={{ background: cat.color_accent }} />
          <span className="ficha-mini-frase">{item.carta.frase}</span>
          <img className="ficha-mini-glifo" src={assetUrl(item.carta.accion.glifo)} alt="" />
          <span className="ficha-mini-accion">{item.carta.accion.nombre}</span>
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
        <span className="ficha-lbl">Tu reflexión</span>
        <div className="ficha-refl-txt" ref={reflRef}>
          {item.reflexion || "Esta Pausa la guardaste sin reflexión."}
        </div>
        {desborda && <span className="ficha-refl-fade" aria-hidden />}
        {desborda && <span className="ficha-refl-more" aria-hidden>⌄</span>}
      </div>

      {/* La puerta a la comunidad. Sin subtexto: el rótulo alcanza. */}
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
      </div>

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

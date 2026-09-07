// Detalle del Baúl como PAGER a pantalla completa (§12.4 / §20).
// Cada experiencia entra entera en una pantalla (carta + reflexión + CTAs, sin
// scroll); el scroll-snap te lleva a la siguiente Pausa guardada, como pasar cartas.
// No hay endpoint de una sola entrada: leemos el Baúl y arrancamos en la elegida.
//
// WS25 · cada página lleva el switch "Compartida con tu comunidad"
// (PUT /api/baul/{id}/visibilidad). Es la única puerta entre el Baúl privado y
// la comunidad: las estrellas nunca salen de acá.
//
// WS29 · C0 · la ficha en sí se mudó a `components/Ficha.tsx`: la misma que verá
// la comunidad, con dos modos. Acá se usa en modo "propia".

import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { Ficha } from "../components/Ficha";
import { api } from "../lib/api";
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
            <Ficha
              item={it}
              modo="propia"
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

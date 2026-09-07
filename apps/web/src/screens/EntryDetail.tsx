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
// la comunidad, con dos modos.
//
// WS30 · C2.2 · el Baúl trae tres clases de ficha, así que este detalle también:
//   · mi Pausa            → <Ficha modo="propia">, con Reenviar debajo.
//   · una Pausa guardada  → <Ficha modo="ajena">, con Quitar de mi Baúl,
//                           Hacer la Pausa (ahora o como la próxima) y Reenviar.
//   · una recomendación   → su propio detalle, sin pager: no es una carta.
// El pager solo pasa Pausas; una recomendación se abre sola (mezclarlas en el
// mismo deslizamiento haría pasar de una carta a un texto sin aviso).

import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { Ficha } from "../components/Ficha";
import { ReenviarSheet } from "../components/ReenviarSheet";
import { SoloComunidad } from "../components/SoloComunidad";
import { api } from "../lib/api";
import { fechaCorta } from "../lib/format";
import { useStore } from "../store";
import { esRecomendacion, nombreTipo } from "./Baul";
import type {
  Compartido,
  ItemBaul,
  ItemFicha,
  ItemRecomendacion,
  ModoPausa,
  Visibilidad,
} from "../lib/types";
import "./baul.css";

/** Lo que necesita el panel de Reenviar mientras se resuelve el link de WhatsApp. */
type Reenvio = { entregaId: string; link: string | null };

export function EntryDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { perfil } = useStore();
  const [items, setItems] = useState<ItemFicha[] | null>(null);
  const [aBorrar, setABorrar] = useState<ItemBaul | null>(null);
  const [borrando, setBorrando] = useState(false);
  // WS30 · C2.2 · lo que suma el Bloque C: reenviar, quitar una guardada y
  // hacer la Pausa de otra persona.
  const [reenvio, setReenvio] = useState<Reenvio | null>(null);
  const [abiertoHacer, setAbiertoHacer] = useState<string | null>(null);
  const [haciendo, setHaciendo] = useState(false);
  // El aviso se guarda con el id de la ficha que lo produjo: el pager muestra
  // varias Pausas a la vez y un mensaje suelto aparecería en todas.
  const [avisoPausa, setAvisoPausa] = useState<{ id: string; texto: string } | null>(null);
  const [invitar, setInvitar] = useState(false);
  const pagerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    api.baulCompleto("reciente").then(setItems).catch(() => setItems([]));
  }, []);

  const pausas = (items || []).filter((it): it is ItemBaul => !esRecomendacion(it));
  const recomendacion = (items || []).find(
    (it): it is ItemRecomendacion => esRecomendacion(it) && it.id === id,
  );

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
      (cur || []).map((x) =>
        x.id === item.id ? { ...x, visibilidad: actualizado.visibilidad } : x,
      ),
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

  // —— Reenviar ——————————————————————————————————————————————————————————
  // La ficha AJENA viaja por WhatsApp con el link in-app (`/comunidad/ficha/:id`):
  // con login y la regla de lectura, y sigue siendo del dueño. El `/c/{token}`
  // es solo para las propias.
  const reenviarAjena = (item: ItemBaul) =>
    setReenvio({
      entregaId: item.id,
      link: `${window.location.origin}/comunidad/ficha/${item.id}`,
    });

  // La ficha PROPIA viaja con el link de regalo de siempre. Se reusa el que ya
  // generó "Enviar" en esta sesión (misma llave que `Share.tsx`) y solo se crea
  // uno nuevo si no había: cada llamada a `api.compartir` nace un token.
  const reenviarPropia = async (item: ItemBaul) => {
    setReenvio({ entregaId: item.id, link: null });
    const llave = `share:${item.id}`;
    try {
      const guardado = sessionStorage.getItem(llave);
      if (guardado) {
        const c = JSON.parse(guardado) as Compartido;
        if (c?.url) {
          setReenvio({ entregaId: item.id, link: `${window.location.origin}${c.url}` });
          return;
        }
      }
    } catch {
      /* sessionStorage no disponible: se genera uno nuevo */
    }
    try {
      const c = await api.compartir(item.id);
      try {
        sessionStorage.setItem(llave, JSON.stringify(c));
      } catch {
        /* ignorar */
      }
      setReenvio((cur) =>
        cur && cur.entregaId === item.id
          ? { ...cur, link: `${window.location.origin}${c.url}` }
          : cur,
      );
    } catch {
      // Sin link de WhatsApp el panel sigue sirviendo: se reenvía dentro de Dwellia.
    }
  };

  // —— Una Pausa guardada: quitarla o vivirla ——————————————————————————
  const quitarGuardada = async (item: ItemBaul) => {
    try {
      await api.quitarGuardada(item.id);
      navigate("/baul", { replace: true });
    } catch (e) {
      setAvisoPausa({ id: item.id, texto: (e as Error).message });
    }
  };

  const pedirHacer = (item: ItemBaul) => {
    setAvisoPausa(null);
    if (perfil?.limites.pausas_extra) setAbiertoHacer(item.id);
    else setInvitar(true);
  };

  const hacerPausa = async (item: ItemBaul, modo: ModoPausa) => {
    setHaciendo(true);
    setAvisoPausa(null);
    try {
      const r = await api.hacerPausa(item.id, modo);
      if (modo === "ahora" && r.entrega) {
        navigate(`/pausa/${r.entrega.id}`);
        return;
      }
      setAbiertoHacer(null);
      setAvisoPausa({ id: item.id, texto: "Te va a llegar como tu próxima Pausa." });
    } catch (e) {
      const err = e as Error & { status?: number };
      setAbiertoHacer(null);
      if (err.status === 403) setInvitar(true);
      else setAvisoPausa({ id: item.id, texto: err.message });
    } finally {
      setHaciendo(false);
    }
  };

  if (items === null) return <div className="center-note">…</div>;

  // —— Una recomendación: su propio detalle, sin pager —————————————————
  if (recomendacion) {
    return (
      <DetalleRecomendacion
        item={recomendacion}
        onVisibilidad={(v) =>
          api.setVisibilidadRecomendacion(recomendacion.id, v).then((r) => {
            setItems((cur) =>
              (cur || []).map((x) =>
                x.id === r.id ? { ...(x as ItemRecomendacion), visibilidad: r.visibilidad } : x,
              ),
            );
          })
        }
        onBorrada={() => navigate("/baul", { replace: true })}
      />
    );
  }

  if (pausas.length === 0)
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
        {pausas.map((it, i) => {
          const guardada = it.guardada === true;
          const hayMas = i < pausas.length - 1;

          // —— La Pausa de otra persona que guardé en mi Baúl ——
          if (guardada) {
            return (
              <div
                key={it.id}
                className="baul-page"
                ref={(el) => (pageRefs.current[it.id] = el)}
              >
                <Ficha
                  item={it}
                  modo="ajena"
                  de={it.de?.apodo}
                  hayMas={hayMas}
                  acciones={
                    abiertoHacer === it.id ? (
                      <div className="confirm-inline pausa-opciones">
                        <p className="confirm-inline-pregunta">¿Cuándo la haces?</p>
                        <p className="confirm-inline-nota">
                          Puedes vivirla ahora mismo, sin tocar tu Pausa de hoy, o
                          dejar que llegue como la próxima.
                        </p>
                        <div className="actions-stack">
                          <Button
                            variant="primary"
                            full
                            disabled={haciendo}
                            onClick={() => hacerPausa(it, "ahora")}
                          >
                            {haciendo ? "Un momento…" : "Hacerla ahora"}
                          </Button>
                          <Button
                            variant="secondary"
                            full
                            disabled={haciendo}
                            onClick={() => hacerPausa(it, "siguiente")}
                          >
                            Que sea mi próxima Pausa
                          </Button>
                          <Button
                            variant="tertiary"
                            disabled={haciendo}
                            onClick={() => setAbiertoHacer(null)}
                          >
                            Ahora no
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <Button variant="primary" full onClick={() => pedirHacer(it)}>
                          Hacer la Pausa
                        </Button>
                        <Button variant="secondary" full onClick={() => reenviarAjena(it)}>
                          Reenviar
                        </Button>
                        <button className="link" onClick={() => quitarGuardada(it)}>
                          Quitar de mi Baúl
                        </button>
                        {avisoPausa?.id === it.id && (
                          <p className="pausa-aviso">{avisoPausa.texto}</p>
                        )}
                      </>
                    )
                  }
                />
              </div>
            );
          }

          // —— Mi Pausa ——
          return (
            <div
              key={it.id}
              className="baul-page"
              ref={(el) => (pageRefs.current[it.id] = el)}
            >
              {/* "Reenviar" no cabe dentro de <Ficha modo="propia"> (ese modo no
                  acepta acciones): la ficha y el botón viajan juntos en un
                  envoltorio, para que la página los siga centrando como a una
                  sola pieza. El "hay más" queda al final, donde siempre. */}
              <div className="ficha-con-reenviar">
                <Ficha
                  item={it}
                  modo="propia"
                  hayMas={false}
                  onShare={() => navigate(`/compartir/${it.id}`)}
                  onDelete={() => setABorrar(it)}
                  onVisibilidad={(v) => cambiarVisibilidad(it, v)}
                />
                <div className="ficha-reenviar actions-stack">
                  <Button variant="secondary" full onClick={() => reenviarPropia(it)}>
                    Reenviar a alguien de tu comunidad
                  </Button>
                </div>
                {hayMas && <div className="baul-more" aria-hidden>⌄</div>}
              </div>
            </div>
          );
        })}
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

      {/* El panel de reenviar: a alguien de mi comunidad o por WhatsApp. */}
      <ReenviarSheet
        entregaId={reenvio?.entregaId || ""}
        abierto={!!reenvio}
        onClose={() => setReenvio(null)}
        linkWhatsApp={reenvio?.link ?? null}
      />

      {invitar && (
        <SoloComunidad
          onClose={() => setInvitar(false)}
        />
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// El detalle de una recomendación: el tipo, el título, el porqué y el enlace.
// Sin carta, sin fotos, sin estrellas — no es una Pausa vivida, es algo que
// alguien deja. Se puede publicar, retocar y borrar.
// ─────────────────────────────────────────────────────────────────────────────

function DetalleRecomendacion({
  item,
  onVisibilidad,
  onBorrada,
}: {
  item: ItemRecomendacion;
  onVisibilidad: (v: Visibilidad) => Promise<void>;
  onBorrada: () => void;
}) {
  const navigate = useNavigate();
  const [cambiando, setCambiando] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [borrando, setBorrando] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  const alternar = async (quiere: boolean) => {
    if (cambiando) return;
    setCambiando(true);
    setAviso(null);
    try {
      await onVisibilidad(quiere ? "compartida" : "privada");
    } catch (e) {
      setAviso((e as Error).message);
    } finally {
      setCambiando(false);
    }
  };

  const borrar = async () => {
    setBorrando(true);
    setAviso(null);
    try {
      await api.borrarRecomendacion(item.id);
      onBorrada();
    } catch (e) {
      setBorrando(false);
      setConfirmando(false);
      setAviso((e as Error).message);
    }
  };

  return (
    <div className="baul-detail">
      <button className="back-link" onClick={() => navigate("/baul")}>← Baúl</button>

      <div className="reco-detalle">
        <div className="reco-detalle-head">
          <span className="entry-top-left">
            <span className="pill-reco">Recomendación</span>
            <span className="entry-reco-tipo">{nombreTipo(item.tipo_recomendacion)}</span>
          </span>
          <span className="reco-detalle-fecha">{fechaCorta(item.fecha)}</span>
        </div>

        <h1 className="reco-detalle-titulo">{item.titulo}</h1>
        <p className="reco-detalle-texto">{item.texto}</p>

        {item.url && (
          <a
            className="reco-detalle-link"
            href={item.url}
            target="_blank"
            rel="noreferrer noopener"
          >
            Abrir el enlace ↗
          </a>
        )}

        {/* La misma puerta que las Pausas, con las mismas palabras. */}
        <label className="toggle-row visibilidad-row">
          <span className="visibilidad-label">Compartir con tu Comunidad</span>
          <span className="switch">
            <input
              type="checkbox"
              checked={item.visibilidad === "compartida"}
              disabled={cambiando}
              onChange={(e) => alternar(e.target.checked)}
            />
            <span className="slider" />
          </span>
        </label>

        {aviso && <p className="reco-aviso">{aviso}</p>}

        {confirmando ? (
          <div className="confirm-inline">
            <p className="confirm-inline-pregunta">¿Borrar esta recomendación?</p>
            <p className="confirm-inline-nota">
              Se borra para siempre y deja de verla quien la tenía a la vista.
            </p>
            <div className="actions-stack">
              <Button
                variant="primary"
                className="btn-danger"
                full
                disabled={borrando}
                onClick={borrar}
              >
                {borrando ? "Borrando…" : "Sí, borrar"}
              </Button>
              <Button variant="tertiary" onClick={() => setConfirmando(false)}>
                Conservar
              </Button>
            </div>
          </div>
        ) : (
          <div className="reco-detalle-acciones">
            <Button
              variant="secondary"
              full
              onClick={() => navigate(`/baul/recomendacion/${item.id}/editar`)}
            >
              Editar
            </Button>
            <button className="link" onClick={() => setConfirmando(true)}>
              Borrar esta recomendación
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

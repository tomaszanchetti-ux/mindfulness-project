// Baúl (§20). Memoria emocional, no dashboard. Lectura del historial vivido.
// Orden: Reciente (default) / Mejor valoradas — lo resuelve la API.
// Filtros de contenido y de visibilidad se aplican en cliente.
//
// WS25 · la ficha del Baúl es la MISMA que verá la comunidad: por eso lleva la
// píldora "Pausa" en el verde Dwellia y, cuando corresponde, una marca discreta
// de que está compartida. Sin likes ni contadores: acá no hay métricas.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { Stars } from "../components/Stars";
import { api } from "../lib/api";
import { fechaCorta } from "../lib/format";
import type { ItemBaul } from "../lib/types";

type Orden = "reciente" | "valoradas";
type Filtro = "todo" | "reflexion" | "compartidas" | "privadas";

const FILTROS: { id: Filtro; label: string }[] = [
  { id: "todo", label: "Todas" },
  { id: "reflexion", label: "Con reflexión" },
  { id: "compartidas", label: "Compartidas" },
  { id: "privadas", label: "Privadas" },
];

export function Baul() {
  const navigate = useNavigate();
  const [items, setItems] = useState<ItemBaul[] | null>(null);
  const [orden, setOrden] = useState<Orden>("reciente");
  const [filtro, setFiltro] = useState<Filtro>("todo");

  useEffect(() => {
    setItems(null);
    api.baul(orden).then(setItems).catch(() => setItems([]));
  }, [orden]);

  const visibles = (items || []).filter((it) => {
    if (filtro === "reflexion") return !!it.reflexion;
    if (filtro === "compartidas") return it.visibilidad === "compartida";
    if (filtro === "privadas") return it.visibilidad !== "compartida";
    return true;
  });

  const vacioPorFiltro = items !== null && items.length > 0 && visibles.length === 0;

  return (
    <div>
      <div className="screen-head">
        <h1 className="screen-title">Baúl</h1>
        <p className="screen-sub">Tus Pausas guardadas</p>
      </div>

      {/* WS25 · Orden y filtros con rótulo, para que se lea qué es qué:
          el orden es un control de dos posiciones; los filtros, chips chicos
          en una sola fila (se desliza si no entran). */}
      <div className="baul-toolbar">
        <div className="baul-tool">
          <span className="baul-tool-label">Orden</span>
          <div className="segmented" role="radiogroup" aria-label="Orden">
            <button
              type="button"
              role="radio"
              aria-checked={orden === "reciente"}
              className={orden === "reciente" ? "is-on" : ""}
              onClick={() => setOrden("reciente")}
            >
              Recientes
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={orden === "valoradas"}
              className={orden === "valoradas" ? "is-on" : ""}
              onClick={() => setOrden("valoradas")}
            >
              Mejor valoradas
            </button>
          </div>
        </div>
        <div className="baul-tool">
          <span className="baul-tool-label">Mostrar</span>
          <div className="chips-scroll" role="radiogroup" aria-label="Mostrar">
            {FILTROS.map((f) => (
              <button
                key={f.id}
                type="button"
                role="radio"
                aria-checked={filtro === f.id}
                className={`chip chip-sm ${filtro === f.id ? "chip-active" : ""}`}
                onClick={() => setFiltro(f.id)}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {items === null && <div className="center-note">…</div>}

      {vacioPorFiltro && (
        <div className="empty">
          <p className="empty-title">Aquí no hay nada todavía.</p>
          <p className="empty-body">Prueba con otro filtro: tus Pausas siguen ahí.</p>
        </div>
      )}

      {items !== null && items.length === 0 && (
        <div className="empty">
          <p className="empty-title">Todavía no guardaste ninguna Pausa.</p>
          <p className="empty-body">
            Cuando cierres tu primera Pausa, va a aparecer aquí.
          </p>
          <Button variant="primary" onClick={() => navigate("/hoy")}>
            Ir a mi Pausa de hoy
          </Button>
        </div>
      )}

      {visibles.map((it) => (
        <button key={it.id} className="entry" onClick={() => navigate(`/baul/${it.id}`)}>
          <span className="entry-spine" style={{ background: it.carta.categoria.color_accent }} />
          <div className="entry-body">
            <div className="entry-top">
              <span className="entry-top-left">
                <span className="pill-pausa">Pausa</span>
                <span className="entry-cat" style={{ color: it.carta.categoria.color_text }}>
                  {it.carta.categoria.nombre}
                </span>
              </span>
              <span className="entry-top-right">
                {it.visibilidad === "compartida" && (
                  <span className="entry-compartida">compartida</span>
                )}
                <span className="entry-date">{fechaCorta(it.fecha)}</span>
              </span>
            </div>
            <p className="entry-frase">{it.carta.frase}</p>
            {it.reflexion && <p className="entry-refl">{it.reflexion}</p>}
            <div className="entry-marks">
              {it.estrellas != null && (
                <span className="entry-mark stars-sm">
                  <Stars value={it.estrellas} readOnly />
                </span>
              )}
              {it.fotos.length > 0 && (
                <span className="entry-mark">◦ {it.fotos.length} foto{it.fotos.length > 1 ? "s" : ""}</span>
              )}
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

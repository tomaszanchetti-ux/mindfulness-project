// Baúl (§20). Memoria emocional, no dashboard. Lectura del historial vivido.
// Orden: Reciente (default) / Más valoradas (toggle real, va a la API).
// Filtros de contenido (Con reflexión / Con foto) se aplican en cliente.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { Stars } from "../components/Stars";
import { api } from "../lib/api";
import { fechaCorta } from "../lib/format";
import type { ItemBaul } from "../lib/types";

type Orden = "reciente" | "valoradas";
type Filtro = "todo" | "reflexion" | "foto";

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
    if (filtro === "foto") return it.fotos.length > 0;
    return true;
  });

  return (
    <div>
      <div className="screen-head">
        <h1 className="screen-title">Baúl</h1>
        <p className="screen-sub">Tus pausas guardadas</p>
      </div>

      {/* Orden */}
      <div className="baul-filters">
        <button
          className={`chip ${orden === "reciente" ? "chip-active" : ""}`}
          onClick={() => setOrden("reciente")}
        >
          Reciente
        </button>
        <button
          className={`chip ${orden === "valoradas" ? "chip-active" : ""}`}
          onClick={() => setOrden("valoradas")}
        >
          Más valoradas
        </button>
      </div>

      {/* Filtros de contenido */}
      <div className="baul-filters">
        {(["todo", "reflexion", "foto"] as Filtro[]).map((f) => (
          <button
            key={f}
            className={`chip ${filtro === f ? "chip-active" : ""}`}
            onClick={() => setFiltro(f)}
          >
            {f === "todo" ? "Todo" : f === "reflexion" ? "Con reflexión" : "Con foto"}
          </button>
        ))}
      </div>

      {items === null && <div className="center-note">…</div>}

      {items !== null && visibles.length === 0 && (
        <div className="empty">
          <p className="empty-title">Todavía no guardaste ninguna pausa.</p>
          <p className="empty-body">
            Cuando completes tu primera consigna, va a aparecer acá.
          </p>
          <Button variant="primary" onClick={() => navigate("/hoy")}>
            Ir a mi pausa de hoy
          </Button>
        </div>
      )}

      {visibles.map((it) => (
        <button key={it.id} className="entry" onClick={() => navigate(`/baul/${it.id}`)}>
          <span className="entry-spine" style={{ background: it.carta.categoria.color_accent }} />
          <div className="entry-body">
            <div className="entry-top">
              <span className="entry-cat" style={{ color: it.carta.categoria.color_text }}>
                {it.carta.categoria.nombre}
              </span>
              <span className="entry-date">{fechaCorta(it.fecha)}</span>
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

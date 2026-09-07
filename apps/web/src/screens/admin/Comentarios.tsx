// WS28 · B2.2b · Bloque 3 · Los comentarios privados de las cartas.
//
// Lo que la gente escribe debajo de las estrellas, agrupado POR CARTA: un
// comentario suelto no dice nada, cinco sobre la misma carta sí. Por eso el
// orden es "las que peor van primero" — la lista existe para encontrar la carta
// que hay que reescribir, no para leer opiniones.
//
// El agrupado se hace acá, en el front: el endpoint devuelve los comentarios
// planos (los últimos 500) y agruparlos es una decisión de esta pantalla.

import { useEffect, useMemo, useState } from "react";
import { api } from "../../lib/api";
import { fechaCorta } from "../../lib/format";
import type { ComentarioAdmin } from "../../lib/types";
import { useStore } from "../../store";
import { es403, mensaje, promedioTexto } from "./comun";

interface Grupo {
  carta_id: string;
  frase: string;
  categoria: string;
  comentarios: ComentarioAdmin[];
  puntuadas: number;
  promedio: number | null;
  hayBajas: boolean;
}

function agrupar(items: ComentarioAdmin[]): Grupo[] {
  const mapa = new Map<string, Grupo>();
  for (const c of items) {
    let g = mapa.get(c.carta_id);
    if (!g) {
      g = {
        carta_id: c.carta_id,
        frase: c.frase,
        categoria: c.categoria,
        comentarios: [],
        puntuadas: 0,
        promedio: null,
        hayBajas: false,
      };
      mapa.set(c.carta_id, g);
    }
    g.comentarios.push(c);
  }

  const grupos = [...mapa.values()];
  for (const g of grupos) {
    const notas = g.comentarios
      .map((c) => c.estrellas)
      .filter((e): e is number => typeof e === "number");
    g.puntuadas = notas.length;
    g.promedio = notas.length ? notas.reduce((a, b) => a + b, 0) / notas.length : null;
    g.hayBajas = notas.some((n) => n <= 2);
  }

  // Las que peor van, primero. Las que nadie puntuó no compiten: van al final.
  grupos.sort((a, b) => {
    if (a.promedio === null && b.promedio === null) return 0;
    if (a.promedio === null) return 1;
    if (b.promedio === null) return -1;
    return a.promedio - b.promedio;
  });
  return grupos;
}

export function Comentarios({ onCerrado }: { onCerrado: () => void }) {
  const { categorias } = useStore();
  const [items, setItems] = useState<ComentarioAdmin[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [soloBajas, setSoloBajas] = useState(false);
  const [abierto, setAbierto] = useState<string | null>(null);

  useEffect(() => {
    let vivo = true;
    api
      .adminComentarios(500)
      .then((res) => {
        if (vivo) setItems(res);
      })
      .catch((e: unknown) => {
        if (!vivo) return;
        if (es403(e)) {
          onCerrado();
          return;
        }
        setItems([]);
        setError(mensaje(e));
      });
    return () => {
      vivo = false;
    };
  }, [onCerrado]);

  const grupos = useMemo(() => agrupar(items || []), [items]);
  const visibles = soloBajas
    ? grupos.filter((g) => (g.promedio !== null && g.promedio <= 2.5) || g.hayBajas)
    : grupos;

  if (error) return <p className="adm-error">{error}</p>;
  if (items === null) return <div className="center-note">…</div>;

  return (
    <section>
      <div className="adm-toolbar">
        <span className="adm-tool-label">Mostrar</span>
        <button
          type="button"
          aria-pressed={soloBajas}
          className={`chip chip-sm ${soloBajas ? "chip-active" : ""}`}
          onClick={() => setSoloBajas((v) => !v)}
        >
          Solo 1-2 estrellas
        </button>
        <span className="adm-conteo">
          {visibles.length === 1 ? "1 carta" : `${visibles.length} cartas`}
        </span>
      </div>

      {grupos.length === 0 && (
        <div className="empty">
          <p className="empty-title">Todavía nadie comentó una carta.</p>
          <p className="empty-body">
            Los comentarios llegan al cerrar una Pausa, debajo de las estrellas.
          </p>
        </div>
      )}

      {grupos.length > 0 && visibles.length === 0 && (
        <div className="empty">
          <p className="empty-title">Ninguna carta va tan mal.</p>
          <p className="empty-body">Quita el filtro para verlas todas.</p>
        </div>
      )}

      {visibles.map((g) => {
        const cat = categorias.find((c) => c.slug === g.categoria);
        const accent = cat?.color_accent || "var(--sand-line)";
        const text = cat?.color_text || "var(--warm-taupe)";
        const abierta = abierto === g.carta_id;
        const baja = g.promedio !== null && g.promedio <= 2.5;
        return (
          <article className="adm-grupo" key={g.carta_id}>
            <button
              type="button"
              className="adm-grupo-head"
              aria-expanded={abierta}
              onClick={() => setAbierto((cur) => (cur === g.carta_id ? null : g.carta_id))}
            >
              <span className="adm-grupo-spine" style={{ background: accent }} />
              <span className="adm-grupo-txt">
                <span className="adm-grupo-frase">{g.frase}</span>
                <span className="adm-grupo-meta">
                  <span style={{ color: text }}>{cat?.nombre || g.categoria}</span> ·{" "}
                  {g.puntuadas === 0
                    ? "sin puntuar"
                    : g.puntuadas === 1
                      ? "puntuada 1 vez"
                      : `puntuada ${g.puntuadas} veces`}{" "}
                  ·{" "}
                  {g.comentarios.length === 1
                    ? "1 comentario"
                    : `${g.comentarios.length} comentarios`}
                </span>
              </span>
              <span className={`adm-grupo-prom ${baja ? "is-baja" : ""}`}>
                <span className="adm-grupo-prom-v">{promedioTexto(g.promedio)}</span>
                <span className="adm-grupo-prom-k">de 5</span>
              </span>
            </button>

            {abierta && (
              <div className="adm-coms">
                {g.comentarios.map((c) => (
                  <div className="adm-com" key={c.entrega_id}>
                    <p className="adm-com-top">
                      {c.estrellas === null ? (
                        <span className="adm-estrellas is-vacio">sin estrellas</span>
                      ) : (
                        <span
                          className="adm-estrellas"
                          aria-label={`${c.estrellas} de 5`}
                        >
                          {/* Una nota fuera de rango no puede tumbar la lista:
                              `repeat` con un negativo lanza. */}
                          {"★".repeat(Math.min(5, Math.max(1, Math.round(c.estrellas))))}
                        </span>
                      )}
                      <span className="adm-com-apodo">{c.apodo || "sin apodo"}</span>
                      <span className="adm-com-fecha">{fechaCorta(c.fecha)}</span>
                    </p>
                    <p className="adm-com-txt">{c.comentario}</p>
                  </div>
                ))}
              </div>
            )}
          </article>
        );
      })}

      <p className="adm-pie">
        Esta lista es solo para leer. Las cartas se corrigen en el repositorio y
        llegan con el siguiente despliegue de contenido.
      </p>
    </section>
  );
}

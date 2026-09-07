// Baúl (§20). Memoria emocional, no dashboard. Lectura del historial vivido.
// Orden: Reciente (default) / Mejor valoradas — lo resuelve la API.
// Filtros de contenido y de visibilidad se aplican en cliente.
//
// WS25 · la ficha del Baúl es la MISMA que verá la comunidad: por eso lleva la
// píldora "Pausa" en el verde Dwellia y, cuando corresponde, una marca discreta
// de que está compartida. Sin likes ni contadores: acá no hay métricas.
//
// WS30 · C2.2 · el Baúl deja de ser solo mis Pausas. `api.baulCompleto` trae tres
// clases de ficha mezcladas por fecha, y cada una tiene su píldora:
//   · Pausa            — la que viví (verde salvia, con estrellas y fotos).
//   · Pausa de <apodo> — una ficha de mi comunidad que guardé (sin estrellas).
//   · Recomendación    — un libro, un video, un podcast… que dejé para el resto.
// El orden "Mejor valoradas" sigue siendo cosa de mis Pausas: las otras dos no
// tienen estrellas mías y la API ya las manda al fondo.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Avatar } from "../components/Avatar";
import { Button } from "../components/Button";
import { SoloComunidad } from "../components/SoloComunidad";
import { Stars } from "../components/Stars";
import { api } from "../lib/api";
import { fechaCorta } from "../lib/format";
import { useStore } from "../store";
import { TIPOS_RECOMENDACION } from "../lib/types";
import type { ItemBaul, ItemFicha, ItemRecomendacion } from "../lib/types";
import "./baul.css";

type Orden = "reciente" | "valoradas";
type Filtro = "todo" | "reflexion" | "compartidas" | "privadas" | "recomendaciones" | "comunidad";

const FILTROS: { id: Filtro; label: string }[] = [
  { id: "todo", label: "Todas" },
  { id: "reflexion", label: "Con reflexión" },
  { id: "recomendaciones", label: "Recomendaciones" },
  // "De mi comunidad" en vez de "Guardadas": dice de dónde vienen, no qué hice
  // con ellas (guardar es el gesto; la comunidad es el lugar).
  { id: "comunidad", label: "De mi comunidad" },
  { id: "compartidas", label: "Compartidas" },
  { id: "privadas", label: "Privadas" },
];

/** El discriminante del contrato: `tipo: "recomendacion"` vs. "pausa" (o ausente). */
export function esRecomendacion(it: ItemFicha): it is ItemRecomendacion {
  return it.tipo === "recomendacion";
}

/** El tipo de una recomendación, en cristiano ("libro" → "Libro"). */
export function nombreTipo(tipo: string): string {
  return TIPOS_RECOMENDACION.find((t) => t.id === tipo)?.label || "Otro";
}

export function Baul() {
  const navigate = useNavigate();
  const { perfil } = useStore();
  const [items, setItems] = useState<ItemFicha[] | null>(null);
  const [orden, setOrden] = useState<Orden>("reciente");
  const [filtro, setFiltro] = useState<Filtro>("todo");
  const [invitar, setInvitar] = useState(false);

  useEffect(() => {
    setItems(null);
    api.baulCompleto(orden).then(setItems).catch(() => setItems([]));
  }, [orden]);

  const visibles = (items || []).filter((it) => {
    const reco = esRecomendacion(it);
    const guardada = !reco && it.guardada === true;
    if (filtro === "recomendaciones") return reco;
    if (filtro === "comunidad") return guardada;
    // "Con reflexión" es de las Pausas: una recomendación es texto de punta a punta.
    if (filtro === "reflexion") return !reco && !!it.reflexion;
    // Compartida / privada es lo que YO decidí publicar: las guardadas quedan
    // fuera (su visibilidad es la del dueño, no la mía).
    if (filtro === "compartidas") return !guardada && it.visibilidad === "compartida";
    if (filtro === "privadas") return !guardada && it.visibilidad !== "compartida";
    return true;
  });

  const vacioPorFiltro = items !== null && items.length > 0 && visibles.length === 0;
  // Escribir una recomendación es de quien es parte; leer las suyas, no (por eso
  // el candado está en el CTA y no en la lista).
  const puedeRecomendar = perfil?.limites.recomendaciones === true;

  const agregarRecomendacion = () => {
    if (puedeRecomendar) navigate("/baul/recomendacion/nueva");
    else setInvitar(true);
  };

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

      {/* WS30 · C2.2 · dejar algo que te hizo bien, al lado de lo que viviste. */}
      <div className="baul-cta actions-stack">
        <Button variant="secondary" full onClick={agregarRecomendacion}>
          Agregar recomendación
        </Button>
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

      {visibles.map((it) =>
        esRecomendacion(it) ? (
          <FilaRecomendacion
            key={it.id}
            item={it}
            onOpen={() => navigate(`/baul/${it.id}`)}
          />
        ) : (
          <FilaPausa key={it.id} item={it} onOpen={() => navigate(`/baul/${it.id}`)} />
        ),
      )}

      {invitar && (
        <SoloComunidad
          titulo="Las recomendaciones son de quienes son parte"
          cuerpo="Un libro, un video, un podcast que te hizo bien: dejarlo en tu Baúl y compartirlo con tu comunidad es de quienes sostienen este lugar sin anuncios."
          onClose={() => setInvitar(false)}
        />
      )}
    </div>
  );
}

/** Una Pausa: la que viví (con estrellas) o la que guardé de alguien (con su cara). */
function FilaPausa({ item, onOpen }: { item: ItemBaul; onOpen: () => void }) {
  const guardada = item.guardada === true;
  const apodo = item.de?.apodo || "alguien";

  return (
    <button className="entry" onClick={onOpen}>
      <span className="entry-spine" style={{ background: item.carta.categoria.color_accent }} />
      <div className="entry-body">
        <div className="entry-top">
          <span className="entry-top-left">
            {guardada ? (
              <span className="pill-guardada">Pausa de {apodo}</span>
            ) : (
              <span className="pill-pausa">Pausa</span>
            )}
            <span className="entry-cat" style={{ color: item.carta.categoria.color_text }}>
              {item.carta.categoria.nombre}
            </span>
          </span>
          <span className="entry-top-right">
            {/* La marca "compartida" es sobre MI decisión: en una ficha ajena no
                significa nada (siempre lo está, o no estaría en la lista). */}
            {!guardada && item.visibilidad === "compartida" && (
              <span className="entry-compartida">compartida</span>
            )}
            <span className="entry-date">{fechaCorta(item.fecha)}</span>
          </span>
        </div>
        <p className="entry-frase">{item.carta.frase}</p>
        {item.reflexion && <p className="entry-refl">{item.reflexion}</p>}
        {guardada && (
          <p className="entry-de">
            <Avatar apodo={apodo} fotoUrl={item.de?.foto_url} size={22} />
            <span>{apodo}</span>
          </p>
        )}
        <div className="entry-marks">
          {/* Las estrellas son siempre mías: una Pausa guardada llega sin ellas. */}
          {item.estrellas != null && (
            <span className="entry-mark stars-sm">
              <Stars value={item.estrellas} readOnly />
            </span>
          )}
          {item.fotos.length > 0 && (
            <span className="entry-mark">◦ {item.fotos.length} foto{item.fotos.length > 1 ? "s" : ""}</span>
          )}
        </div>
      </div>
    </button>
  );
}

/** Una recomendación: el tipo, el título y las primeras líneas de por qué. */
function FilaRecomendacion({
  item,
  onOpen,
}: {
  item: ItemRecomendacion;
  onOpen: () => void;
}) {
  return (
    <button className="entry" onClick={onOpen}>
      {/* Sin pilar: el lomo toma el tono del papel, para que no imite una carta. */}
      <span className="entry-spine" style={{ background: "var(--sand-line)" }} />
      <div className="entry-body">
        <div className="entry-top">
          <span className="entry-top-left">
            <span className="pill-reco">Recomendación</span>
            <span className="entry-reco-tipo">{nombreTipo(item.tipo_recomendacion)}</span>
          </span>
          <span className="entry-top-right">
            {item.visibilidad === "compartida" && (
              <span className="entry-compartida">compartida</span>
            )}
            <span className="entry-date">{fechaCorta(item.fecha)}</span>
          </span>
        </div>
        <p className="entry-reco-titulo">{item.titulo}</p>
        <p className="entry-reco-texto">{item.texto}</p>
        {item.url && <span className="entry-reco-link">◦ con enlace</span>}
      </div>
    </button>
  );
}

// WS30 · C2.1 · La vitrina de otra persona (`/comunidad/:usuarioId`).
//
// Arriba, quién es: su cara, su apodo, su nombre y el botón del vínculo (el
// mismo de la pestaña Comunidad, `CtaVinculo`). Debajo, lo que decidió compartir:
// sus Pausas y sus recomendaciones, mezcladas por fecha tal como las manda el
// backend (`GET /api/fichas/de/{id}`).
//
// `fichas: null` NO es un error ni un "no tiene nada": es un perfil privado sin
// vínculo. Se dice con todas las letras y se ofrece la solicitud, que es la
// salida. Aceptar o que te acepten cambia lo que se ve, así que al cambiar el
// vínculo la vitrina se vuelve a pedir.
//
// WS30 · C2b · dos cosas más, del Q/A de Tomás:
//   · Sus Pausas y sus recomendaciones dejan de ir mezcladas: cada una en su
//     pestaña, con su conteo y su vacío amable. Arranca en Pausas.
//   · Si ya está en mi comunidad, hay una salida: "Quitar de mi comunidad", con
//     su pregunta antes (nunca de un toque). Al quitarla, la vitrina se vuelve
//     a pedir: si su perfil es privado, deja de verse (`fichas: null`).

import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Avatar } from "../components/Avatar";
import { Button } from "../components/Button";
import { CtaVinculo } from "./Comunidad";
import { api, assetUrl } from "../lib/api";
import { fechaCorta } from "../lib/format";
import { TIPOS_RECOMENDACION } from "../lib/types";
import type { BaulAjeno, FichaAjena, ItemRecomendacion } from "../lib/types";
import "./comunidad.css";

type Pestana = "pausas" | "recomendaciones";

export function PerfilAjeno() {
  const { usuarioId = "" } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<BaulAjeno | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pestana, setPestana] = useState<Pestana>("pausas");
  // La pregunta de "quitar de mi comunidad" y el momento en que se está yendo.
  const [confirmarQuitar, setConfirmarQuitar] = useState(false);
  const [quitando, setQuitando] = useState(false);

  const cargar = useCallback(() => {
    api
      .baulDe(usuarioId)
      .then((d) => {
        setData(d);
        setError(null);
      })
      .catch((e) => setError((e as Error).message));
  }, [usuarioId]);

  useEffect(cargar, [cargar]);

  const quitar = async () => {
    if (quitando) return;
    setQuitando(true);
    try {
      await api.quitarDeMiComunidad(usuarioId);
      setConfirmarQuitar(false);
      // La vitrina cambia con el vínculo: si su perfil es privado, lo que sigue
      // es el mensaje de perfil privado, no una lista vieja.
      cargar();
    } catch (e) {
      setConfirmarQuitar(false);
      setError((e as Error).message);
    } finally {
      setQuitando(false);
    }
  };

  if (error)
    return (
      <div>
        <button className="back-link" onClick={() => navigate("/comunidad")}>
          ← Comunidad
        </button>
        <div className="center-note">{error}</div>
      </div>
    );
  if (!data) return <div className="center-note">…</div>;

  const { persona, fichas } = data;
  const nombre = [persona.nombre, persona.apellido].filter(Boolean).join(" ");
  const enMiComunidad = (persona.vinculo ?? "ninguno") === "aceptada";

  // Cada pestaña tiene su lista: el backend las manda mezcladas por fecha y acá
  // se separan por su `tipo`, sin reordenar nada.
  const pausas = (fichas || []).filter((f): f is FichaAjena => f.tipo !== "recomendacion");
  const recos = (fichas || []).filter(
    (f): f is ItemRecomendacion => f.tipo === "recomendacion",
  );

  return (
    <div className="comunidad">
      <button className="back-link" onClick={() => navigate("/comunidad")}>
        ← Comunidad
      </button>

      <div className="com-perfil-head">
        <Avatar apodo={persona.apodo} fotoUrl={persona.foto_url} size={88} />
        <h1 className="com-perfil-apodo">{persona.apodo}</h1>
        {nombre && <p className="com-perfil-nombre">{nombre}</p>}
        <div className="com-perfil-cta">
          <CtaVinculo
            persona={persona}
            onVinculo={cargar}
            onError={setError}
            onQuitar={enMiComunidad ? () => setConfirmarQuitar(true) : undefined}
          />
        </div>
      </div>

      {fichas === null ? (
        <p className="com-perfil-privado">
          Perfil privado. Envíale una solicitud para ver sus Pausas.
        </p>
      ) : (
        <>
          {/* Dos pestañas, el mismo control de dos posiciones que el orden del Baúl. */}
          <div className="com-tabs">
            <div className="segmented" role="radiogroup" aria-label="Qué ver de esta persona">
              <button
                type="button"
                role="radio"
                aria-checked={pestana === "pausas"}
                className={pestana === "pausas" ? "is-on" : ""}
                onClick={() => setPestana("pausas")}
              >
                Pausas{pausas.length > 0 ? ` (${pausas.length})` : ""}
              </button>
              <button
                type="button"
                role="radio"
                aria-checked={pestana === "recomendaciones"}
                className={pestana === "recomendaciones" ? "is-on" : ""}
                onClick={() => setPestana("recomendaciones")}
              >
                Recomendaciones{recos.length > 0 ? ` (${recos.length})` : ""}
              </button>
            </div>
          </div>

          {pestana === "pausas" ? (
            pausas.length === 0 ? (
              <p className="com-vacio">Todavía no compartió Pausas.</p>
            ) : (
              <div className="com-fichas">
                {pausas.map((f) => (
                  <PausaCompartida
                    key={f.id}
                    ficha={f}
                    onAbrir={() => navigate(`/comunidad/ficha/${f.id}`)}
                  />
                ))}
              </div>
            )
          ) : recos.length === 0 ? (
            <p className="com-vacio">Todavía no compartió recomendaciones.</p>
          ) : (
            <div className="com-fichas">
              {recos.map((r) => (
                <FilaRecomendacion
                  key={r.id}
                  item={r}
                  onAbrir={() =>
                    navigate(`/comunidad/${usuarioId}/recomendacion/${r.id}`)
                  }
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* —— Quitar de mi comunidad: la pregunta antes, y el rojo en el sí —— */}
      {confirmarQuitar && (
        <div className="modal-backdrop" onClick={() => setConfirmarQuitar(false)}>
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label={`Quitar a ${persona.apodo} de tu comunidad`}
            onClick={(e) => e.stopPropagation()}
          >
            <h3>¿Quitar a {persona.apodo} de tu comunidad?</h3>
            <p>
              Dejarán de ver las Pausas que compartes, y tú las suyas. Pueden volver a
              enviarse una solicitud.
            </p>
            <div className="modal-actions">
              <Button variant="danger" full disabled={quitando} onClick={quitar}>
                {quitando ? "Un momento…" : "Sí, quitar"}
              </Button>
              <Button
                variant="tertiary"
                disabled={quitando}
                onClick={() => setConfirmarQuitar(false)}
              >
                Conservar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// —— Una Pausa suya: se toca y se abre entera ————————————————————————————————
function PausaCompartida({ ficha, onAbrir }: { ficha: FichaAjena; onAbrir: () => void }) {
  const cat = ficha.carta.categoria;
  return (
    <button type="button" className="com-ficha" onClick={onAbrir}>
      <span className="com-mini">
        <span className="com-mini-band" style={{ background: cat.color_accent }} />
        <img className="com-mini-dibujo" src={assetUrl(cat.img)} alt="" />
      </span>
      <span className="com-ficha-datos">
        <span className="com-ficha-top">
          <span className="com-ficha-cat" style={{ color: cat.color_text }}>
            {cat.nombre}
          </span>
          <span className="com-ficha-fecha">{fechaCorta(ficha.fecha)}</span>
        </span>
        <span className="com-ficha-frase">{ficha.carta.frase}</span>
        {ficha.reflexion && <span className="com-ficha-refl">{ficha.reflexion}</span>}
      </span>
    </button>
  );
}

// —— Una recomendación suya: acá solo el resumen; se lee en su pantalla ————
function FilaRecomendacion({
  item,
  onAbrir,
}: {
  item: ItemRecomendacion;
  onAbrir: () => void;
}) {
  const etiqueta =
    TIPOS_RECOMENDACION.find((t) => t.id === item.tipo_recomendacion)?.label ?? "Otro";
  return (
    <button type="button" className="com-reco-fila" onClick={onAbrir}>
      <span className="com-reco-top">
        <span className="com-pill">Recomendación</span>
        <span className="com-ficha-cat">{etiqueta}</span>
        <span className="com-ficha-fecha" style={{ marginLeft: "auto" }}>
          {fechaCorta(item.fecha)}
        </span>
      </span>
      <span className="com-reco-titulo">{item.titulo}</span>
      <span className="com-reco-resumen">{item.texto}</span>
    </button>
  );
}

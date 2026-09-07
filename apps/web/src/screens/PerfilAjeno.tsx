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

import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Avatar } from "../components/Avatar";
import { CtaVinculo } from "./Comunidad";
import { api, assetUrl } from "../lib/api";
import { fechaCorta } from "../lib/format";
import { TIPOS_RECOMENDACION } from "../lib/types";
import type { BaulAjeno, FichaAjena, ItemRecomendacion } from "../lib/types";
import "./comunidad.css";

export function PerfilAjeno() {
  const { usuarioId = "" } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<BaulAjeno | null>(null);
  const [error, setError] = useState<string | null>(null);

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
          <CtaVinculo persona={persona} onVinculo={cargar} onError={setError} />
        </div>
      </div>

      {fichas === null ? (
        <p className="com-perfil-privado">
          Perfil privado. Envíale una solicitud para ver sus Pausas.
        </p>
      ) : fichas.length === 0 ? (
        <div className="empty">
          <p className="empty-title">Todavía no compartió nada.</p>
          <p className="empty-body">
            Cuando abra una Pausa a su comunidad, la vas a encontrar aquí.
          </p>
        </div>
      ) : (
        <div className="com-fichas">
          {fichas.map((f) =>
            f.tipo === "recomendacion" ? (
              <Recomendacion key={f.id} item={f} />
            ) : (
              <PausaCompartida
                key={f.id}
                ficha={f}
                onAbrir={() => navigate(`/comunidad/ficha/${f.id}`)}
              />
            ),
          )}
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

// —— Una recomendación suya: se lee entera acá, no tiene detrás ————————————
function Recomendacion({ item }: { item: ItemRecomendacion }) {
  const etiqueta =
    TIPOS_RECOMENDACION.find((t) => t.id === item.tipo_recomendacion)?.label ?? "Otro";
  return (
    <article className="com-reco">
      <div className="com-reco-top">
        <span className="com-pill">Recomendación</span>
        <span className="com-ficha-cat">{etiqueta}</span>
        <span className="com-ficha-fecha" style={{ marginLeft: "auto" }}>
          {fechaCorta(item.fecha)}
        </span>
      </div>
      <h3 className="com-reco-titulo">{item.titulo}</h3>
      <p className="com-reco-texto">{item.texto}</p>
      {item.url && (
        <a className="com-reco-url" href={item.url} target="_blank" rel="noreferrer noopener">
          Ver más
        </a>
      )}
    </article>
  );
}

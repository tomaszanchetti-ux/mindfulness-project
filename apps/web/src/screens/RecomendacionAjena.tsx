// WS30 · C2b · La recomendación de OTRA persona, en su propia pantalla
// (`/comunidad/:usuarioId/recomendacion/:recomendacionId`).
//
// Por qué existe: en la vitrina del perfil una recomendación se leía entera
// inline y empujaba todo lo demás. Ahora allá va resumida y acá se lee completa,
// como se abre una Pausa.
//
// No hay endpoint de una recomendación ajena por id: se lee la vitrina de su
// dueño (`GET /api/fichas/de/{id}`, que ya trae solo las compartidas y respeta
// la regla de lectura) y se busca la que se pidió. Si no está —la borró, la hizo
// privada, o se rompió el vínculo— se dice, y se vuelve.
//
// El botón del enlace dice a dónde lleva: "Ver en YouTube" acompaña mejor que
// "Abrir el enlace", que no promete nada.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Avatar } from "../components/Avatar";
import { api } from "../lib/api";
import { fechaCorta } from "../lib/format";
import { TIPOS_RECOMENDACION } from "../lib/types";
import type { ItemRecomendacion, Persona } from "../lib/types";
import "./comunidad.css";

/** El rótulo del botón según a dónde lleva el enlace. Sin dominio → el genérico. */
export function rotuloEnlace(url: string): string {
  let host = "";
  try {
    host = new URL(url).hostname.toLowerCase();
  } catch {
    return "Abrir el enlace";
  }
  if (host.endsWith("youtube.com") || host.endsWith("youtu.be")) return "Ver en YouTube";
  if (host.endsWith("spotify.com")) return "Abrir en Spotify";
  if (host.endsWith("apple.com")) return "Abrir en Apple";
  if (
    host.includes("amazon.") ||
    host.includes("casadellibro") ||
    host.includes("planetadelibros")
  )
    return "Ver el libro";
  return "Abrir el enlace";
}

export function RecomendacionAjena() {
  const { usuarioId = "", recomendacionId = "" } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState<ItemRecomendacion | null>(null);
  const [persona, setPersona] = useState<Persona | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    let vivo = true;
    setCargando(true);
    api
      .baulDe(usuarioId)
      .then((d) => {
        if (!vivo) return;
        setPersona(d.persona);
        const encontrada = (d.fichas || []).find(
          (f): f is ItemRecomendacion =>
            f.tipo === "recomendacion" && f.id === recomendacionId,
        );
        setItem(encontrada ?? null);
        setCargando(false);
      })
      .catch((e) => {
        if (!vivo) return;
        setError((e as Error).message);
        setCargando(false);
      });
    return () => {
      vivo = false;
    };
  }, [usuarioId, recomendacionId]);

  const volver = () => navigate(`/comunidad/${usuarioId}`);

  if (cargando) return <div className="center-note">…</div>;

  if (error || !item)
    return (
      <div className="comunidad">
        <button className="back-link" onClick={volver}>
          ← Volver
        </button>
        <div className="center-note">
          {error || "Esta recomendación ya no está disponible."}
        </div>
      </div>
    );

  const etiqueta =
    TIPOS_RECOMENDACION.find((t) => t.id === item.tipo_recomendacion)?.label ?? "Otro";
  const de = item.de || persona;

  return (
    <div className="comunidad">
      <button className="back-link" onClick={volver}>
        ← Volver
      </button>

      <article className="com-reco">
        <div className="com-reco-top">
          <span className="com-pill">Recomendación</span>
          <span className="com-ficha-cat">{etiqueta}</span>
          <span className="com-ficha-fecha" style={{ marginLeft: "auto" }}>
            {fechaCorta(item.fecha)}
          </span>
        </div>

        <h1 className="com-reco-titulo">{item.titulo}</h1>
        <p className="com-reco-texto">{item.texto}</p>

        {de && (
          <p className="com-reco-de">
            <Avatar apodo={de.apodo} fotoUrl={de.foto_url} size={26} />
            <span>de {de.apodo}</span>
          </p>
        )}

        {item.url && (
          <a
            className="btn btn-primary btn-full com-reco-boton"
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {rotuloEnlace(item.url)}
          </a>
        )}
      </article>
    </div>
  );
}

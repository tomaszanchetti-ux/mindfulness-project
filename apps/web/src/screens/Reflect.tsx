// Guardar la pausa (§12.2, reframe WS14). El usuario ya vivió la pausa y escribió
// en su diario afuera; acá la guarda en el Baúl con extras OPCIONALES (nota,
// estrellas, foto). Se puede guardar sin escribir ni una palabra (regla M3).
//
// WS24 · A2.2: los límites (caracteres de la nota, fotos por pausa) NO se
// hardcodean acá — salen de `perfil.limites`, que arma el backend según el plan.
// Debajo de las estrellas se invita a un comentario sobre la carta: feedback
// privado para Dwellia (nunca se publica), con la pregunta según la puntuación.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { FotoPrivada } from "../components/FotoPrivada";
import { Stars } from "../components/Stars";
import { api } from "../lib/api";
import { useStore } from "../store";
import type { CartaDelDia, FotoSubida } from "../lib/types";

// El comentario de la carta no depende del plan: el backend lo topea en 150
// para todos (schemas.py · CierreRitual.comentario_carta).
const COMENTARIO_MAX = 150;

export function Reflect() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { perfil } = useStore();

  const [data, setData] = useState<CartaDelDia | null>(null);
  const [texto, setTexto] = useState("");
  const [estrellas, setEstrellas] = useState<number | null>(null);
  const [comentario, setComentario] = useState("");
  // WS16: las fotos se suben a Storage apenas se eligen (y se pueden quitar).
  const [fotos, setFotos] = useState<FotoSubida[]>([]);
  const [subiendo, setSubiendo] = useState(false);
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    api.cartaDelDia().then(setData).catch(() => setData(null));
  }, [id]);

  // Los límites del plan (el backend es el que manda; acá solo se muestran).
  const limites = perfil?.limites ?? null;

  const agregarFoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // permite volver a elegir el mismo archivo
    if (!file || !limites || fotos.length >= limites.fotos_max || subiendo) return;
    setSubiendo(true);
    try {
      const f = await api.subirFoto(id, file);
      setFotos((cur) => [...cur, f]);
    } catch (err) {
      alert((err as Error).message);
    } finally {
      setSubiendo(false);
    }
  };

  const quitarFoto = (f: FotoSubida) => {
    setFotos((cur) => cur.filter((x) => x.id !== f.id));
    api.borrarFoto(f.id).catch(() => {});
  };

  const guardar = async () => {
    setGuardando(true);
    try {
      const dicho = comentario.trim();
      await api.cerrarRitual(id, {
        reflexion: texto.trim() ? texto.trim() : null,
        estrellas,
        // Vacío = no se manda: nunca pisa un comentario anterior con nada.
        ...(dicho ? { comentario_carta: dicho } : {}),
        completada: true,
      });
      navigate(`/cierre/${id}`, { replace: true });
    } catch (e) {
      setGuardando(false);
      alert((e as Error).message);
    }
  };

  // Sin perfil todavía no sabemos los límites: esperamos antes de pedir nada.
  if (!limites) return <div className="center-note">Preparando tu pausa…</div>;

  const near = texto.length > limites.reflexion_max - 30;
  const nearComentario = comentario.length > COMENTARIO_MAX - 30;
  // La pregunta cambia con la puntuación: si la carta no llegó, preguntamos qué
  // le hubiese gustado recibir (eso es lo que afina el motor).
  const preguntaComentario =
    estrellas != null && estrellas <= 2
      ? "¿Qué te hubiese gustado recibir?"
      : "¿Algo que quieras decirnos de esta carta?";

  return (
    <div>
      <button className="back-link" onClick={() => navigate(-1)}>
        ← Volver
      </button>

      <div className="screen-head">
        <h1 className="screen-title">Guarda tu pausa de hoy</h1>
      </div>

      {data && (
        <div className="reflect-recap">
          <div className="frase">{data.carta.frase}</div>
        </div>
      )}

      <div className="pausa-block">
        <p className="pausa-label">Tu pausa de hoy</p>
        <p className="pausa-text">{data?.carta.prompt}</p>
      </div>

      {/* WS14 · guardar con extras opcionales: nota → puntuar → foto. */}
      <p className="reflect-invite">
        Si escribiste en tu diario, puedes dejar aquí una nota para tu Baúl.
      </p>
      <textarea
        className="textarea"
        placeholder="¿Qué te dejó esta pausa? (opcional)…"
        maxLength={limites.reflexion_max}
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
      />
      <div className={`counter ${near ? "near" : ""}`}>
        {texto.length} / {limites.reflexion_max}
      </div>
      <p className="helper" style={{ marginTop: 2 }}>Una palabra, una frase o nada. Esto es tuyo.</p>

      <div style={{ textAlign: "center", margin: "20px 0 14px" }}>
        <p className="completion-stars-label">¿Cuánto te llegó? (opcional)</p>
        <Stars value={estrellas} onChange={setEstrellas} />
      </div>

      {/* WS24 · A2.2 · El comentario aparece recién cuando hay estrellas: la
          puntuación abre la puerta y la pregunta se adapta a ella. */}
      {estrellas != null && (
        <div className="comentario-carta">
          <label className="comentario-pregunta" htmlFor="comentario-carta">
            {preguntaComentario} <span className="comentario-opcional">(opcional)</span>
          </label>
          <textarea
            id="comentario-carta"
            className="textarea textarea-mini"
            placeholder="Cuéntanos en una línea…"
            maxLength={COMENTARIO_MAX}
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
          />
          <div className={`counter ${nearComentario ? "near" : ""}`}>
            {comentario.length} / {COMENTARIO_MAX}
          </div>
          <p className="comentario-privado">Solo lo lee Dwellia, nunca se publica.</p>
        </div>
      )}

      <p className="reflect-helper-mem">
        {limites.fotos_max > 1
          ? `Conmemórala con fotos (hasta ${limites.fotos_max}, opcional):`
          : "Conmemórala con una foto (opcional):"}
      </p>
      <div className="photo-row">
        {fotos.map((f) => (
          <span key={f.id} className="photo-thumb-wrap">
            <FotoPrivada className="photo-thumb" src={f.url} />
            <button
              type="button"
              className="photo-remove"
              aria-label="Quitar foto"
              onClick={() => quitarFoto(f)}
            >
              ×
            </button>
          </span>
        ))}
        {fotos.length < limites.fotos_max && (
          <label className={`photo-add ${subiendo ? "busy" : ""}`}>
            <span className="plus">{subiendo ? "…" : "+"}</span>
            <span>{subiendo ? "Subiendo" : "Foto"}</span>
            <input
              type="file"
              accept="image/*"
              hidden
              disabled={subiendo}
              onChange={agregarFoto}
            />
          </label>
        )}
      </div>

      <div className="actions-stack">
        <Button
          variant="primary"
          full
          disabled={guardando}
          onClick={guardar}
        >
          {guardando ? "Guardando…" : "Guardar en mi Baúl"}
        </Button>
      </div>
    </div>
  );
}

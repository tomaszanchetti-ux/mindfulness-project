// Guardar la pausa (§12.2, reframe WS14). El usuario ya vivió la pausa y escribió
// en su diario afuera; acá la guarda en el Baúl con extras OPCIONALES (nota,
// estrellas, foto). Se puede guardar sin escribir ni una palabra (regla M3).

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { FotoPrivada } from "../components/FotoPrivada";
import { Stars } from "../components/Stars";
import { api } from "../lib/api";
import type { CartaDelDia, FotoSubida } from "../lib/types";

const LIMITE = 250;
const MAX_FOTOS = 3;

export function Reflect() {
  const { id = "" } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState<CartaDelDia | null>(null);
  const [texto, setTexto] = useState("");
  const [estrellas, setEstrellas] = useState<number | null>(null);
  // WS16: las fotos se suben a Storage apenas se eligen (y se pueden quitar).
  const [fotos, setFotos] = useState<FotoSubida[]>([]);
  const [subiendo, setSubiendo] = useState(false);
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    api.cartaDelDia().then(setData).catch(() => setData(null));
  }, [id]);

  const agregarFoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // permite volver a elegir el mismo archivo
    if (!file || fotos.length >= MAX_FOTOS || subiendo) return;
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
      await api.cerrarRitual(id, {
        reflexion: texto.trim() ? texto.trim() : null,
        estrellas,
        completada: true,
      });
      navigate(`/cierre/${id}`, { replace: true });
    } catch (e) {
      setGuardando(false);
      alert((e as Error).message);
    }
  };

  const near = texto.length > LIMITE - 30;

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
        maxLength={LIMITE}
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
      />
      <div className={`counter ${near ? "near" : ""}`}>
        {texto.length} / {LIMITE}
      </div>
      <p className="helper" style={{ marginTop: 2 }}>Una palabra, una frase o nada. Esto es tuyo.</p>

      <div style={{ textAlign: "center", margin: "20px 0 14px" }}>
        <p className="completion-stars-label">¿Cuánto te llegó? (opcional)</p>
        <Stars value={estrellas} onChange={setEstrellas} />
      </div>

      <p className="reflect-helper-mem">Conmemórala con una foto (opcional):</p>
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
        {fotos.length < MAX_FOTOS && (
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

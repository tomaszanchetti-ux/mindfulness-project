// Reflexionar (§12.2). Convertir la consigna en algo propio, sin presión.
// Todo opcional: se puede guardar sin escribir ni una palabra (regla M3).

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { Stars } from "../components/Stars";
import { api } from "../lib/api";
import type { CartaDelDia } from "../lib/types";

const LIMITE = 250;

export function Reflect() {
  const { id = "" } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState<CartaDelDia | null>(null);
  const [texto, setTexto] = useState("");
  const [estrellas, setEstrellas] = useState<number | null>(null);
  const [fotos, setFotos] = useState<string[]>([]); // preview local (sin endpoint aún)
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    api.cartaDelDia().then(setData).catch(() => setData(null));
  }, []);

  const agregarFoto = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && fotos.length < 3) setFotos((f) => [...f, URL.createObjectURL(file)]);
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

      {data && (
        <div className="reflect-recap">
          <div className="frase">{data.carta.frase}</div>
        </div>
      )}

      <p className="reflect-prompt">{data?.carta.prompt}</p>

      {/* WS10 · el cierre constante: el fin es escribir en tu diario (afuera). */}
      <div className="cierre-diario">
        <p className="cierre-diario-title">Escribe en tu diario lo que sentiste.</p>
        <p className="cierre-diario-sub">
          En tu cuaderno, fuera del teléfono. Eso es la pausa.
        </p>
      </div>

      <p className="reflect-helper-mem">Y si quieres, deja una nota corta aquí para tu Baúl:</p>
      <textarea
        className="textarea"
        placeholder="Una nota de ayuda-memoria (opcional)…"
        maxLength={LIMITE}
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
      />
      <div className={`counter ${near ? "near" : ""}`}>
        {texto.length} / {LIMITE}
      </div>

      <div className="photo-row">
        {fotos.map((src, i) => (
          <img key={i} className="photo-thumb" src={src} alt="" />
        ))}
        {fotos.length < 3 && (
          <label className="photo-add">
            <span className="plus">+</span>
            <span>Foto</span>
            <input type="file" accept="image/*" hidden onChange={agregarFoto} />
          </label>
        )}
      </div>
      {fotos.length > 0 && (
        <p className="photo-note">
          Las fotos se ven aquí pero todavía no se guardan (falta el endpoint de subida).
        </p>
      )}

      <div style={{ textAlign: "center", margin: "8px 0 20px" }}>
        <p className="completion-stars-label">¿Quieres valorar esta pausa? (opcional)</p>
        <Stars value={estrellas} onChange={setEstrellas} />
      </div>

      <p className="helper">Puede ser una palabra, una frase o nada. Esto es tuyo.</p>

      <div className="actions-stack">
        <Button variant="primary" full disabled={guardando} onClick={guardar}>
          {guardando ? "Guardando…" : "Guardar en mi Baúl"}
        </Button>
      </div>
    </div>
  );
}

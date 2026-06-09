// Reflexionar (§12.2). Convertir la consigna en algo propio, sin presión.
// Todo opcional: se puede guardar sin escribir ni una palabra (regla M3).

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { Stars } from "../components/Stars";
import { api } from "../lib/api";
import { CARTA_DEMO, TOUR_ID, useTutorial } from "../tutorial";
import type { CartaDelDia } from "../lib/types";

const LIMITE = 250;

export function Reflect() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const tut = useTutorial();

  const [data, setData] = useState<CartaDelDia | null>(null);
  const [texto, setTexto] = useState("");
  const [estrellas, setEstrellas] = useState<number | null>(null);
  const [fotos, setFotos] = useState<string[]>([]); // preview local (sin endpoint aún)
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    // Modo tutorial: carta de ejemplo, sin API.
    if (tut.activo || id === TOUR_ID) {
      setData({
        carta: CARTA_DEMO,
        entrega: {
          id: TOUR_ID,
          fecha: new Date().toISOString(),
          estrellas: null,
          completada: false,
          reflexion: null,
        },
      });
      return;
    }
    api.cartaDelDia().then(setData).catch(() => setData(null));
  }, [tut.activo, id]);

  // Edge: ruta del tour abierta sin tour activo (recarga) → volver a Hoy.
  useEffect(() => {
    if (id === TOUR_ID && !tut.activo) navigate("/hoy", { replace: true });
  }, [id, tut.activo, navigate]);

  const agregarFoto = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && fotos.length < 3) setFotos((f) => [...f, URL.createObjectURL(file)]);
  };

  const guardar = async () => {
    if (tut.activo) return; // en el tour, el avance lo maneja el recorrido
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

      <div className="pausa-block">
        <p className="pausa-label">Tu pausa de hoy</p>
        <p className="pausa-text">{data?.carta.prompt}</p>
      </div>

      {/* WS10 · paso de vuelta a la app: reflexionar sobre la actividad → puntuar → foto opcional. */}
      <p className="reflect-invite">Tómate un momento para reflexionar sobre tu pausa.</p>
      <textarea
        className="textarea"
        data-tour="refl-text"
        placeholder="¿Qué te dejó? Escribe tu reflexión…"
        maxLength={LIMITE}
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
      />
      <div className={`counter ${near ? "near" : ""}`}>
        {texto.length} / {LIMITE}
      </div>
      <p className="helper" style={{ marginTop: 2 }}>Una palabra, una frase o nada. Esto es tuyo.</p>

      <div style={{ textAlign: "center", margin: "20px 0 14px" }} data-tour="refl-stars">
        <p className="completion-stars-label">¿Cuánto te llegó? (opcional)</p>
        <Stars value={estrellas} onChange={setEstrellas} />
      </div>

      <p className="reflect-helper-mem">Conmemórala con una foto (opcional):</p>
      <div className="photo-row" data-tour="refl-photo">
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

      <div className="actions-stack">
        <Button
          variant="primary"
          full
          data-tour="refl-save"
          disabled={guardando}
          onClick={guardar}
        >
          {guardando ? "Guardando…" : "Guardar en mi Baúl"}
        </Button>
      </div>
    </div>
  );
}

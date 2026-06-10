// Home / Hoy (§19). El lugar más simple de la app: recibir la consigna y decidir
// qué hacer con ella. Carta cerrada (frente) → "Ver mi pausa" revela el dorso.
// Si ya guardaste la pausa de hoy, la Home pasa a modo "hecho" (en calma).
//
// Primer uso (WS14): dos nudges contextuales sobre la carta REAL — señalan la carta
// y el botón Guardar. Se ven una sola vez por usuario/dispositivo (lib/nudges).

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Spotlight } from "../components/Spotlight";
import { useAuth } from "../auth";
import { api } from "../lib/api";
import { fechaLarga, saludo } from "../lib/format";
import { marcarNudgeVisto, nudgeVisto } from "../lib/nudges";
import { useStore } from "../store";
import type { CartaDelDia } from "../lib/types";

export function Home() {
  const navigate = useNavigate();
  const { perfil } = useStore();
  const uid = useAuth().user?.uid ?? "anon";
  const [data, setData] = useState<CartaDelDia | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [flipped, setFlipped] = useState(false);
  const [nudgeCarta, setNudgeCarta] = useState(() => !nudgeVisto(uid, "carta"));
  const [nudgeGuardar, setNudgeGuardar] = useState(() => !nudgeVisto(uid, "guardar"));

  useEffect(() => {
    api
      .cartaDelDia()
      .then((d) => {
        setData(d);
        // Modo "hecho": si ya guardaste hoy, mostramos la carta girada (la frase a la vista).
        if (d.entrega.completada) setFlipped(true);
      })
      .catch((e) => setError((e as Error).message));
  }, []);

  if (error) return <div className="center-note">{error}</div>;
  if (!data) return <div className="center-note">Preparando tu pausa…</div>;

  const { carta, entrega } = data;
  const hecha = entrega.completada;

  return (
    <div>
      <div className="home-greet">
        <p className="screen-kicker">
          {saludo(perfil?.hora_aviso)}
          {perfil?.apodo ? `, ${perfil.apodo}` : ""}.
        </p>
        <p className="home-date">{fechaLarga(entrega.fecha)}</p>
      </div>

      <div className="home-card-wrap" data-nudge="home-card">
        <Card carta={carta} flipped={flipped} onFlip={() => setFlipped((f) => !f)} />
      </div>

      {hecha ? (
        // —— Modo "hecho": pausa de hoy ya guardada. En calma, sin nada que exigir. ——
        <>
          <p className="home-done-note">
            Ya viviste tu pausa de hoy. Mañana te espera una nueva.
          </p>
          <div className="actions-stack">
            <Button
              variant="primary"
              full
              onClick={() => navigate(`/baul/${entrega.id}`)}
            >
              {entrega.reflexion ? "Ver mi reflexión" : "Ver mi pausa de hoy"}
            </Button>
          </div>
        </>
      ) : !flipped ? (
        <div className="actions-stack">
          <Button variant="primary" full onClick={() => setFlipped(true)}>
            Ver mi pausa
          </Button>
        </div>
      ) : (
        <div className="actions-stack">
          <Button
            variant="primary"
            full
            data-nudge="guardar"
            onClick={() => navigate(`/reflexionar/${entrega.id}`)}
          >
            Guardar
          </Button>
          <Button
            variant="secondary"
            full
            onClick={() => navigate(`/compartir/${entrega.id}`)}
          >
            Compartir
          </Button>
        </div>
      )}

      {/* —— Nudges de primer uso (solo con la pausa de hoy pendiente) —— */}
      {!hecha && !flipped && nudgeCarta && (
        <Spotlight
          targetSelector='[data-nudge="home-card"]'
          titulo="Esta es tu carta de hoy"
          cuerpo="Cada día recibes una nueva. Tócala para descubrir tu pausa."
          onDone={() => {
            marcarNudgeVisto(uid, "carta");
            setNudgeCarta(false);
          }}
        />
      )}
      {!hecha && flipped && nudgeGuardar && (
        <Spotlight
          targetSelector='[data-nudge="guardar"]'
          titulo="Vive tu pausa, lejos del teléfono"
          cuerpo="La carta te propone una pausa sin el teléfono. Al volver, escribe en tu diario lo que sentiste y toca Guardar. Si quieres regalar la carta, toca Compartir."
          onDone={() => {
            marcarNudgeVisto(uid, "guardar");
            setNudgeGuardar(false);
          }}
        />
      )}
    </div>
  );
}

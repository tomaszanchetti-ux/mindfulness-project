// Home / Hoy (§19). El lugar más simple de la app: recibir la consigna y decidir
// qué hacer con ella. Carta cerrada (frente) → "Ver mi pausa" revela el dorso.
// Si ya guardaste la pausa de hoy, la Home pasa a modo "hecho" (en calma).

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { api } from "../lib/api";
import { fechaLarga, saludo } from "../lib/format";
import { useStore } from "../store";
import type { CartaDelDia } from "../lib/types";

export function Home() {
  const navigate = useNavigate();
  const { perfil } = useStore();
  const [data, setData] = useState<CartaDelDia | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [flipped, setFlipped] = useState(false);

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

      <div className="home-card-wrap">
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
            onClick={() => navigate(`/reflexionar/${entrega.id}`)}
          >
            Reflexionar
          </Button>
          <Button
            variant="secondary"
            full
            onClick={() => navigate(`/cierre/${entrega.id}`)}
          >
            Guardar
          </Button>
        </div>
      )}
    </div>
  );
}

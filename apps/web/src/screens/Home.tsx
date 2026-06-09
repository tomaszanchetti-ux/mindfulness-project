// Home / Hoy (§19). El lugar más simple de la app: recibir la consigna y decidir
// qué hacer con ella. Carta cerrada (frente) → "Ver mi pausa" revela el dorso.

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
      .then(setData)
      .catch((e) => setError((e as Error).message));
  }, []);

  if (error) return <div className="center-note">{error}</div>;
  if (!data) return <div className="center-note">Preparando tu pausa…</div>;

  const { carta, entrega } = data;

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
        <Card carta={carta} flipped={flipped} onFlip={() => setFlipped(true)} />
        {!flipped && <p className="flip-hint">Toca la carta para descubrirla</p>}
      </div>

      {!flipped ? (
        <div className="actions-stack">
          <Button variant="primary" full onClick={() => setFlipped(true)}>
            Ver mi pausa
          </Button>
        </div>
      ) : (
        <div className="actions-stack">
          <p className="cierre-constante">
            Haz tu pausa afuera. Al volver, escribe en tu diario lo que sentiste.
          </p>
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

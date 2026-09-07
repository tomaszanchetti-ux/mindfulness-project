// WS30 · C2.1 · La Pausa extra (`/pausa/:entregaId`).
//
// Es la carta de otra persona que elegiste vivir "ahora": el backend ya creó tu
// entrega (`extra`) y acá se vive igual que la carta del día — la carta cerrada,
// se toca para descubrir el dorso, y "Ya la hice" lleva al mismo cierre de
// siempre (`/reflexionar/:id`). Sin tab bar: es un momento de foco.
//
// No reemplaza la carta de hoy ni la gasta: la del día sigue esperándote.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { api } from "../lib/api";
import type { CartaDelDia } from "../lib/types";
import "./comunidad.css";

export function PausaExtra() {
  const { entregaId = "" } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<CartaDelDia | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [flipped, setFlipped] = useState(false);

  useEffect(() => {
    let vivo = true;
    api
      .entrega(entregaId)
      .then((d) => {
        if (!vivo) return;
        setData(d);
        // Ya vivida: la carta se muestra girada, con su frase a la vista.
        if (d.entrega.completada) setFlipped(true);
      })
      .catch((e) => vivo && setError((e as Error).message));
    return () => {
      vivo = false;
    };
  }, [entregaId]);

  const volver = () => (history.length > 1 ? navigate(-1) : navigate("/hoy"));

  if (error)
    return (
      <div>
        <button className="back-link" onClick={volver}>
          ← Volver
        </button>
        <div className="center-note">{error}</div>
      </div>
    );
  if (!data) return <div className="center-note">Preparando tu Pausa…</div>;

  const { carta, entrega } = data;
  const hecha = entrega.completada;

  return (
    <div className="pausa-extra">
      <button className="back-link" onClick={volver}>
        ← Volver
      </button>

      <p className="pausa-extra-kicker">Tu Pausa extra de hoy</p>
      {entrega.de && <p className="pausa-extra-de">La carta que compartió {entrega.de.apodo}</p>}

      <div className="pausa-extra-card">
        <Card carta={carta} flipped={flipped} onFlip={() => setFlipped((f) => !f)} />
      </div>

      {hecha ? (
        <>
          <p className="pausa-extra-nota">Ya viviste esta Pausa. Quedó en tu Baúl.</p>
          <div className="actions-stack">
            <Button variant="primary" full onClick={() => navigate(`/baul/${entrega.id}`)}>
              Ver mi Pausa
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
            Ya la hice
          </Button>
        </div>
      )}
    </div>
  );
}

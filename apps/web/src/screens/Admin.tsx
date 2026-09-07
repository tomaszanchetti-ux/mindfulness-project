// WS28 · B2.2b · El adminland (/admin): el escritorio de Dwellia.
//
// La única cuenta con `perfil.es_admin` entra acá desde Perfil (la ruta y su
// guarda las cablea `main.tsx`; esta pantalla solo se dibuja). No es una pestaña
// de la app: es otro lugar, con su propia puerta de salida arriba a la derecha.
//
// Tres bloques, uno visible a la vez:
//   1 · Cola de aprobación — el funnel de cada carta propuesta y la decisión.
//   2 · Termómetro         — los números del sistema (solo lectura).
//   3 · Comentarios        — el feedback privado de las cartas, agrupado.
//
// El 403 no se maneja bloque por bloque: si el backend cierra la puerta, se
// cierra la pantalla entera y se ofrece volver.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { Cola } from "./admin/Cola";
import { Comentarios } from "./admin/Comentarios";
import { Termometro } from "./admin/Termometro";
import "./admin.css";

type Bloque = "cola" | "termometro" | "comentarios";

const BLOQUES: { id: Bloque; label: string }[] = [
  { id: "cola", label: "Cola de aprobación" },
  { id: "termometro", label: "Termómetro" },
  { id: "comentarios", label: "Comentarios" },
];

export function Admin() {
  const navigate = useNavigate();
  const [bloque, setBloque] = useState<Bloque>("cola");
  const [cerrado, setCerrado] = useState(false);

  const volver = () => navigate("/perfil");

  if (cerrado) {
    return (
      <div className="adm">
        <div className="empty adm-cerrado">
          <p className="empty-title">Esta pantalla es solo para Dwellia.</p>
          <p className="empty-body">
            Tu cuenta no tiene acceso al escritorio. Si crees que es un error,
            escríbenos.
          </p>
          <Button variant="secondary" onClick={volver}>
            Volver a la app
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="adm">
      <header className="adm-head">
        <div className="adm-head-txt">
          <p className="screen-kicker">Dwellia</p>
          <h1 className="screen-title">Escritorio de Dwellia</h1>
        </div>
        <Button variant="secondary" onClick={volver}>
          Volver a la app
        </Button>
      </header>

      <div
        className="adm-tabs segmented"
        role="tablist"
        aria-label="Bloques del escritorio"
      >
        {BLOQUES.map((b) => (
          <button
            key={b.id}
            type="button"
            role="tab"
            aria-selected={bloque === b.id}
            className={bloque === b.id ? "is-on" : ""}
            onClick={() => setBloque(b.id)}
          >
            {b.label}
          </button>
        ))}
      </div>

      {bloque === "cola" && <Cola onCerrado={() => setCerrado(true)} />}
      {bloque === "termometro" && <Termometro onCerrado={() => setCerrado(true)} />}
      {bloque === "comentarios" && <Comentarios onCerrado={() => setCerrado(true)} />}
    </div>
  );
}

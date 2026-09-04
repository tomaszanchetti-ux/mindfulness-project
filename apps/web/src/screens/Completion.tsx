// Cierre del ritual (§12.3). Materializa "la mejor sesión termina".
// Marca la entrega como completada (idempotente; no pisa la reflexión ya escrita).
// Acción primaria = Cerrar.
//
// WS25 · el loop del envío vive acá: quien acaba de guardar es invitado —sin
// presión— a enviarle la Pausa a alguien. Se puede volver a enviar las veces
// que quiera desde el Baúl.

import { useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { api } from "../lib/api";

export function Completion() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const marcada = useRef(false);

  useEffect(() => {
    if (marcada.current) return;
    marcada.current = true;
    // Sólo confirma "completada"; reflexión/estrellas (si las hubo) quedan intactas.
    api.cerrarRitual(id, { completada: true }).catch(() => {});
  }, [id]);

  return (
    <div className="completion">
      <div className="completion-mark">✓</div>
      <h2 className="completion-title">Listo por hoy.</h2>
      <p className="completion-body">
        Guardamos esta Pausa en tu Baúl.
        <br />
        Puedes volver cuando quieras.
      </p>

      <p className="completion-invite">¿Quieres enviar a alguien la Pausa?</p>

      <div className="actions-stack" style={{ width: "100%" }}>
        <Button variant="primary" full onClick={() => navigate("/hoy", { replace: true })}>
          Cerrar
        </Button>
        <Button
          variant="secondary"
          full
          onClick={() => navigate(`/compartir/${id}`)}
        >
          Enviar
        </Button>
      </div>
    </div>
  );
}

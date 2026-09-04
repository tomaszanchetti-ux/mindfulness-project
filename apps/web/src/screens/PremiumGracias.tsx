// WS24 · A2.1 · vuelta del Checkout de Stripe (?session_id=…): refresca el perfil y
// agradece.
//
// Quien activa premium es el webhook, no el navegador: cuando el usuario aterriza
// aquí puede que Stripe todavía no nos haya avisado. Por eso reintentamos el perfil
// hasta 5 veces cada 2 s y, si sigue en free, lo decimos con calma — nunca como
// error: el cobro salió bien, solo falta que llegue la confirmación.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { useStore } from "../store";
import "./premium.css";

const INTENTOS = 5;
const ESPERA_MS = 2000;

export function PremiumGracias() {
  const navigate = useNavigate();
  const { refrescarPerfil } = useStore();
  const [estado, setEstado] = useState<"confirmando" | "listo" | "pendiente">(
    "confirmando",
  );

  useEffect(() => {
    let vivo = true;
    (async () => {
      for (let i = 0; i < INTENTOS; i++) {
        const p = await refrescarPerfil();
        if (!vivo) return;
        if (p?.plan === "premium") {
          setEstado("listo");
          return;
        }
        if (i < INTENTOS - 1) {
          await new Promise((r) => setTimeout(r, ESPERA_MS));
          if (!vivo) return;
        }
      }
      setEstado("pendiente");
    })();
    return () => {
      vivo = false;
    };
  }, [refrescarPerfil]);

  return (
    <div className="premium-gracias">
      <h1 className="premium-gracias-titulo">Gracias por apoyar Dwellia</h1>

      {estado === "listo" && (
        <p className="premium-gracias-texto">
          Ya eres parte de Dwellia premium. Tu aporte sostiene un lugar sin anuncios
          y sin prisa, para ti y para quien llegue después.
        </p>
      )}
      {estado === "confirmando" && (
        <p className="premium-gracias-texto">Estamos confirmando tu aporte…</p>
      )}
      {estado === "pendiente" && (
        <p className="premium-gracias-texto">
          Estamos confirmando tu aporte; en unos minutos lo verás en tu Perfil. Tu
          pausa de hoy te espera igual.
        </p>
      )}

      <div className="actions-stack">
        <Button onClick={() => navigate("/hoy")}>Ir a mi Pausa</Button>
      </div>
    </div>
  );
}

// Retorno del enlace mágico (M1). La persona llega acá desde su correo; si el
// email quedó guardado (mismo dispositivo) completamos solos, si no lo pedimos.

import { useEffect, useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import {
  completarMagicLink,
  emailGuardado,
  esMagicLink,
} from "../lib/firebase";

type Estado = "completando" | "pedir-email" | "error";

export function LoginEmail() {
  const navigate = useNavigate();
  const [estado, setEstado] = useState<Estado>("completando");
  const [email, setEmail] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const esEnlace = useRef(esMagicLink()).current;

  const completar = async (direccion: string) => {
    setOcupado(true);
    try {
      await completarMagicLink(direccion);
      navigate("/", { replace: true });
    } catch {
      setEstado("error");
    } finally {
      setOcupado(false);
    }
  };

  useEffect(() => {
    if (!esEnlace) return;
    const guardado = emailGuardado();
    if (guardado) {
      completar(guardado);
    } else {
      // Enlace abierto en otro dispositivo o navegador: confirmamos el email.
      setEstado("pedir-email");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // URL sin enlace válido (entró a mano): al login normal.
  if (!esEnlace) return <Navigate to="/login" replace />;

  return (
    <div className="login">
      <h1 className="login-logo">Dwellia</h1>

      {estado === "completando" && (
        <p className="login-fine">Entrando…</p>
      )}

      {estado === "pedir-email" && (
        <div className="login-actions">
          <p className="login-fine" style={{ margin: 0 }}>
            Confirma tu email para terminar de entrar.
          </p>
          <input
            type="email"
            className="time-input"
            style={{ width: "100%", textAlign: "center" }}
            placeholder="tu@email.com"
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && email.trim() && completar(email.trim())}
          />
          <Button
            variant="primary"
            full
            disabled={ocupado || !email.trim()}
            onClick={() => completar(email.trim())}
          >
            {ocupado ? "Entrando…" : "Entrar"}
          </Button>
        </div>
      )}

      {estado === "error" && (
        <div className="login-actions">
          <p className="login-fine login-error" style={{ margin: 0 }}>
            El enlace ya no es válido o el email no coincide.
          </p>
          <Button variant="primary" full onClick={() => navigate("/login", { replace: true })}>
            Volver a intentar
          </Button>
        </div>
      )}
    </div>
  );
}

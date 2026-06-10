// Login (M1): passwordless real con Firebase — Google o enlace mágico por email.
// En dev no hay Firebase: un botón directo entra con el usuario sintético.

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { enviarMagicLink, loginConGoogle } from "../lib/firebase";
import { useStore } from "../store";

type Modo = "opciones" | "email" | "enviado";

export function Login() {
  const navigate = useNavigate();
  const { perfil } = useStore();
  const [modo, setModo] = useState<Modo>("opciones");
  const [email, setEmail] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");

  const entrarDev = () => {
    navigate(perfil?.onboarding_completo ? "/hoy" : "/onboarding");
  };

  const conGoogle = async () => {
    setError("");
    setOcupado(true);
    try {
      await loginConGoogle();
      // onAuthStateChanged hace el resto; SoloAnonimo redirige a "/".
    } catch {
      setError("No pudimos iniciar sesión con Google. Intenta de nuevo.");
    } finally {
      setOcupado(false);
    }
  };

  const enviarEnlace = async () => {
    const v = email.trim();
    if (!v || !v.includes("@")) {
      setError("Escribe un email válido.");
      return;
    }
    setError("");
    setOcupado(true);
    try {
      await enviarMagicLink(v);
      setModo("enviado");
    } catch {
      setError("No pudimos enviar el enlace. Intenta de nuevo.");
    } finally {
      setOcupado(false);
    }
  };

  return (
    <div className="login">
      <h1 className="login-logo">Dwellia</h1>
      <p className="login-tag login-slogan">One quiet pause a day</p>

      {modo === "opciones" && (
        <div className="login-actions">
          <Button variant="primary" full onClick={conGoogle} disabled={ocupado}>
            Continuar con Google
          </Button>
          <Button
            variant="secondary"
            full
            onClick={() => {
              setError("");
              setModo("email");
            }}
            disabled={ocupado}
          >
            Recibir un enlace por email
          </Button>
          {import.meta.env.DEV && (
            <Button variant="tertiary" full onClick={entrarDev}>
              Entrar (dev)
            </Button>
          )}
        </div>
      )}

      {modo === "email" && (
        <div className="login-actions">
          <input
            type="email"
            className="time-input"
            style={{ width: "100%", textAlign: "center" }}
            placeholder="tu@email.com"
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && enviarEnlace()}
          />
          <Button variant="primary" full onClick={enviarEnlace} disabled={ocupado}>
            {ocupado ? "Enviando…" : "Enviarme el enlace"}
          </Button>
          <Button variant="tertiary" full onClick={() => setModo("opciones")}>
            Volver
          </Button>
        </div>
      )}

      {modo === "enviado" && (
        <div className="login-actions">
          <p className="login-fine" style={{ margin: 0 }}>
            Te enviamos un enlace a <b>{email.trim()}</b>.
            <br />
            Ábrelo desde este dispositivo para entrar.
          </p>
          <Button variant="tertiary" full onClick={() => setModo("opciones")}>
            Volver
          </Button>
        </div>
      )}

      {error && <p className="login-fine login-error">{error}</p>}

      <p className="login-fine">
        Sin contraseñas. Entras con un toque.
        <br />
        Lo que escribas y guardes es tuyo.
      </p>
    </div>
  );
}

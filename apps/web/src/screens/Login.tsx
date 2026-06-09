// Login (M1). En el prototipo es passwordless simulado: el modo dev de la API ya
// resuelve el usuario `dev|user`. Con Expo, estos botones serán Google + magic-link
// de Firebase Auth (mismo contrato, sin password).

import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { useStore } from "../store";

export function Login() {
  const navigate = useNavigate();
  const { perfil } = useStore();

  const entrar = () => {
    navigate(perfil?.onboarding_completo ? "/hoy" : "/onboarding");
  };

  return (
    <div className="login">
      <h1 className="login-logo">Dwellia</h1>
      <p className="login-tag login-slogan">One quiet pause a day</p>

      <div className="login-actions">
        <Button variant="primary" full onClick={entrar}>
          Continuar con Google
        </Button>
        <Button variant="secondary" full onClick={entrar}>
          Recibir un enlace por email
        </Button>
      </div>

      <p className="login-fine">
        Sin contraseñas. Entrás con un toque.
        <br />
        Lo que escribas y guardes es tuyo.
      </p>
    </div>
  );
}

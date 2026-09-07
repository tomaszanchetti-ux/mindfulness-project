// WS29 · C0 · La Pausa extra (`/pausa/:entregaId`): vivir una Pausa que no es la
// carta de hoy. Se hace a pantalla completa, como el ritual: sin tab bar.
// Lugar reservado: la C2 la construye.

import { useNavigate } from "react-router-dom";

export function PausaExtra() {
  const navigate = useNavigate();
  return (
    <div>
      <button className="back-link" onClick={() => navigate("/hoy")}>
        ← Hoy
      </button>
      <div className="center-note">Muy pronto.</div>
    </div>
  );
}

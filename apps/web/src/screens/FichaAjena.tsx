// WS29 · C0 · La ficha de la Pausa de otra persona (`/comunidad/ficha/:entregaId`).
// Se lee a pantalla completa, como el detalle del Baúl: sin tab bar.
// Lugar reservado: la C2 la trae del backend y la muestra con <Ficha modo="ajena" />.

import { useNavigate } from "react-router-dom";

export function FichaAjena() {
  const navigate = useNavigate();
  return (
    <div>
      <button className="back-link" onClick={() => navigate("/comunidad")}>
        ← Comunidad
      </button>
      <div className="center-note">Muy pronto.</div>
    </div>
  );
}

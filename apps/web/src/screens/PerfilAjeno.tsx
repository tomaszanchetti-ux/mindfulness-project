// WS29 · C0 · El perfil de otra persona de tu Comunidad (`/comunidad/:usuarioId`).
// Lugar reservado: la C2 trae quién es y sus Pausas compartidas.

import { useNavigate } from "react-router-dom";

export function PerfilAjeno() {
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

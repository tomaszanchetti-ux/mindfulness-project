// Página pública del regalo (§12.6). El receptor abre y ve, SIN login ni instalar.
// Es el destino, no un trampolín: girar la carta es parte de ver. CTA suave al final.

import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { assetUrl, api } from "../lib/api";
import type { Regalo } from "../lib/types";

export function PublicShare() {
  const { token = "" } = useParams();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  // Vista previa del remitente (no la ve el destinatario real, que no tiene "home").
  const preview = params.get("preview") === "1";
  const [regalo, setRegalo] = useState<Regalo | null | undefined>(undefined);
  const [flipped, setFlipped] = useState(false);

  useEffect(() => {
    api.regalo(token).then(setRegalo).catch(() => setRegalo(null));
  }, [token]);

  if (regalo === undefined) return <div className="center-note">…</div>;

  if (regalo === null)
    return (
      <div className="empty">
        <p className="empty-title">Esta pausa ya no está disponible.</p>
        <p className="empty-body">
          Puede que quien la envió haya decidido dejar de compartirla.
        </p>
        <Button variant="primary" onClick={() => navigate("/login")}>
          Crear mi propia pausa
        </Button>
      </div>
    );

  const de = regalo.de || "Alguien";

  return (
    <>
      {preview && (
        <button className="back-link" onClick={() => navigate("/hoy")}>
          ← Inicio
        </button>
      )}
      <div className="gift">
        <p className="gift-intro">{de} pensó en vos.</p>

      <div className="gift-card-wrap">
        <Card carta={regalo.carta} flipped={flipped} onFlip={() => setFlipped((f) => !f)} />
        {!flipped && <p className="flip-hint">Tocá la carta para abrirla</p>}
      </div>

      {regalo.nota && (
        <div className="gift-message">
          <span className="gift-quote">“</span>
          <p className="gift-message-text">{regalo.nota}</p>
          {regalo.de && <p className="gift-message-from">— {regalo.de}</p>}
        </div>
      )}

      {/* Modo ejercicio (premium): reflexión + fotos, si la entrega sigue viva. */}
      {regalo.modo === "ejercicio" && regalo.reflexion && (
        <p className="gift-message-text" style={{ fontStyle: "italic", margin: "0 0 12px" }}>
          {regalo.reflexion}
        </p>
      )}
      {regalo.modo === "ejercicio" && regalo.fotos && regalo.fotos.length > 0 && (
        <div className="detail-photos" style={{ justifyContent: "center", marginBottom: 14 }}>
          {regalo.fotos.map((src, i) => (
            <img key={i} src={assetUrl(src)} alt="" />
          ))}
        </div>
      )}

      <div className="gift-cta">
        <p>¿Querés recibir una pausa así, cada día?</p>
        <Button variant="secondary" full onClick={() => navigate("/login")}>
          Configurá tu cuenta para tener tus propias cartas
        </Button>
        </div>
      </div>
    </>
  );
}

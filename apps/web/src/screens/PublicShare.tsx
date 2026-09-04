// Página del regalo (§12.6). El receptor abre el enlace y ve la Pausa que le
// enviaron: la carta, la nota, y —si viajaron— la reflexión y las fotos.
// Es el destino, no un trampolín: girar la carta es parte de ver. CTA suave al final.
//
// WS25 · el regalo YA NO es público: `GET /api/c/{token}` exige login, y la ruta
// vive detrás de `RequireAuth` (sin onboarding obligatorio — alguien recién
// llegado puede abrir el regalo antes de configurar nada). Por eso las fotos se
// bajan con `FotoPrivada` (fetch autenticado), no con un <img src> directo.

import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { FotoPrivada } from "../components/FotoPrivada";
import { api } from "../lib/api";
import type { Regalo } from "../lib/types";

export function PublicShare() {
  const { token = "" } = useParams();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  // Vista previa del remitente: la misma pantalla, con un "volver" arriba.
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
        <p className="empty-title">Esta Pausa ya no está disponible.</p>
        <p className="empty-body">
          Puede que quien la envió haya decidido dejar de compartirla.
        </p>
        <Button variant="primary" onClick={() => navigate("/hoy")}>
          Ir a mi Pausa de hoy
        </Button>
      </div>
    );

  const de = regalo.de || "Alguien";

  return (
    <>
      {preview && (
        <button className="back-link" onClick={() => navigate(-1)}>
          ← Volver
        </button>
      )}
      <div className="gift">
        <p className="gift-intro">{de} te envió esta Pausa.</p>

      <div className="gift-card-wrap">
        <Card carta={regalo.carta} flipped={flipped} onFlip={() => setFlipped((f) => !f)} />
        {!flipped && <p className="flip-hint">Toca la carta para abrirla</p>}
      </div>

      {regalo.nota && (
        <div className="gift-message">
          <span className="gift-quote">“</span>
          <p className="gift-message-text">{regalo.nota}</p>
          {regalo.de && <p className="gift-message-from">— {regalo.de}</p>}
        </div>
      )}

      {/* Ficha entera: la reflexión y las fotos, si viajaron con el regalo. */}
      {regalo.modo === "ejercicio" && regalo.reflexion && (
        <p className="gift-message-text" style={{ fontStyle: "italic", margin: "0 0 12px" }}>
          {regalo.reflexion}
        </p>
      )}
      {regalo.modo === "ejercicio" && regalo.fotos && regalo.fotos.length > 0 && (
        <div className="detail-photos" style={{ justifyContent: "center", marginBottom: 14 }}>
          {regalo.fotos.map((src) => (
            <FotoPrivada key={src} src={src} />
          ))}
        </div>
      )}

      <div className="gift-cta">
        <p>¿Quieres recibir una Pausa así, cada día?</p>
        <Button variant="secondary" full onClick={() => navigate("/")}>
          Empieza tu propia Pausa diaria
        </Button>
        </div>
      </div>
    </>
  );
}

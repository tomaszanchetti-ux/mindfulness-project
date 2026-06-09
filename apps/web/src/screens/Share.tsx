// Compartir (§12.5). El gesto íntimo: "Vi esto y pensé en ti."
// v1 free: se envía SÓLO la carta + una nota personal (≤250). El modo "ejercicio"
// (sumar reflexión/fotos) queda para premium — el backend lo sigue soportando.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { api } from "../lib/api";
import { CARTA_DEMO, PASO_SHARE_LINK, TOUR_ID, useTutorial } from "../tutorial";
import type { Compartido, ItemBaul } from "../lib/types";

const LIMITE = 250;

// Enlace de ejemplo para el tour (no se genera nada real).
const TOUR_LINK: Compartido = { token: "ejemplo", url: "/c/ejemplo", modo: "carta_sola" };

export function Share() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const tut = useTutorial();
  const [item, setItem] = useState<ItemBaul | null | undefined>(undefined);
  const [nota, setNota] = useState("");
  const [link, setLink] = useState<Compartido | null>(null);
  const [copiado, setCopiado] = useState(false);
  const [generando, setGenerando] = useState(false);

  useEffect(() => {
    // Modo tutorial: carta de ejemplo, sin tocar la API.
    if (tut.activo || id === TOUR_ID) {
      setItem({
        id: TOUR_ID,
        fecha: new Date().toISOString(),
        estrellas: null,
        completada: true,
        reflexion: null,
        fotos: [],
        carta: CARTA_DEMO,
      });
      return;
    }
    api
      .baul("reciente")
      .then((list) => setItem(list.find((x) => x.id === id) ?? null))
      .catch(() => setItem(null));
  }, [id, tut.activo]);

  // Edge: ruta del tour abierta sin tour activo (recarga) → volver a Hoy.
  useEffect(() => {
    if (id === TOUR_ID && !tut.activo) navigate("/hoy", { replace: true });
  }, [id, tut.activo, navigate]);

  // Recordar el enlace ya generado: si el remitente va al preview y vuelve, sigue acá
  // (no pierde el botón Copiar ni tiene que generar otro).
  useEffect(() => {
    if (tut.activo) return;
    const saved = sessionStorage.getItem(`share:${id}`);
    if (saved) {
      try {
        setLink(JSON.parse(saved));
      } catch {
        /* ignorar */
      }
    }
  }, [id, tut.activo]);

  const generar = async () => {
    if (tut.activo) return; // en el tour el avance lo maneja el recorrido
    setGenerando(true);
    try {
      // v1 free: siempre "carta sola" (la carta + tu nota, sin tus datos).
      const c = await api.compartir(id, "carta_sola", nota.trim() || undefined);
      setLink(c);
      sessionStorage.setItem(`share:${id}`, JSON.stringify(c));
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setGenerando(false);
    }
  };

  // Durante el tour, el enlace "aparece" en el paso correspondiente.
  const linkEfectivo = tut.activo ? (tut.paso >= PASO_SHARE_LINK ? TOUR_LINK : null) : link;
  const urlCompleta = linkEfectivo ? `${window.location.origin}${linkEfectivo.url}` : "";

  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(urlCompleta);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      /* clipboard no disponible */
    }
  };

  const near = nota.length > LIMITE - 30;

  return (
    <div>
      <button className="back-link" onClick={() => navigate(-1)}>← Volver</button>

      <div className="screen-head share-head">
        <h1 className="screen-title">Vi esto y pensé en ti.</h1>
      </div>

      {item && (
        <div className="share-preview">
          <Card carta={item.carta} flipped />
        </div>
      )}

      {!linkEfectivo ? (
        <>
          <textarea
            className="textarea"
            data-tour="share-note"
            placeholder="Agrega una nota personal (opcional)…"
            maxLength={LIMITE}
            value={nota}
            onChange={(e) => setNota(e.target.value)}
            style={{ minHeight: 92 }}
          />
          <div className={`counter ${near ? "near" : ""}`}>
            {nota.length} / {LIMITE}
          </div>

          <div className="actions-stack" style={{ marginTop: 10 }}>
            <Button variant="primary" full data-tour="share-generate" disabled={generando} onClick={generar}>
              {generando ? "Generando…" : "Generar enlace"}
            </Button>
          </div>
        </>
      ) : (
        <>
          <div className="share-link" data-tour="share-link">
            <code>{urlCompleta}</code>
            <Button variant="secondary" onClick={copiar}>
              {copiado ? "Copiado ✓" : "Copiar"}
            </Button>
          </div>
          <div className="actions-stack">
            <Button variant="primary" full onClick={() => navigate(`${linkEfectivo.url}?preview=1`)}>
              Ver cómo lo recibe
            </Button>
            <Button variant="tertiary" onClick={() => navigate("/hoy")}>
              Listo
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

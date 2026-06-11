// Compartir (§12.5). El gesto íntimo: "Vi esto y pensé en ti."
// v1 free: se envía SÓLO la carta + una nota personal (≤150). El modo "ejercicio"
// (sumar reflexión/fotos) queda para premium — el backend lo sigue soportando.
//
// Loop WS14: se puede compartir ANTES de guardar (camino B). En ese caso, tras
// generar el enlace el CTA principal invita a guardar la pausa.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { api } from "../lib/api";
import type { Compartido, ItemBaul } from "../lib/types";

const LIMITE = 150; // free (WS19); premium subirá a ~500

export function Share() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState<ItemBaul | null | undefined>(undefined);
  const [nota, setNota] = useState("");
  const [link, setLink] = useState<Compartido | null>(null);
  const [copiado, setCopiado] = useState(false);
  const [generando, setGenerando] = useState(false);

  useEffect(() => {
    // El Baúl solo lista pausas guardadas; si venimos del camino B (compartir antes
    // de guardar) la entrega de hoy no está ahí → fallback a la carta del día.
    api
      .baul("reciente")
      .then(async (list) => {
        const enBaul = list.find((x) => x.id === id);
        if (enBaul) {
          setItem(enBaul);
          return;
        }
        const d = await api.cartaDelDia();
        if (d.entrega.id === id) {
          setItem({ ...d.entrega, fotos: [], carta: d.carta });
        } else {
          setItem(null);
        }
      })
      .catch(() => setItem(null));
  }, [id]);

  // Recordar el enlace ya generado: si el remitente va al preview y vuelve, sigue acá
  // (no pierde el botón Copiar ni tiene que generar otro). Se guarda también la nota
  // para poder mostrarla y retocarla (QA 10/06: antes quedaba inaccesible).
  useEffect(() => {
    const saved = sessionStorage.getItem(`share:${id}`);
    if (saved) {
      try {
        const c = JSON.parse(saved) as Compartido & { nota?: string };
        setLink(c);
        if (c.nota) setNota(c.nota);
      } catch {
        /* ignorar */
      }
    }
  }, [id]);

  const generar = async () => {
    setGenerando(true);
    try {
      // v1 free: siempre "carta sola" (la carta + tu nota, sin tus datos).
      const notaLimpia = nota.trim();
      const c = await api.compartir(id, "carta_sola", notaLimpia || undefined);
      setLink(c);
      sessionStorage.setItem(
        `share:${id}`,
        JSON.stringify({ ...c, nota: notaLimpia }),
      );
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setGenerando(false);
    }
  };

  // Volver a escribir: descarta el enlace de la vista (el regalo es el enlace nuevo
  // que se genere con la nota retocada) y reabre el campo de la nota.
  const cambiarNota = () => {
    sessionStorage.removeItem(`share:${id}`);
    setLink(null);
    setCopiado(false);
  };

  const urlCompleta = link ? `${window.location.origin}${link.url}` : "";

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
  // Loop WS14: si la pausa de hoy aún no se guardó, el siguiente paso es guardarla.
  const pendienteGuardar = item ? !item.completada : false;

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

      {!link ? (
        <>
          <textarea
            className="textarea"
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
            <Button variant="primary" full disabled={generando} onClick={generar}>
              {generando ? "Generando…" : "Generar enlace"}
            </Button>
          </div>
        </>
      ) : (
        <>
          {nota.trim() && (
            <p className="share-nota">
              <span className="share-nota-label">Tu nota · </span>
              {nota.trim()}
            </p>
          )}
          <div className="share-link">
            <code>{urlCompleta}</code>
            <Button variant="secondary" onClick={copiar}>
              {copiado ? "Copiado ✓" : "Copiar"}
            </Button>
          </div>
          <div className="actions-stack-pre">
            <Button variant="tertiary" onClick={cambiarNota}>
              {nota.trim() ? "Cambiar la nota" : "Agregar una nota"}
            </Button>
          </div>
          <div className="actions-stack">
            {pendienteGuardar ? (
              <>
                <Button variant="primary" full onClick={() => navigate(`/reflexionar/${id}`)}>
                  Guardar mi pausa
                </Button>
                <Button variant="secondary" full onClick={() => navigate(`${link.url}?preview=1`)}>
                  Ver cómo lo recibe
                </Button>
                <Button variant="tertiary" onClick={() => navigate("/hoy")}>
                  Más tarde
                </Button>
              </>
            ) : (
              <>
                <Button variant="primary" full onClick={() => navigate(`${link.url}?preview=1`)}>
                  Ver cómo lo recibe
                </Button>
                <Button variant="tertiary" onClick={() => navigate("/hoy")}>
                  Listo
                </Button>
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}

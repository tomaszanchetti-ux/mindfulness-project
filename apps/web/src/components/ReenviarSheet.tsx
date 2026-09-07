// WS29 · C0 · WS30 · C2.1 · El panel "Reenviar": elegir a alguien de mi comunidad
// (reenvío dentro de la app) o mandar el link por WhatsApp. Lo usan la ficha
// ajena (C2.1) y la ficha propia del Baúl (C2.2). La INTERFAZ la fijó C0 y no
// cambia:
//
//   <ReenviarSheet entregaId={id} abierto={bool} onClose={() => …}
//                  linkWhatsApp="https://…" />
//
// - `entregaId`: la Pausa que se reenvía (propia o ajena; el backend decide).
// - `linkWhatsApp`: el link que viaja por WhatsApp. Ficha propia: el link de
//   regalo `/c/{token}` (se crea con `api.compartir`); ficha ajena: el link
//   in-app `${origin}/comunidad/ficha/${entregaId}` (con login y la regla de
//   lectura). Si es null, el bloque de WhatsApp no existe.
//
// La comunidad se pide recién al abrir el panel: mientras nadie toca "Reenviar"
// no hay motivo para molestar al backend.

import { useEffect, useState } from "react";
import { Avatar } from "./Avatar";
import { Button } from "./Button";
import { api } from "../lib/api";
import type { Persona } from "../lib/types";
import "../screens/comunidad.css";

// WS30 · C2b · el comentario opcional que viaja con la Pausa. El tope es el del
// backend (`COMENTARIO_REENVIO_MAX`): acá se frena antes de llegar, y si igual
// rebota, el 422 viene en español y se muestra tal cual.
const COMENTARIO_MAX = 200;

export interface ReenviarSheetProps {
  entregaId: string;
  abierto: boolean;
  onClose: () => void;
  linkWhatsApp: string | null;
}

export function ReenviarSheet({ entregaId, abierto, onClose, linkWhatsApp }: ReenviarSheetProps) {
  const [gente, setGente] = useState<Persona[] | null>(null);
  const [enviando, setEnviando] = useState<string | null>(null);
  const [enviada, setEnviada] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [comentario, setComentario] = useState("");

  useEffect(() => {
    if (!abierto) return;
    let vivo = true;
    // Cada apertura arranca limpia: nadie quiere ver el error de la vez pasada.
    setEnviada(null);
    setError(null);
    setComentario("");
    api
      .miComunidad()
      .then((c) => {
        if (vivo) setGente(c.gente);
      })
      .catch((e) => {
        if (!vivo) return;
        setGente([]);
        setError((e as Error).message);
      });
    return () => {
      vivo = false;
    };
  }, [abierto]);

  if (!abierto) return null;

  const enviar = async (p: Persona) => {
    if (enviando) return;
    setEnviando(p.usuario_id);
    setError(null);
    try {
      await api.reenviar(entregaId, p.usuario_id, comentario);
      setEnviada(p.apodo);
      // Un momento para leer "Enviada a …" y el panel se va solo.
      setTimeout(onClose, 1100);
    } catch (e) {
      // Los mensajes del backend ya vienen en español ("Ya le enviaste esta
      // Pausa.", "No encontramos esta Pausa."): se muestran tal cual.
      setError((e as Error).message);
    } finally {
      setEnviando(null);
    }
  };

  const porWhatsApp = () => {
    if (!linkWhatsApp) return;
    const texto = `Te comparto una Pausa de Dwellia: ${linkWhatsApp}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(texto)}`, "_blank", "noopener");
    onClose();
  };

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div
        className="sheet"
        role="dialog"
        aria-modal="true"
        aria-label="Reenviar esta Pausa"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sheet-asa" aria-hidden />
        <h3 className="sheet-titulo">Reenviar</h3>
        <p className="sheet-nota">Que esta Pausa le llegue a alguien más.</p>

        {enviada ? (
          <p className="com-confirmacion">Enviada a {enviada}.</p>
        ) : (
          <>
            {error && <p className="com-aviso">{error}</p>}

            {/* Una línea tuya antes de la Pausa: opcional, y va con las dos
                salidas (dentro de Dwellia y por WhatsApp no: ahí viaja el link). */}
            <label className="sheet-lbl" htmlFor="reenvio-comentario">
              Un comentario para quien la recibe (opcional)
            </label>
            <textarea
              id="reenvio-comentario"
              className="textarea sheet-comentario"
              maxLength={COMENTARIO_MAX}
              placeholder="Por qué se la mandas."
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
            />
            <p className={`counter ${comentario.length > COMENTARIO_MAX - 20 ? "near" : ""}`}>
              {comentario.length}/{COMENTARIO_MAX}
            </p>

            <span className="sheet-lbl">A alguien de tu comunidad</span>
            {gente === null ? (
              <p className="sheet-vacio">…</p>
            ) : gente.length === 0 ? (
              <p className="sheet-vacio">Todavía no tienes a nadie en tu comunidad.</p>
            ) : (
              <div>
                {gente.map((p) => (
                  <button
                    key={p.usuario_id}
                    type="button"
                    className="sheet-persona"
                    disabled={!!enviando}
                    onClick={() => enviar(p)}
                  >
                    <Avatar apodo={p.apodo} fotoUrl={p.foto_url} size={38} />
                    <span>{enviando === p.usuario_id ? "Enviando…" : p.apodo}</span>
                  </button>
                ))}
              </div>
            )}

            {linkWhatsApp && (
              <>
                <hr className="sheet-sep" />
                <span className="sheet-lbl">Por WhatsApp</span>
                <Button variant="secondary" full onClick={porWhatsApp}>
                  Enviar por WhatsApp
                </Button>
              </>
            )}
          </>
        )}

        <div className="actions-stack sheet-cerrar">
          <Button variant="tertiary" onClick={onClose}>
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  );
}

// WS30 · C2.1 · La Pausa de otra persona (`/comunidad/ficha/:entregaId`).
//
// Se lee a pantalla completa, como el detalle del Baúl, con el MISMO componente
// (`components/Ficha.tsx`) en modo "ajena": sin estrellas, sin el switch de
// visibilidad y sin Eliminar. Las tres acciones las pone esta pantalla:
//
//   · Guardar en mi Baúl  — un interruptor (guardar / quitar). Aparece en el
//     Baúl como "Pausa de <apodo>" mientras el dueño la deje compartida.
//   · Hacer la Pausa      — vivir SU carta (premium). Dos caminos, en un panel:
//     "Hacer ahora" (nace una Pausa extra y se va a vivirla) o "Que sea mi
//     próxima carta" (entra a la cola de una: la próxima que llegue va a ser esa).
//   · Reenviar            — a alguien de mi comunidad o por WhatsApp, con el
//     link in-app de esta misma ficha (el `/c/{token}` es solo para las propias).
//
// Si la ficha es MÍA (llegué acá desde un link que reenvié) no se muestran ni
// Guardar ni Hacer la Pausa: ya es mi Pausa.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { Ficha } from "../components/Ficha";
import { ReenviarSheet } from "../components/ReenviarSheet";
import { SoloComunidad } from "../components/SoloComunidad";
import { api } from "../lib/api";
import { useStore } from "../store";
import type { FichaAjena as FichaAjenaTipo, ItemBaul, ModoPausa } from "../lib/types";
import "./comunidad.css";

// La ficha ajena no trae estrellas ni visibilidad (nunca salen de la cuenta del
// dueño), pero `Ficha` dibuja un `ItemBaul`: acá se completa lo que falta con lo
// único que puede ser — sin puntuación y compartida (si no, no estaría a la vista).
function comoItem(f: FichaAjenaTipo): ItemBaul {
  return {
    tipo: "pausa",
    id: f.id,
    fecha: f.fecha,
    estrellas: null,
    completada: true,
    reflexion: f.reflexion,
    fotos: f.fotos,
    carta: f.carta,
    visibilidad: "compartida",
    de: f.de,
    guardada: f.guardada,
  };
}

export function FichaAjena() {
  const { entregaId = "" } = useParams();
  const navigate = useNavigate();
  const { perfil } = useStore();

  const [ficha, setFicha] = useState<FichaAjenaTipo | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [guardada, setGuardada] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null); // error de una acción
  const [confirmacion, setConfirmacion] = useState<string | null>(null);

  const [verPausa, setVerPausa] = useState(false); // el panel "Hacer la Pausa"
  const [haciendo, setHaciendo] = useState<ModoPausa | null>(null);
  const [verPremium, setVerPremium] = useState(false);
  const [verReenviar, setVerReenviar] = useState(false);

  useEffect(() => {
    let vivo = true;
    api
      .fichaAjena(entregaId)
      .then((f) => {
        if (!vivo) return;
        setFicha(f);
        setGuardada(f.guardada);
      })
      .catch((e) => vivo && setError((e as Error).message));
    return () => {
      vivo = false;
    };
  }, [entregaId]);

  if (error)
    return (
      <div>
        <button className="back-link" onClick={() => navigate("/comunidad")}>
          ← Comunidad
        </button>
        <div className="center-note">{error}</div>
      </div>
    );
  if (!ficha) return <div className="center-note">…</div>;

  const esMia = !!perfil && ficha.de.usuario_id === perfil.usuario_id;
  const puedeHacerla = perfil?.limites.pausas_extra === true;

  const alternarGuardada = async () => {
    if (guardando) return;
    setGuardando(true);
    setAviso(null);
    setConfirmacion(null);
    try {
      if (guardada) {
        await api.quitarGuardada(ficha.id);
        setGuardada(false);
        setConfirmacion("La quitaste de tu Baúl.");
      } else {
        await api.guardarFicha(ficha.id);
        setGuardada(true);
        setConfirmacion("Guardada en tu Baúl.");
      }
    } catch (e) {
      setAviso((e as Error).message);
    } finally {
      setGuardando(false);
    }
  };

  const abrirPausa = () => {
    setAviso(null);
    setConfirmacion(null);
    if (!puedeHacerla) {
      setVerPremium(true);
      return;
    }
    setVerPausa(true);
  };

  const hacer = async (modo: ModoPausa) => {
    if (haciendo) return;
    setHaciendo(modo);
    setAviso(null);
    try {
      const r = await api.hacerPausa(ficha.id, modo);
      if (modo === "ahora" && r.entrega) {
        navigate(`/pausa/${r.entrega.id}`);
        return;
      }
      setVerPausa(false);
      setConfirmacion("Te va a llegar como tu próxima Pausa.");
    } catch (e) {
      // El backend contesta en español (403 de plan, 404 de la regla de lectura,
      // 422 del modo): se muestra tal cual, dentro del panel.
      setAviso((e as Error).message);
    } finally {
      setHaciendo(null);
    }
  };

  return (
    <div className="comunidad">
      <button className="back-link" onClick={() => navigate(-1)}>
        ← Volver
      </button>

      <Ficha
        item={comoItem(ficha)}
        modo="ajena"
        de={ficha.de.apodo}
        acciones={
          <div className="com-acciones">
            {!esMia && (
              <Button variant="secondary" full disabled={guardando} onClick={alternarGuardada}>
                {guardando
                  ? "Un momento…"
                  : guardada
                    ? "Quitar de mi Baúl"
                    : "Guardar en mi Baúl"}
              </Button>
            )}
            {!esMia && (
              <Button variant="primary" full onClick={abrirPausa}>
                Hacer la Pausa
              </Button>
            )}
            <Button variant="secondary" full onClick={() => setVerReenviar(true)}>
              Reenviar
            </Button>
            {confirmacion && <p className="com-confirmacion">{confirmacion}</p>}
            {aviso && !verPausa && <p className="com-error">{aviso}</p>}
          </div>
        }
      />

      {/* —— El panel de "Hacer la Pausa": los dos caminos —— */}
      {verPausa && (
        <div className="sheet-backdrop" onClick={() => setVerPausa(false)}>
          <div
            className="sheet"
            role="dialog"
            aria-modal="true"
            aria-label="Hacer esta Pausa"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sheet-asa" aria-hidden />
            <h3 className="sheet-titulo">Hacer esta Pausa</h3>
            <p className="sheet-nota">Vive la carta de {ficha.de.apodo} a tu manera.</p>

            {aviso && <p className="com-aviso">{aviso}</p>}

            <button
              type="button"
              className="sheet-opcion"
              disabled={!!haciendo}
              onClick={() => hacer("ahora")}
            >
              <span className="sheet-opcion-tit">
                {haciendo === "ahora" ? "Preparando tu Pausa…" : "Hacer ahora"}
              </span>
              <span className="sheet-opcion-nota">
                Se suma a tu día como una Pausa extra. La de hoy sigue siendo tuya.
              </span>
            </button>
            <button
              type="button"
              className="sheet-opcion"
              disabled={!!haciendo}
              onClick={() => hacer("siguiente")}
            >
              <span className="sheet-opcion-tit">
                {haciendo === "siguiente" ? "Guardando…" : "Que sea mi próxima carta"}
              </span>
              <span className="sheet-opcion-nota">
                En lugar de una carta al azar, la próxima que te llegue va a ser esta.
              </span>
            </button>

            <div className="actions-stack sheet-cerrar">
              <Button variant="tertiary" disabled={!!haciendo} onClick={() => setVerPausa(false)}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* —— Free: hacer la Pausa de otra persona es de quienes son parte —— */}
      {verPremium && (
        <SoloComunidad
          onClose={() => setVerPremium(false)}
        />
      )}

      {/* —— Reenviar: a mi comunidad, o el link in-app por WhatsApp —— */}
      <ReenviarSheet
        entregaId={ficha.id}
        abierto={verReenviar}
        onClose={() => setVerReenviar(false)}
        linkWhatsApp={`${window.location.origin}/comunidad/ficha/${ficha.id}`}
      />
    </div>
  );
}

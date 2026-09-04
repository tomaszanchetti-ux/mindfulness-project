// Compartir (§12.5). El gesto íntimo: "Vi esto y pensé en ti."
//
// WS25 · se acabó el selector de modo: viaja la ficha ENTERA tal como está al
// momento de enviar (la carta y, si existen, la reflexión y las fotos). El
// backend deriva el modo y ya no mira el plan — free y premium envían igual.
// Lo único que el remitente elige es la nota que acompaña al regalo.
//
// Por eso la pantalla muestra primero una vista previa de lo que viaja: nadie
// envía a ciegas. Las estrellas NO viajan (decisión de Tomás, 04/09).
//
// Camino "Enviar" (sin guardar): la Pausa quedó cerrada con `completada:false`,
// así que no está en el Baúl. Tras generar el enlace se invita a guardarla.

import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { FotoPrivada } from "../components/FotoPrivada";
import { api } from "../lib/api";
import { useStore } from "../store";
import type { Compartido, ItemBaul } from "../lib/types";

export function Share() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { perfil } = useStore();
  const [item, setItem] = useState<ItemBaul | null | undefined>(undefined);
  const [nota, setNota] = useState("");
  const [link, setLink] = useState<Compartido | null>(null);
  const [copiado, setCopiado] = useState(false);
  const [generando, setGenerando] = useState(false);
  const [guardando, setGuardando] = useState(false);

  // Fotos de una Pausa que todavía NO está en el Baúl: no hay endpoint que las
  // liste, así que Reflect nos las pasa por el estado de navegación al enviar.
  const fotosEnVuelo = (location.state as { fotos?: string[] } | null)?.fotos;

  useEffect(() => {
    // El Baúl solo lista Pausas guardadas; si venimos del camino "Enviar" la
    // entrega de hoy no está ahí → fallback a la carta del día (que ya trae la
    // reflexión persistida por el cierre con `completada:false`).
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
          setItem({
            ...d.entrega,
            fotos: fotosEnVuelo ?? [],
            carta: d.carta,
            visibilidad: "privada",
          });
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
      const notaLimpia = nota.trim();
      const c = await api.compartir(id, notaLimpia || undefined);
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

  // Guardar la Pausa después de haberla enviado (camino "Enviar"). Es el mismo
  // cierre de siempre, con `completada:true`: no pisa nada de lo escrito.
  const guardarPausa = async () => {
    setGuardando(true);
    try {
      await api.cerrarRitual(id, { completada: true });
      navigate(`/cierre/${id}`, { replace: true });
    } catch (e) {
      setGuardando(false);
      alert((e as Error).message);
    }
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

  const limites = perfil?.limites ?? null;
  const notaMax = limites?.reflexion_max ?? 0;
  const near = notaMax > 0 && nota.length > notaMax - 30;
  // Si la Pausa de hoy aún no se guardó, el siguiente paso es ofrecerle el Baúl.
  const pendienteGuardar = item ? !item.completada : false;
  const reflexion = item?.reflexion?.trim() || "";
  const fotos = item?.fotos ?? [];

  // Sin perfil todavía no sabemos los límites del plan: esperamos.
  if (!limites) return <div className="center-note">Preparando…</div>;

  return (
    <div>
      <button className="back-link" onClick={() => navigate(-1)}>← Volver</button>

      <div className="screen-head share-head">
        <h1 className="screen-title">Vi esto y pensé en ti.</h1>
      </div>

      {/* Lo que viaja, tal cual: la carta y —si existen— la reflexión y las fotos. */}
      {item && (
        <div className="share-preview">
          <p className="share-preview-label">Así la va a recibir</p>
          <div className="share-preview-card">
            <Card carta={item.carta} flipped />
          </div>
          {reflexion && <p className="share-preview-refl">{reflexion}</p>}
          {fotos.length > 0 && (
            <div className="share-preview-fotos">
              {fotos.map((src) => (
                <FotoPrivada key={src} className="share-preview-foto" src={src} />
              ))}
            </div>
          )}
        </div>
      )}

      {!link ? (
        <>
          <textarea
            className="textarea"
            placeholder="Agrega una nota personal (opcional)…"
            maxLength={notaMax}
            value={nota}
            onChange={(e) => setNota(e.target.value)}
            style={{ minHeight: 92 }}
          />
          <div className={`counter ${near ? "near" : ""}`}>
            {nota.length} / {notaMax}
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

          {pendienteGuardar ? (
            <div className="share-guardar">
              <p className="share-guardar-pregunta">¿Quieres guardar la Pausa?</p>
              <p className="share-guardar-nota">
                Lo que ya enviaste no cambia. Guardarla la deja en tu Baúl, para
                volver cuando quieras.
              </p>
              <div className="actions-stack">
                <Button variant="primary" full disabled={guardando} onClick={guardarPausa}>
                  {guardando ? "Guardando…" : "Guardar en mi Baúl"}
                </Button>
                <Button
                  variant="secondary"
                  full
                  onClick={() => navigate(`${link.url}?preview=1`)}
                >
                  Ver cómo lo recibe
                </Button>
                <Button variant="tertiary" onClick={() => navigate("/hoy")}>
                  Ahora no
                </Button>
              </div>
            </div>
          ) : (
            <div className="actions-stack">
              <Button variant="primary" full onClick={() => navigate(`${link.url}?preview=1`)}>
                Ver cómo lo recibe
              </Button>
              <Button variant="tertiary" onClick={() => navigate("/hoy")}>
                Listo
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

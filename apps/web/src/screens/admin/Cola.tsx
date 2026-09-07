// WS28 · B2.2b · Bloque 1 · La cola de aprobación.
//
// Cada carta propuesta se lee entera antes de decidir: el FUNNEL en tres
// columnas cuenta de dónde viene (v1: lo que escribió el autor, vuelta por
// vuelta), qué dijo el juez (v2) y qué se hace con ella (vFinal). En un teléfono
// las tres columnas se apilan en ese mismo orden, que es el orden del relato.
//
// Ninguna decisión usa `confirm()` del navegador: aprobar es CARGAR al mazo, así
// que la pregunta vive en la pantalla, con el papel de la app.

import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { api } from "../../lib/api";
import { fechaCorta, fechaRelativa } from "../../lib/format";
import { FRASE_MAX, PROMPT_MAX, PROMPT_MIN, rotulo } from "../../lib/propuestas";
import type {
  Carta,
  CategoriaContenido,
  FiltroAdmin,
  Hallazgo,
  PropuestaAdmin,
  Redaccion,
  SugerenciaCarta,
} from "../../lib/types";
import { useStore } from "../../store";
import {
  Mini,
  accionDe,
  es403,
  firmaTexto,
  legible,
  mensaje,
  pilarDe,
  porTexto,
} from "./comun";

const FILTROS: { id: FiltroAdmin; label: string }[] = [
  { id: "pendientes", label: "Pendientes" },
  { id: "a_revisar", label: "Con retoque" },
  { id: "aprobada", label: "Cargadas" },
  { id: "rechazada", label: "No aprobadas" },
];

const VACIOS: Record<FiltroAdmin, string> = {
  pendientes: "No hay cartas esperando.",
  a_revisar: "No hay cartas devueltas con un retoque.",
  aprobada: "Todavía no cargaste ninguna carta de la comunidad.",
  rechazada: "No hay cartas sin aprobar.",
};

// Los dos estados desde los que todavía se puede decidir (el backend acepta
// aprobar y pedir retoque solo desde acá; rechazar además desde `a_revisar`,
// pero esa carta ya está con su autor y no se le vuelve a poner mano encima).
function sePuedeDecidir(estado: string): boolean {
  return estado === "revision_dwellia" || estado === "en_revision";
}

export function Cola({ onCerrado }: { onCerrado: () => void }) {
  const { categorias } = useStore();
  const [filtro, setFiltro] = useState<FiltroAdmin>("pendientes");
  const [items, setItems] = useState<PropuestaAdmin[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [abierta, setAbierta] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [enGrande, setEnGrande] = useState<Carta | null>(null);
  const [flipped, setFlipped] = useState(true);

  const cargar = useCallback(
    async (f: FiltroAdmin) => {
      setItems(null);
      setError(null);
      try {
        setItems(await api.adminCartas(f));
      } catch (e) {
        if (es403(e)) {
          onCerrado();
          return;
        }
        setItems([]);
        setError(mensaje(e));
      }
    },
    [onCerrado],
  );

  useEffect(() => {
    void cargar(filtro);
  }, [cargar, filtro]);

  // El aviso de éxito se va solo: es una confirmación, no un cartel.
  useEffect(() => {
    if (!aviso) return;
    const t = window.setTimeout(() => setAviso(null), 6000);
    return () => window.clearTimeout(t);
  }, [aviso]);

  const trasDecidir = async (texto: string) => {
    setAbierta(null);
    setAviso(texto);
    await cargar(filtro);
  };

  return (
    <section>
      <div className="adm-toolbar">
        <span className="adm-tool-label">Mostrar</span>
        <div className="chips-scroll" role="radiogroup" aria-label="Mostrar">
          {FILTROS.map((f) => (
            <button
              key={f.id}
              type="button"
              role="radio"
              aria-checked={filtro === f.id}
              className={`chip chip-sm ${filtro === f.id ? "chip-active" : ""}`}
              onClick={() => {
                setAbierta(null);
                setFiltro(f.id);
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
        {items !== null && (
          <span className="adm-conteo">
            {items.length === 1 ? "1 carta" : `${items.length} cartas`}
          </span>
        )}
      </div>

      {aviso && <p className="adm-aviso">{aviso}</p>}
      {error && <p className="adm-error">{error}</p>}

      {items === null && <div className="center-note">…</div>}

      {items !== null && items.length === 0 && !error && (
        <div className="empty">
          <p className="empty-title">{VACIOS[filtro]}</p>
          <p className="empty-body">Prueba con otro filtro.</p>
        </div>
      )}

      {(items || []).map((p) => (
        <Item
          key={p.id}
          p={p}
          categorias={categorias}
          abierta={abierta === p.id}
          onToggle={() => setAbierta((cur) => (cur === p.id ? null : p.id))}
          onVerCarta={() => {
            setFlipped(true);
            setEnGrande(p.carta);
          }}
          onHecho={trasDecidir}
        />
      ))}

      {enGrande && enGrande.categoria && enGrande.accion && (
        <div className="lightbox" onClick={() => setEnGrande(null)}>
          <div className="lightbox-carta" onClick={(e) => e.stopPropagation()}>
            <Card
              carta={enGrande}
              flipped={flipped}
              onFlip={() => setFlipped((f) => !f)}
            />
          </div>
          <button className="lightbox-close" aria-label="Cerrar">
            ×
          </button>
        </div>
      )}
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Un ítem de la cola: colapsado es una línea de lectura; abierto, el funnel.
// ─────────────────────────────────────────────────────────────────────────────
function Item({
  p,
  categorias,
  abierta,
  onToggle,
  onVerCarta,
  onHecho,
}: {
  p: PropuestaAdmin;
  categorias: CategoriaContenido[];
  abierta: boolean;
  onToggle: () => void;
  onVerCarta: () => void;
  onHecho: (texto: string) => Promise<void>;
}) {
  const r = rotulo(p.estado);
  const pilar = pilarDe(p.carta);
  const accion = accionDe(p.carta);
  const autor =
    p.firma === "anonima" ? "anónimo" : p.autor.apodo || p.autor.nombre || "sin apodo";

  return (
    <article className={`adm-item ${abierta ? "is-open" : ""}`}>
      <div className="adm-item-head">
        <Mini carta={p.carta} onClick={onVerCarta} />
        <button
          type="button"
          className="adm-item-info"
          aria-expanded={abierta}
          onClick={onToggle}
        >
          {/* Spans y no <p>: esto vive dentro de un <button>. */}
          <span className="adm-item-frase">{p.carta.frase}</span>
          <span className="adm-item-meta">
            <span style={{ color: pilar.text }}>{pilar.nombre}</span>
            {accion && ` · ${accion}`}
          </span>
          <span className="adm-item-tags">
            <span className={`pill-estado es-${r.tono}`}>{r.texto}</span>
            <span className="adm-autor">{autor}</span>
            {p.firma !== "anonima" && p.autor.email && (
              <span className="adm-email">{p.autor.email}</span>
            )}
            <span className="adm-fecha">{fechaRelativa(p.created_at)}</span>
          </span>
        </button>
        <button
          type="button"
          className="adm-chevron"
          aria-label={abierta ? "Cerrar la carta" : "Abrir la carta"}
          onClick={onToggle}
        >
          ⌄
        </button>
      </div>

      {abierta && (
        <div className="adm-funnel">
          <ColumnaEscrita p={p} categorias={categorias} />
          <ColumnaJuez p={p} />
          <div className="adm-col">
            <h4 className="adm-col-t">
              <span className="adm-col-n">vFinal</span> Tu decisión
            </h4>
            {sePuedeDecidir(p.estado) ? (
              <Decision p={p} onHecho={onHecho} />
            ) : (
              <DecisionTomada p={p} />
            )}
          </div>
        </div>
      )}
    </article>
  );
}

// —— v1 · Lo que escribió ————————————————————————————————————————————————
function ColumnaEscrita({
  p,
  categorias,
}: {
  p: PropuestaAdmin;
  categorias: CategoriaContenido[];
}) {
  // Una propuesta anterior al historial no tiene vueltas guardadas: la carta que
  // se está mirando ES su v1, y así se dice (en vez de una columna vacía).
  const versiones: Redaccion[] =
    p.historial.length > 0
      ? [...p.historial].sort((a, b) => a.version - b.version)
      : [
          {
            version: 1,
            frase: p.carta.frase,
            prompt: p.carta.prompt,
            categoria: p.carta.categoria?.slug || "",
            accion: p.carta.accion?.slug || "",
            firma: p.firma,
            fecha: p.created_at,
            por: "usuario",
          },
        ];

  const nombrePilar = (slug: string) =>
    categorias.find((c) => c.slug === slug)?.nombre || legible(slug) || "sin pilar";

  return (
    <div className="adm-col">
      <h4 className="adm-col-t">
        <span className="adm-col-n">v1</span> Lo que escribió
      </h4>
      {versiones.map((v) => (
        <div className="adm-redaccion" key={`${v.version}-${v.fecha}`}>
          <p className="adm-redaccion-top">
            <span className="adm-redaccion-v">v{v.version}</span>
            <span>{fechaCorta(v.fecha)}</span>
            {porTexto(v.por) && <span>· {porTexto(v.por)}</span>}
          </p>
          <p className="adm-redaccion-frase">{v.frase}</p>
          <p className="adm-redaccion-prompt">{v.prompt}</p>
          <p className="adm-redaccion-meta">
            {nombrePilar(v.categoria)} · {legible(v.accion) || "sin acción"} ·{" "}
            {firmaTexto(v.firma)}
          </p>
        </div>
      ))}
    </div>
  );
}

// —— v2 · El juez ————————————————————————————————————————————————————————
const RESULTADOS: Record<string, string> = {
  aprueba: "El juez la aprueba",
  requiere_revision: "El juez pide un retoque",
  rechaza: "El juez la rechaza",
};

const FUENTES: Record<string, string> = {
  juez: "Lo escribió el juez.",
  dwellia: "Lo escribió Dwellia.",
};

function ColumnaJuez({ p }: { p: PropuestaAdmin }) {
  const vr = p.veredicto_resumen;
  const resultado = (vr?.resultado && RESULTADOS[vr.resultado]) || "Sin veredicto todavía";
  const brutos = p.veredicto?.hallazgos;
  const hallazgos: Hallazgo[] = Array.isArray(brutos) ? brutos : [];
  const cuantos = vr?.hallazgos ?? hallazgos.length;
  const fix = vr?.fix || p.veredicto?.fix_sugerido || null;
  const concepto = p.veredicto?.concepto || p.concepto;

  return (
    <div className="adm-col">
      <h4 className="adm-col-t">
        <span className="adm-col-n">v2</span> El juez
      </h4>

      <p className="adm-veredicto-res">{resultado}</p>
      {vr?.fuente && <p className="adm-nota">{FUENTES[vr.fuente] || legible(vr.fuente)}</p>}

      {vr?.motivo && (
        <>
          <span className="adm-lbl">Por qué</span>
          <p className="adm-txt">{vr.motivo}</p>
        </>
      )}

      <span className="adm-lbl">
        {cuantos === 0
          ? "Sin puntos marcados"
          : cuantos === 1
            ? "1 punto marcado"
            : `${cuantos} puntos marcados`}
      </span>
      {hallazgos.length > 0 && (
        <ul className="adm-hallazgos">
          {hallazgos.map((h, i) => (
            <li key={`${h.regla}-${i}`} className={`adm-hallazgo ${h.mayor ? "is-mayor" : ""}`}>
              <p className="adm-hallazgo-regla">
                <span>{h.regla || "sin regla"}</span>
                {h.mayor && <span className="adm-hallazgo-mayor">grave</span>}
              </p>
              <p className="adm-hallazgo-detalle">{h.detalle || "Sin detalle."}</p>
            </li>
          ))}
        </ul>
      )}

      {fix && (fix.frase || fix.prompt) && (
        <>
          <span className="adm-lbl">El retoque que propone</span>
          <div className="adm-fix">
            {fix.frase && (
              <p className="adm-redaccion-frase" style={{ marginBottom: fix.prompt ? 8 : 0 }}>
                {fix.frase}
              </p>
            )}
            {fix.prompt && <p className="adm-redaccion-prompt" style={{ margin: 0 }}>{fix.prompt}</p>}
          </div>
        </>
      )}

      {concepto && (
        <>
          <span className="adm-lbl">Concepto</span>
          <p className="adm-txt">{concepto}</p>
        </>
      )}
    </div>
  );
}

// —— vFinal · La decisión ya tomada ——————————————————————————————————————
function DecisionTomada({ p }: { p: PropuestaAdmin }) {
  const r = rotulo(p.estado);
  return (
    <div className="adm-decidida">
      <span className={`pill-estado es-${r.tono}`}>{r.texto}</span>
      {p.motivo && <p className="adm-txt">{p.motivo}</p>}
      {p.concepto && <p className="adm-nota">Concepto: {p.concepto}</p>}
      {p.carta_id && (
        <p className="adm-nota">Ya está en el mazo, con la referencia {p.carta_id}.</p>
      )}
      <p className="adm-nota">Última novedad: {fechaCorta(p.updated_at)}</p>
    </div>
  );
}

// —— vFinal · Las tres acciones ——————————————————————————————————————————
type Accion = "aprobar" | "rechazar" | "retoque";

const ACCIONES: { id: Accion; label: string }[] = [
  { id: "aprobar", label: "Aprobar" },
  { id: "rechazar", label: "No aprobar" },
  { id: "retoque", label: "Pedir un retoque" },
];

function Decision({
  p,
  onHecho,
}: {
  p: PropuestaAdmin;
  onHecho: (texto: string) => Promise<void>;
}) {
  const [accion, setAccion] = useState<Accion | null>(null);
  const [concepto, setConcepto] = useState(p.concepto || "");
  const [confirmar, setConfirmar] = useState(false);
  const [motivo, setMotivo] = useState("");
  const [sugerencia, setSugerencia] = useState("");
  const [fixFrase, setFixFrase] = useState("");
  const [fixPrompt, setFixPrompt] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const elegir = (id: Accion) => {
    setAccion((cur) => (cur === id ? null : id));
    setConfirmar(false);
    setError(null);
  };

  // Un solo camino para las tres: pedir, y si sale bien, avisar al padre (que
  // recarga la lista). Si falla, el mensaje del backend se muestra tal cual.
  const correr = async (llamada: () => Promise<unknown>, texto: string) => {
    setEnviando(true);
    setError(null);
    try {
      await llamada();
      await onHecho(texto);
    } catch (e) {
      setError(mensaje(e));
      setEnviando(false);
      setConfirmar(false);
    }
  };

  const frase = fixFrase.trim();
  const prompt = fixPrompt.trim();
  const promptMal = prompt.length > 0 && (prompt.length < PROMPT_MIN || prompt.length > PROMPT_MAX);
  const fix: SugerenciaCarta | null =
    frase || prompt ? { frase: frase || null, prompt: prompt || null } : null;

  return (
    <div>
      <div className="adm-decidir-chips" role="group" aria-label="Qué hacer con esta carta">
        {ACCIONES.map((a) => (
          <button
            key={a.id}
            type="button"
            aria-pressed={accion === a.id}
            className={`chip chip-sm ${accion === a.id ? "chip-active" : ""}`}
            onClick={() => elegir(a.id)}
          >
            {a.label}
          </button>
        ))}
      </div>

      {accion === null && (
        <p className="adm-nota" style={{ marginTop: 0 }}>
          Elige qué hacer con esta carta. Aprobarla la carga al mazo en el momento.
        </p>
      )}

      {accion === "aprobar" && (
        <div className="adm-forma">
          <div className="adm-campo">
            <label className="adm-campo-lbl" htmlFor={`concepto-${p.id}`}>
              Concepto (opcional)
            </label>
            <input
              id={`concepto-${p.id}`}
              className="adm-input"
              value={concepto}
              maxLength={80}
              placeholder="gratitud-cotidiana"
              onChange={(e) => setConcepto(e.target.value)}
            />
            <span className="adm-contador">
              Sirve para que el mazo no repita la misma idea en la semana.
            </span>
          </div>

          {confirmar ? (
            <div className="confirm-inline">
              <p className="confirm-inline-pregunta">¿Cargarla al mazo?</p>
              <p className="confirm-inline-nota">
                Desde este momento la carta puede tocarle a cualquiera, con la firma
                que eligió su autor.
              </p>
              <div className="actions-stack">
                <Button
                  full
                  disabled={enviando}
                  onClick={() =>
                    correr(
                      () => api.adminAprobar(p.id, concepto.trim() || undefined),
                      "Carta cargada al mazo. Su autor ya recibió el aviso.",
                    )
                  }
                >
                  {enviando ? "Cargando…" : "Sí, cargarla"}
                </Button>
                <Button variant="tertiary" disabled={enviando} onClick={() => setConfirmar(false)}>
                  Todavía no
                </Button>
              </div>
            </div>
          ) : (
            <div className="actions-stack">
              <Button full onClick={() => setConfirmar(true)}>
                Aprobar
              </Button>
            </div>
          )}
          {error && <p className="adm-error-inline">{error}</p>}
        </div>
      )}

      {accion === "rechazar" && (
        <div className="adm-forma">
          <div className="adm-campo">
            <label className="adm-campo-lbl" htmlFor={`motivo-${p.id}`}>
              Motivo para el autor
            </label>
            <textarea
              id={`motivo-${p.id}`}
              className="adm-textarea"
              value={motivo}
              placeholder="Lo que va a leer en su pantalla."
              onChange={(e) => setMotivo(e.target.value)}
            />
          </div>
          <div className="actions-stack">
            <Button
              full
              className="btn-danger"
              disabled={enviando || motivo.trim().length === 0}
              onClick={() =>
                correr(
                  () => api.adminRechazar(p.id, motivo.trim()),
                  "Carta no aprobada. Su autor ya recibió el motivo.",
                )
              }
            >
              {enviando ? "Enviando…" : "No aprobar"}
            </Button>
          </div>
          {error && <p className="adm-error-inline">{error}</p>}
        </div>
      )}

      {accion === "retoque" && (
        <div className="adm-forma">
          <div className="adm-campo">
            <label className="adm-campo-lbl" htmlFor={`sugerencia-${p.id}`}>
              Sugerencia para el autor
            </label>
            <textarea
              id={`sugerencia-${p.id}`}
              className="adm-textarea"
              value={sugerencia}
              placeholder="Qué tendría que cambiar para que entre."
              onChange={(e) => setSugerencia(e.target.value)}
            />
          </div>

          <div className="adm-campo">
            <label className="adm-campo-lbl" htmlFor={`fix-frase-${p.id}`}>
              Frase corregida (opcional)
            </label>
            <input
              id={`fix-frase-${p.id}`}
              className="adm-input"
              value={fixFrase}
              maxLength={FRASE_MAX}
              onChange={(e) => setFixFrase(e.target.value)}
            />
            <span className="adm-contador">
              {frase.length}/{FRASE_MAX}
            </span>
          </div>

          <div className="adm-campo">
            <label className="adm-campo-lbl" htmlFor={`fix-prompt-${p.id}`}>
              Pausa corregida (opcional)
            </label>
            <textarea
              id={`fix-prompt-${p.id}`}
              className="adm-textarea"
              value={fixPrompt}
              maxLength={PROMPT_MAX}
              onChange={(e) => setFixPrompt(e.target.value)}
            />
            <span className={`adm-contador ${promptMal ? "is-mal" : ""}`}>
              {prompt.length}/{PROMPT_MAX}
              {promptMal && ` · tiene que medir entre ${PROMPT_MIN} y ${PROMPT_MAX}`}
            </span>
          </div>

          <div className="actions-stack">
            <Button
              full
              disabled={enviando || sugerencia.trim().length === 0 || promptMal}
              onClick={() =>
                correr(
                  () => api.adminARevisar(p.id, sugerencia.trim(), fix),
                  "Carta devuelta con tu sugerencia. Su autor ya recibió el aviso.",
                )
              }
            >
              {enviando ? "Enviando…" : "Pedir un retoque"}
            </Button>
          </div>
          {error && <p className="adm-error-inline">{error}</p>}
        </div>
      )}
    </div>
  );
}

// WS27 · B2.2 · El wizard de una carta para la comunidad.
//
// Cuatro pasos, con la barra de puntos del onboarding: pilar → acción inicial →
// frase y prompt (con la carta dibujándose en vivo) → firma y cesión.
//
// El MISMO componente sirve para escribir una carta nueva (`/crear/nueva`,
// POST) y para corregir una que necesita un retoque (`/crear/:id/editar`, PUT).
// Con `?usar=sugerencia` el editor arranca precargado con el retoque propuesto;
// sin el parámetro, con lo que el autor había escrito. Los dos caminos son el
// mismo formulario: si el retoque se corrige a mano, se sigue corrigiendo ahí.
//
// La vista previa NO es un dibujo aparte: es `Card`, el único render de carta de
// la app, alimentado con una carta sintética. Lo que se ve es lo que va a ser.

import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { api, assetUrl } from "../lib/api";
import { FRASE_MAX, PROMPT_MAX, PROMPT_MIN } from "../lib/propuestas";
import { useStore } from "../store";
import type { AccionContenido, Carta, FirmaCarta } from "../lib/types";

const PASOS = 4;

export function CartaNueva() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [params] = useSearchParams();
  const { perfil, categorias } = useStore();
  const editando = !!id;

  const [acciones, setAcciones] = useState<AccionContenido[]>([]);
  const [paso, setPaso] = useState(1);
  const [categoria, setCategoria] = useState<string>("");
  const [accion, setAccion] = useState<string>("");
  const [frase, setFrase] = useState("");
  const [prompt, setPrompt] = useState("");
  const [firma, setFirma] = useState<FirmaCarta>("anonima");
  const [cesion, setCesion] = useState(false);
  const [flipped, setFlipped] = useState(true); // la previa arranca por el dorso
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // null = todavía cargando lo que hace falta para dibujar el paso 1.
  const [listo, setListo] = useState(false);

  const apodo = perfil?.apodo?.trim() || "";

  useEffect(() => {
    api.acciones().then(setAcciones).catch(() => setAcciones([]));
  }, []);

  // —— Modo edición: se lee la propuesta y se precarga el formulario ——
  // Solo `a_revisar` se puede reenviar (el backend responde 409 al resto): si no
  // es esa, se vuelve a Crear sin dejar al autor escribiendo algo que va a rebotar.
  useEffect(() => {
    if (!editando) {
      setListo(true);
      return;
    }
    let vivo = true;
    api
      .cartasMias()
      .then((cartas) => {
        if (!vivo) return;
        const p = cartas.find((c) => c.id === id);
        if (!p || p.estado !== "a_revisar") {
          navigate("/crear", { replace: true });
          return;
        }
        const usar = params.get("usar") === "sugerencia" && p.sugerencia;
        setCategoria(p.carta.categoria?.slug || "");
        setAccion(p.carta.accion?.slug || "");
        // El retoque puede traer solo uno de los dos campos: lo que no propone,
        // se conserva tal como lo escribió el autor.
        setFrase((usar && p.sugerencia?.frase) || p.carta.frase);
        setPrompt((usar && p.sugerencia?.prompt) || p.carta.prompt);
        setFirma(p.firma);
        setListo(true);
      })
      .catch((e) => {
        if (!vivo) return;
        setError((e as Error).message);
        setListo(true);
      });
    return () => {
      vivo = false;
    };
  }, [editando, id, params, navigate]);

  const cat = categorias.find((c) => c.slug === categoria) || null;
  const acc = acciones.find((a) => a.slug === accion) || null;

  // La carta sintética de la vista previa. Nunca viaja a la API: es lo que el
  // autor mira mientras escribe.
  const previa: Carta | null = useMemo(() => {
    if (!cat || !acc) return null;
    return {
      id: "previa",
      frase: frase || "Aquí va tu frase.",
      prompt: prompt || "Aquí va la Pausa que propones.",
      categoria: cat,
      accion: acc,
      origen: "comunidad",
      firma_publica: firma === "apodo" ? apodo || null : null,
    };
  }, [cat, acc, frase, prompt, firma, apodo]);

  const fraseOk = frase.trim().length > 0 && frase.trim().length <= FRASE_MAX;
  const promptLargo = prompt.trim().length;
  const promptOk = promptLargo >= PROMPT_MIN && promptLargo <= PROMPT_MAX;

  const puedeSeguir =
    (paso === 1 && !!categoria) ||
    (paso === 2 && !!accion) ||
    (paso === 3 && fraseOk && promptOk) ||
    (paso === 4 && (editando || cesion));

  const enviar = async () => {
    setEnviando(true);
    setError(null);
    const body = {
      categoria,
      accion,
      frase: frase.trim(),
      prompt: prompt.trim(),
      firma,
    };
    try {
      if (editando && id) await api.reenviarCarta(id, body);
      else await api.proponerCarta({ ...body, cesion_aceptada: true });
      navigate("/crear", { replace: true });
    } catch (e) {
      // El backend habla en español (422 del contenido, 403 free, 409 en curso):
      // se muestra tal cual, junto al botón que lo disparó.
      setError((e as Error).message);
      setEnviando(false);
    }
  };

  if (!listo) return <div className="center-note">…</div>;

  return (
    <div className="ob crear-wizard">
      <div className="ob-progress">
        {Array.from({ length: PASOS }).map((_, i) => (
          <div key={i} className={`ob-dot ${i < paso ? "on" : ""}`} />
        ))}
      </div>

      <div className="ob-body">
        {/* —— 1 · El pilar —————————————————————————————————————————— */}
        {paso === 1 && (
          <>
            <h2 className="ob-q">¿Sobre qué pilar quieres escribir?</h2>
            <p className="ob-hint">
              Cada carta vive en uno de los seis pilares de Dwellia.
            </p>
            <div className="pilar-grid">
              {categorias.map((c) => (
                <button
                  key={c.slug}
                  type="button"
                  className={`pilar-opt ${categoria === c.slug ? "on" : ""}`}
                  style={
                    categoria === c.slug
                      ? { borderColor: c.color_accent, boxShadow: `inset 0 0 0 1px ${c.color_accent}` }
                      : undefined
                  }
                  onClick={() => setCategoria(c.slug)}
                >
                  <span className="pilar-band" style={{ background: c.color_accent }} />
                  <img className="pilar-img" src={assetUrl(c.img)} alt="" />
                  <span className="pilar-nombre" style={{ color: c.color_text }}>
                    {c.nombre}
                  </span>
                </button>
              ))}
            </div>
          </>
        )}

        {/* —— 2 · La acción inicial ——————————————————————————————————— */}
        {paso === 2 && (
          <>
            <h2 className="ob-q">¿Con qué acción empieza la Pausa?</h2>
            <p className="ob-hint">
              El primer gesto, lejos del teléfono. Escribir en el diario es
              siempre el cierre, no el comienzo.
            </p>
            <div className="opt-list">
              {acciones.map((a) => (
                <button
                  key={a.slug}
                  type="button"
                  className={`opt accion-opt ${accion === a.slug ? "on" : ""}`}
                  onClick={() => setAccion(a.slug)}
                >
                  <span
                    className="accion-glifo"
                    style={{
                      background: cat?.color_accent || "var(--sage)",
                      WebkitMaskImage: `url(${assetUrl(a.glifo)})`,
                      maskImage: `url(${assetUrl(a.glifo)})`,
                    }}
                    aria-hidden
                  />
                  <span>{a.nombre}</span>
                </button>
              ))}
            </div>
          </>
        )}

        {/* —— 3 · Frase y prompt, con la carta dibujándose en vivo —————— */}
        {paso === 3 && (
          <>
            <h2 className="ob-q">Escribe tu carta</h2>
            {previa && (
              <div className="wizard-previa">
                <Card carta={previa} flipped={flipped} onFlip={() => setFlipped((f) => !f)} />
                <p className="wizard-previa-nota">
                  Toca la carta para ver el otro lado.
                </p>
              </div>
            )}

            <label className="ob-field-label" htmlFor="carta-frase">
              La frase · la puerta de la carta
            </label>
            <textarea
              id="carta-frase"
              className="textarea textarea-mini"
              maxLength={FRASE_MAX}
              placeholder="Una línea que se pueda llevar en el bolsillo."
              value={frase}
              onChange={(e) => setFrase(e.target.value)}
            />
            <p className={`counter ${frase.length > FRASE_MAX - 10 ? "near" : ""}`}>
              {frase.length}/{FRASE_MAX}
            </p>

            <label className="ob-field-label" htmlFor="carta-prompt">
              La Pausa · qué le propones a quien la reciba
            </label>
            <textarea
              id="carta-prompt"
              className="textarea"
              maxLength={PROMPT_MAX}
              placeholder="Qué hacer, dónde mirar, y el cierre: termina invitando a escribir en el diario."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
            <p className={`counter ${promptOk ? "" : "near"}`}>
              {promptLargo}/{PROMPT_MAX}
              {promptLargo < PROMPT_MIN ? ` · faltan ${PROMPT_MIN - promptLargo}` : ""}
            </p>
            <p className="helper">
              Entre {PROMPT_MIN} y {PROMPT_MAX} caracteres, y termina invitando a
              escribir en el diario.
            </p>
          </>
        )}

        {/* —— 4 · Firma y envío ——————————————————————————————————————— */}
        {paso === 4 && (
          <>
            <h2 className="ob-q">¿Cómo quieres firmarla?</h2>
            <p className="ob-hint">
              Es lo único tuyo que viaja con la carta. Puedes cambiarlo hasta que
              la envíes.
            </p>
            <div className="opt-list">
              <button
                type="button"
                className={`opt ${firma === "anonima" ? "on" : ""}`}
                onClick={() => setFirma("anonima")}
              >
                Anónima
                <span className="opt-nota">
                  En el dorso dirá “de alguien de la comunidad”.
                </span>
              </button>
              <button
                type="button"
                className={`opt ${firma === "apodo" ? "on" : ""}`}
                disabled={!apodo}
                onClick={() => apodo && setFirma("apodo")}
              >
                {apodo ? `Con mi apodo (${apodo})` : "Con mi apodo"}
                <span className="opt-nota">
                  {apodo
                    ? "En el dorso dirá tu apodo."
                    : "Todavía no tienes apodo: puedes ponerlo en tu Perfil y volver."}
                </span>
              </button>
            </div>

            {editando ? (
              <p className="helper" style={{ textAlign: "left" }}>
                Ya cediste esta carta cuando la enviaste la primera vez: no hace
                falta volver a hacerlo.
              </p>
            ) : (
              <label className="terms-row cesion-row">
                <input
                  type="checkbox"
                  checked={cesion}
                  onChange={(e) => setCesion(e.target.checked)}
                />
                <span>
                  Cedo esta carta a Dwellia para que forme parte del mazo de la
                  comunidad; puede ser retocada por el equipo y no lleva datos
                  míos salvo el apodo si lo elijo.
                </span>
              </label>
            )}
          </>
        )}
      </div>

      {error && <p className="crear-aviso">{error}</p>}

      <div className="ob-foot">
        {paso < PASOS ? (
          <Button variant="primary" full disabled={!puedeSeguir} onClick={() => setPaso(paso + 1)}>
            Continuar
          </Button>
        ) : (
          <Button variant="primary" full disabled={!puedeSeguir || enviando} onClick={enviar}>
            {enviando ? "Enviando…" : "Enviar a evaluación"}
          </Button>
        )}
        <Button
          variant="tertiary"
          disabled={enviando}
          onClick={() => (paso === 1 ? navigate("/crear") : setPaso(paso - 1))}
        >
          {paso === 1 ? "Cancelar" : "Atrás"}
        </Button>
      </div>
    </div>
  );
}

// Onboarding (M1). "Preparar un ritual", no configurar una app.
// Flujo canónico: Login → SLIDESHOW (qué es + compromiso) → CONFIGURACIÓN.
//   Intro (sin progreso):  0 Bienvenida (marca + slogan) · 1 Slideshow del ritual
//   Config (5 pasos):      2 Datos · 3 Categorías · 4 Actividades · 5 Momento · 6 Aviso + términos
// (El "Tono" del doc UX fue eliminado del onboarding por canon M1.)
// WS10: el fin es escribir en tu diario; las actividades se ELIGEN ("escribir" siempre).

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { StoryArt } from "../components/StoryArt";
import type { Escena } from "../components/StoryArt";
import { api } from "../lib/api";
import { useStore } from "../store";

// El ritual contado paso a paso: carrusel de 7 pantallas (QA 10/06, reemplaza la
// lista de viñetas). Se puede deslizar o avanzar con el botón.
const SLIDES: {
  escena: Escena;
  kicker?: string;
  titulo: string;
  cuerpo: string;
  tip?: string;
}[] = [
  {
    escena: "amanecer",
    titulo: "Una pausa al día.",
    cuerpo:
      "Dwellia es un espacio para conectar contigo: al menos 15 minutos al día, lejos de las distracciones.",
    tip: "Te recomendamos tener un diario personal físico y entre 15 y 30 minutos disponibles cada día.",
  },
  {
    escena: "recibe",
    kicker: "Paso 1",
    titulo: "Recibe tu carta",
    cuerpo: "Cada día, Dwellia te envía una carta con una pausa para realizar.",
  },
  {
    escena: "pausa",
    kicker: "Paso 2",
    titulo: "Vive tu pausa",
    cuerpo: "Lejos del móvil y a tu manera. Ese momento es solo tuyo.",
  },
  {
    escena: "diario",
    kicker: "Paso 3",
    titulo: "Escribe lo que sentiste",
    cuerpo:
      "Al terminar, escribe en tu diario personal lo que la pausa despertó en ti.",
  },
  {
    escena: "guarda",
    kicker: "Paso 4",
    titulo: "Guárdala en tu Baúl",
    cuerpo:
      "Vuelve a Dwellia para guardar la experiencia en tu Baúl de crecimiento personal.",
  },
  {
    escena: "comparte",
    kicker: "Paso 5",
    titulo: "Compártela si quieres",
    cuerpo: "Regala tu experiencia a tus seres queridos.",
  },
  {
    escena: "amanecer",
    titulo: "¿Comenzamos?",
    cuerpo: "Sin feed ni likes. Solo una pausa al día.",
  },
];

const ACCION_PISO = "escribir"; // siempre incluida y bloqueada (WS10)

const MOMENTOS: { key: string; label: string; hora: string }[] = [
  { key: "manana", label: "A la mañana", hora: "08:00" },
  { key: "mediodia", label: "Al mediodía", hora: "13:00" },
  { key: "tarde", label: "A la tarde", hora: "18:00" },
  { key: "noche", label: "A la noche", hora: "21:00" },
];

// Los 5 pasos de configuración (los que muestran progreso).
const CONFIG_STEPS = 5;
const PRIMER_CONFIG = 2;

export function Onboarding() {
  const navigate = useNavigate();
  const { categorias, acciones, refrescarPerfil } = useStore();
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Madrid";

  const [step, setStep] = useState(0);
  const [slide, setSlide] = useState(0);
  const slidesRef = useRef<HTMLDivElement>(null);
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");
  const [apodo, setApodo] = useState("");
  const [apodoEdited, setApodoEdited] = useState(false);
  const [sel, setSel] = useState<string[]>([]);
  const [selAct, setSelAct] = useState<string[]>([]);
  const [actInit, setActInit] = useState(false);
  const [momento, setMomento] = useState<string>("manana");
  const [horaCustom, setHoraCustom] = useState<string>("");
  const [aviso, setAviso] = useState(true);
  const [terminos, setTerminos] = useState(false);
  const [guardando, setGuardando] = useState(false);

  // Por defecto: solo "Escribir" seleccionada (el piso). El usuario suma las que quiera.
  useEffect(() => {
    if (!actInit && acciones.length > 0) {
      setSelAct([ACCION_PISO]);
      setActInit(true);
    }
  }, [acciones, actInit]);

  const toggleCat = (slug: string) => {
    setSel((cur) => {
      if (cur.includes(slug)) return cur.filter((c) => c !== slug);
      if (cur.length >= 6) return cur;
      return [...cur, slug];
    });
  };

  const toggleAct = (slug: string) => {
    if (slug === ACCION_PISO) return; // "escribir" no se puede sacar
    setSelAct((cur) =>
      cur.includes(slug) ? cur.filter((a) => a !== slug) : [...cur, slug],
    );
  };

  const horaElegida = () =>
    momento === "custom"
      ? horaCustom || "08:00"
      : MOMENTOS.find((m) => m.key === momento)?.hora || "08:00";

  const finalizar = async () => {
    setGuardando(true);
    try {
      await api.setCategorias(sel);
      // "escribir" siempre entra (el backend la fuerza igual); mando lo elegido.
      await api.setAcciones(
        selAct.includes(ACCION_PISO) ? selAct : [...selAct, ACCION_PISO],
      );
      await api.setPerfil({
        nombre: nombre.trim(),
        apellido: apellido.trim(),
        apodo: apodo.trim() || nombre.trim(),
        tz,
        hora_aviso: horaElegida(),
        aviso_activo: aviso,
        aceptar_terminos: true,
      });
      await refrescarPerfil();
      // WS14: directo a la carta real del día; los nudges de la Home hacen el resto.
      navigate("/hoy", { replace: true });
    } catch (e) {
      setGuardando(false);
      alert((e as Error).message);
    }
  };

  const mostrarProgreso = step >= PRIMER_CONFIG;

  // —— Slideshow (paso 1): swipe nativo con scroll-snap + botón que avanza. ——
  const onSlidesScroll = () => {
    const el = slidesRef.current;
    if (!el) return;
    setSlide(Math.round(el.scrollLeft / el.clientWidth));
  };

  const irASlide = (i: number) => {
    const el = slidesRef.current;
    if (!el) return;
    el.scrollTo({ left: i * el.clientWidth, behavior: "smooth" });
  };

  const avanzarSlide = () => {
    if (slide >= SLIDES.length - 1) {
      setStep(2);
      return;
    }
    irASlide(slide + 1);
  };

  return (
    <div className="ob">
      {mostrarProgreso && (
        <div className="ob-progress">
          {Array.from({ length: CONFIG_STEPS }).map((_, i) => (
            <div key={i} className={`ob-dot ${i <= step - PRIMER_CONFIG ? "on" : ""}`} />
          ))}
        </div>
      )}

      {/* —— 0 · Bienvenida (marca + slogan) —— */}
      {step === 0 && (
        <div className="ob-welcome">
          <h1 className="ob-brand">Dwellia</h1>
          <p className="ob-slogan">One quiet pause a day</p>
          <div className="ob-welcome-foot">
            <Button variant="primary" full onClick={() => setStep(1)}>
              Comenzar
            </Button>
          </div>
        </div>
      )}

      {/* —— 1 · El ritual contado paso a paso (slideshow deslizable) —— */}
      {step === 1 && (
        <>
          <div className="ob-slides" ref={slidesRef} onScroll={onSlidesScroll}>
            {SLIDES.map((s, i) => (
              <section className="ob-slide" key={i}>
                <div className="ob-slide-art">
                  <StoryArt escena={s.escena} />
                </div>
                {s.kicker && <p className="ob-slide-kicker">{s.kicker}</p>}
                <h2 className="ob-slide-title">{s.titulo}</h2>
                <p className="ob-slide-body">{s.cuerpo}</p>
                {s.tip && <p className="ob-slide-tip">{s.tip}</p>}
              </section>
            ))}
          </div>
          <div className="ob-slides-dots">
            {SLIDES.map((_, i) => (
              <button
                key={i}
                className={`ob-sdot ${i === slide ? "on" : ""}`}
                aria-label={`Pantalla ${i + 1}`}
                onClick={() => irASlide(i)}
              />
            ))}
          </div>
          <div className="ob-foot">
            <Button variant="primary" full onClick={avanzarSlide}>
              {slide >= SLIDES.length - 1 ? "Sí, comencemos" : "Siguiente"}
            </Button>
          </div>
        </>
      )}

      {/* —— 2 · Datos —— */}
      {step === 2 && (
        <>
          <div className="ob-body">
            <h2 className="ob-q">¿Cómo te llamas?</h2>
            <p className="ob-hint">Así es como te vamos a llamar dentro de la app.</p>

            <div className="ob-fields">
              <div>
                <label className="ob-field-label">Nombre</label>
                <input
                  className="time-input"
                  type="text"
                  maxLength={80}
                  placeholder="Tu nombre"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                />
              </div>
              <div>
                <label className="ob-field-label">Apellido (opcional)</label>
                <input
                  className="time-input"
                  type="text"
                  maxLength={80}
                  placeholder="Tu apellido"
                  value={apellido}
                  onChange={(e) => setApellido(e.target.value)}
                />
              </div>
              <div>
                <label className="ob-field-label">Apodo · cómo te llamamos</label>
                <input
                  className="time-input"
                  type="text"
                  maxLength={40}
                  placeholder="Cómo quieres que te llamemos"
                  value={apodoEdited ? apodo : nombre}
                  onChange={(e) => {
                    setApodoEdited(true);
                    setApodo(e.target.value);
                  }}
                />
              </div>
            </div>
          </div>
          <div className="ob-foot">
            <Button variant="primary" full disabled={!nombre.trim()} onClick={() => setStep(3)}>
              Continuar
            </Button>
          </div>
        </>
      )}

      {/* —— 3 · Categorías —— */}
      {step === 3 && (
        <>
          <div className="ob-body">
            <h2 className="ob-q">¿Qué quieres cultivar estos días?</h2>
            <p className="ob-hint">Elige entre 2 y 6. Puedes cambiarlo cuando quieras.</p>
            <div className="cat-grid">
              {categorias.map((c) => (
                <button
                  key={c.slug}
                  className={`cat-opt ${sel.includes(c.slug) ? "on" : ""}`}
                  onClick={() => toggleCat(c.slug)}
                >
                  <span className="swatch" style={{ background: c.color_accent }} />
                  {c.nombre}
                </button>
              ))}
            </div>
          </div>
          <div className="ob-foot">
            <Button variant="primary" full disabled={sel.length < 2} onClick={() => setStep(4)}>
              {sel.length < 2 ? "Elige al menos 2" : "Continuar"}
            </Button>
          </div>
        </>
      )}

      {/* —— 4 · Actividades (WS10) —— */}
      {step === 4 && (
        <>
          <div className="ob-body">
            <h2 className="ob-q">¿Cómo te gusta hacer tu pausa?</h2>
            <p className="ob-hint">
              Cada pausa es una excusa para detenerte, sentir y escribir lo que
              despierta en ti.
            </p>
            <div className="cat-grid">
              {acciones.map((a) => {
                const piso = a.slug === ACCION_PISO;
                return (
                  <button
                    key={a.slug}
                    className={`cat-opt ${selAct.includes(a.slug) ? "on" : ""} ${piso ? "locked" : ""}`}
                    onClick={() => toggleAct(a.slug)}
                    disabled={piso}
                  >
                    {a.nombre}
                  </button>
                );
              })}
            </div>
          </div>
          <div className="ob-foot">
            <Button variant="primary" full onClick={() => setStep(5)}>
              Continuar
            </Button>
          </div>
        </>
      )}

      {/* —— 5 · Momento —— */}
      {step === 5 && (
        <>
          <div className="ob-body">
            <h2 className="ob-q">¿Cuándo quieres recibir tu pausa?</h2>
            <p className="ob-hint">Es el horario en que te llegará la carta del día.</p>
            <div className="opt-list">
              {MOMENTOS.map((m) => (
                <button
                  key={m.key}
                  className={`opt ${momento === m.key ? "on" : ""}`}
                  onClick={() => setMomento(m.key)}
                >
                  {m.label} · {m.hora}
                </button>
              ))}
              <button
                className={`opt ${momento === "custom" ? "on" : ""}`}
                onClick={() => setMomento("custom")}
              >
                Elegir un horario
              </button>
              {momento === "custom" && (
                <input
                  type="time"
                  className="time-input"
                  value={horaCustom}
                  onChange={(e) => setHoraCustom(e.target.value)}
                />
              )}
            </div>
          </div>
          <div className="ob-foot">
            <Button variant="primary" full onClick={() => setStep(6)}>
              Continuar
            </Button>
          </div>
        </>
      )}

      {/* —— 6 · Aviso + términos —— */}
      {step === 6 && (
        <>
          <div className="ob-body">
            <h2 className="ob-q">¿Quieres que te avisemos?</h2>
            <p className="ob-hint">
              Puedes entrar por tu cuenta cuando quieras. Si prefieres, te avisamos a la
              hora que elegiste.
            </p>
            <label className="toggle-row">
              <span>Avisarme cada día</span>
              <span className="switch">
                <input
                  type="checkbox"
                  checked={aviso}
                  onChange={(e) => setAviso(e.target.checked)}
                />
                <span className="slider" />
              </span>
            </label>

            <label className="terms-row">
              <input
                type="checkbox"
                checked={terminos}
                onChange={(e) => setTerminos(e.target.checked)}
              />
              <span>
                Acepto los términos y entiendo que lo que escribo es privado salvo que
                elija compartirlo.
              </span>
            </label>
          </div>
          <div className="ob-foot">
            <Button variant="primary" full disabled={!terminos || guardando} onClick={finalizar}>
              {guardando ? "Preparando…" : "Crear mi ritual"}
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

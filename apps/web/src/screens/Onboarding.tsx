// Onboarding (M1). "Preparar un ritual", no configurar una app.
// Flujo canónico (storytelling WS22): Login → SLIDESHOW → CONFIGURACIÓN.
//   Intro (sin progreso):  0 Bienvenida (marca + slogan) · 1 Slideshow storytelling
//     (una pausa al día · los anillos · la pausa de dos tiempos · pasos 1-5 · ¿comenzamos?)
//   Config (3 pasos):      2 Datos · 3 Momento · 4 Aviso + términos
// Ni los pilares ni las acciones se eligen (WS17/WS22): el motor cura. La teoría
// vive en "El método Dwellia" (Perfil) — se avisa en el cierre, nunca se obliga.

import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { AnillosCirculo, PausaDosTiempos } from "../components/CirculosStory";
import { activarPush, soportaPush } from "../lib/push";
import { StoryArt } from "../components/StoryArt";
import type { Escena } from "../components/StoryArt";
import { api } from "../lib/api";
import { useStore } from "../store";

// El storytelling contado pantalla a pantalla (carrusel deslizable, WS22):
// qué es Dwellia → los anillos → la pausa de dos tiempos → los 5 pasos → comenzar.
const SLIDES: {
  escena?: Escena;
  viz?: "anillos" | "pausa";
  kicker?: string;
  titulo: string;
  cuerpo: string;
  tip?: string;
}[] = [
  {
    escena: "amanecer",
    titulo: "Una pausa al día.",
    cuerpo:
      "Dwellia es un espacio de crecimiento personal: una pausa diaria para conectar contigo, con tu alrededor y con la naturaleza — lejos de las distracciones.",
    tip: "Para aprovecharla al máximo: ten un diario personal físico y reserva entre 15 y 30 minutos cada día.",
  },
  {
    viz: "anillos",
    titulo: "Seis pilares, tres círculos",
    cuerpo:
      "El crecimiento se cultiva en seis pilares que te rodean en tres círculos: hacia adentro, hacia tu experiencia y hacia los demás. Cada semana los recorres todos — uno por día, más un día sorpresa.",
  },
  {
    viz: "pausa",
    titulo: "La pausa de dos tiempos",
    cuerpo:
      "Cada carta te propone una acción sencilla —contemplar, respirar, pasear, hacer— que te lleva a la calma. Y desde la calma, escribes en tu diario lo que sentiste.",
    tip: "Como el agua: cuando se aquieta, se ve el fondo.",
  },
  {
    // Divisoria (QA Tomás WS18): cierra el "qué es" y abre el "cómo funciona".
    escena: "amanecer",
    titulo: "¿Cómo funciona?",
    cuerpo: "Así es Dwellia en tu día a día — cinco pasos, una pausa.",
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
    cuerpo: "Lejos del móvil y a tu manera. Deja que la acción te lleve a la calma.",
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
    tip: "El porqué de todo esto vive en El método Dwellia, dentro de tu Perfil. Léelo cuando quieras.",
  },
];

const MOMENTOS: { key: string; label: string; hora: string }[] = [
  { key: "manana", label: "A la mañana", hora: "08:00" },
  { key: "mediodia", label: "Al mediodía", hora: "13:00" },
  { key: "tarde", label: "A la tarde", hora: "18:00" },
  { key: "noche", label: "A la noche", hora: "21:00" },
];

// Los 3 pasos de configuración (los que muestran progreso) — WS22: las acciones
// ya no se eligen, así que el paso de actividades desapareció.
const CONFIG_STEPS = 3;
const PRIMER_CONFIG = 2;

// Los puntitos del slideshow solo viven durante los pasos del ritual.
const PRIMER_PASO = SLIDES.findIndex((s) => s.kicker);
const PASOS = SLIDES.filter((s) => s.kicker).length;

export function Onboarding() {
  const navigate = useNavigate();
  const { categorias, refrescarPerfil } = useStore();
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Madrid";

  const [step, setStep] = useState(0);
  const [slide, setSlide] = useState(0);
  const slidesRef = useRef<HTMLDivElement>(null);
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");
  const [apodo, setApodo] = useState("");
  const [apodoEdited, setApodoEdited] = useState(false);
  const [momento, setMomento] = useState<string>("manana");
  const [horaCustom, setHoraCustom] = useState<string>("");
  const [aviso, setAviso] = useState(true);
  const [terminos, setTerminos] = useState(false);
  const [guardando, setGuardando] = useState(false);

  const horaElegida = () =>
    momento === "custom"
      ? horaCustom || "08:00"
      : MOMENTOS.find((m) => m.key === momento)?.hora || "08:00";

  const finalizar = async () => {
    setGuardando(true);
    // El aviso llega por notificación (WS21): pedimos el permiso DENTRO del mismo
    // toque (los navegadores lo exigen). Si no se puede acá (ej. iPhone sin
    // instalar), el Perfil ofrece activarlo después — no bloquea el onboarding.
    if (aviso && soportaPush()) {
      activarPush().catch(() => {});
    }
    try {
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
                {s.viz ? (
                  <div className="ob-slide-viz">
                    {s.viz === "anillos" ? (
                      <AnillosCirculo pilares={categorias} />
                    ) : (
                      <PausaDosTiempos />
                    )}
                  </div>
                ) : (
                  <div className="ob-slide-art">
                    <StoryArt escena={s.escena!} />
                  </div>
                )}
                {s.kicker && <p className="ob-slide-kicker">{s.kicker}</p>}
                <h2 className="ob-slide-title">{s.titulo}</h2>
                <p className="ob-slide-body">{s.cuerpo}</p>
                {s.tip && <p className="ob-slide-tip">{s.tip}</p>}
              </section>
            ))}
          </div>
          {/* Puntitos SOLO durante los pasos 1-5 (QA Tomás WS18): diez puntos
              gritaban "esto es largo"; acá funcionan como "paso X de 5". El
              contenedor queda siempre (min-height) para que nada salte. */}
          <div className="ob-slides-dots" style={{ minHeight: 8 }}>
            {slide >= PRIMER_PASO &&
              slide < PRIMER_PASO + PASOS &&
              Array.from({ length: PASOS }).map((_, i) => (
                <button
                  key={i}
                  className={`ob-sdot ${PRIMER_PASO + i === slide ? "on" : ""}`}
                  aria-label={`Paso ${i + 1}`}
                  onClick={() => irASlide(PRIMER_PASO + i)}
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

      {/* —— 3 · Momento —— */}
      {step === 3 && (
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
            <Button variant="primary" full onClick={() => setStep(4)}>
              Continuar
            </Button>
          </div>
        </>
      )}

      {/* —— 4 · Aviso + términos —— */}
      {step === 4 && (
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
            {aviso && (
              <p className="ob-hint" style={{ marginTop: 8 }}>
                {soportaPush()
                  ? "Te pediremos permiso para enviarte la notificación."
                  : "En iPhone, el aviso llega con Dwellia instalada en tu pantalla de inicio — en tu Perfil te mostramos cómo."}
              </p>
            )}

            <label className="terms-row">
              <input
                type="checkbox"
                checked={terminos}
                onChange={(e) => setTerminos(e.target.checked)}
              />
              <span>
                Acepto los{" "}
                <a href="/terminos" target="_blank" rel="noreferrer" className="terms-link">
                  términos y la política de privacidad
                </a>
                , y entiendo que lo que escribo es privado salvo que elija compartirlo.
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

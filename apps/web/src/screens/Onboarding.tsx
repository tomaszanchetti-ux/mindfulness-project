// Onboarding (M1). "Preparar un ritual", no configurar una app.
// Flujo canónico: Login → SLIDESHOW (qué es + compromiso) → CONFIGURACIÓN.
//   Intro (sin progreso):  0 Bienvenida (marca + slogan) · 1 Qué es + compromiso
//   Config (5 pasos):      2 Datos · 3 Categorías · 4 Actividades · 5 Momento · 6 Aviso + términos
// (El "Tono" del doc UX fue eliminado del onboarding por canon M1.)
// WS10: el fin es escribir en tu diario; las actividades se ELIGEN ("escribir" siempre).

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { api } from "../lib/api";
import { useStore } from "../store";

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

  // Por defecto: todas las actividades seleccionadas (lo más permisivo).
  useEffect(() => {
    if (!actInit && acciones.length > 0) {
      setSelAct(acciones.map((a) => a.slug));
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
      navigate("/hoy", { replace: true });
    } catch (e) {
      setGuardando(false);
      alert((e as Error).message);
    }
  };

  const mostrarProgreso = step >= PRIMER_CONFIG;

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

      {/* —— 1 · Qué es + compromiso (suave, con aire) —— */}
      {step === 1 && (
        <>
          <div className="ob-explain">
            <p className="ob-explain-lead">Una pausa al día.</p>
            <ol className="ob-steps">
              <li>
                <span className="ob-step-n">1</span>
                <span>Recibe una carta</span>
              </li>
              <li>
                <span className="ob-step-n">2</span>
                <span>Realiza la actividad</span>
              </li>
              <li>
                <span className="ob-step-n">3</span>
                <span>Escribe lo que sentiste</span>
              </li>
            </ol>
            <p className="ob-explain-accent">Sin feed ni likes.</p>
            <p className="ob-explain-tip">
              Recomendamos tener un diario físico y 15 minutos de calma al día.
            </p>
          </div>
          <div className="ob-foot">
            <Button variant="primary" full onClick={() => setStep(2)}>
              Continuar
            </Button>
          </div>
        </>
      )}

      {/* —— 2 · Datos —— */}
      {step === 2 && (
        <>
          <div className="ob-body">
            <h2 className="ob-q">¿Cómo te llamás?</h2>
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
                  placeholder="Cómo querés que te llamemos"
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
            <h2 className="ob-q">¿Qué querés cultivar estos días?</h2>
            <p className="ob-hint">Elegí entre 2 y 6. Podés cambiarlo cuando quieras.</p>
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
              {sel.length < 2 ? "Elegí al menos 2" : "Continuar"}
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
              Elegí las actividades que querés recibir. Hagas la que hagas, siempre cerrás
              escribiendo en tu diario lo que sentiste.
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
                    {piso && <span className="cat-opt-tag">siempre</span>}
                  </button>
                );
              })}
            </div>
            <p className="ob-hint" style={{ marginTop: 14 }}>
              "Escribir" siempre está disponible, para los días sin tiempo o ganas de salir.
            </p>
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
            <h2 className="ob-q">¿Cuándo querés recibir tu pausa?</h2>
            <p className="ob-hint">Usamos la hora de tu teléfono.</p>
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
            <h2 className="ob-q">¿Querés que te avisemos?</h2>
            <p className="ob-hint">
              Podés entrar por tu cuenta cuando quieras. Si preferís, te avisamos a la
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

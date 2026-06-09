// Onboarding (M1). "Preparar un ritual", no configurar una app.
// Flujo canónico: Login → SLIDESHOW (qué es + compromiso) → CONFIGURACIÓN.
//   Intro (sin progreso):  0 Bienvenida (marca + slogan) · 1 Qué es + compromiso
//   Config (4 pasos):      2 Datos · 3 Categorías · 4 Momento · 5 Aviso + términos
// (El "Tono" del doc UX fue eliminado del onboarding por canon M1.)

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { api } from "../lib/api";
import { useStore } from "../store";

const MOMENTOS: { key: string; label: string; hora: string }[] = [
  { key: "manana", label: "A la mañana", hora: "08:00" },
  { key: "mediodia", label: "Al mediodía", hora: "13:00" },
  { key: "tarde", label: "A la tarde", hora: "18:00" },
  { key: "noche", label: "A la noche", hora: "21:00" },
];

// Los 4 pasos de configuración (los que muestran progreso).
const CONFIG_STEPS = 4;
const PRIMER_CONFIG = 2;

export function Onboarding() {
  const navigate = useNavigate();
  const { categorias, refrescarPerfil } = useStore();
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Madrid";

  const [step, setStep] = useState(0);
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");
  const [apodo, setApodo] = useState("");
  const [apodoEdited, setApodoEdited] = useState(false);
  const [sel, setSel] = useState<string[]>([]);
  const [momento, setMomento] = useState<string>("manana");
  const [horaCustom, setHoraCustom] = useState<string>("");
  const [aviso, setAviso] = useState(true);
  const [terminos, setTerminos] = useState(false);
  const [guardando, setGuardando] = useState(false);

  const toggleCat = (slug: string) => {
    setSel((cur) => {
      if (cur.includes(slug)) return cur.filter((c) => c !== slug);
      if (cur.length >= 6) return cur;
      return [...cur, slug];
    });
  };

  const horaElegida = () =>
    momento === "custom"
      ? horaCustom || "08:00"
      : MOMENTOS.find((m) => m.key === momento)?.hora || "08:00";

  const finalizar = async () => {
    setGuardando(true);
    try {
      await api.setCategorias(sel);
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
            <p className="ob-explain-body">
              Por fuera del teléfono.
              <br />
              La app es para recibir y guardar
              <br />
              lo que vivís.
            </p>
            <p className="ob-explain-accent">Sin feed ni likes.</p>
            <p className="ob-explain-tip">
              Tené un diario cerca y date unos minutos.
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

      {/* —— 4 · Momento —— */}
      {step === 4 && (
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
            <Button variant="primary" full onClick={() => setStep(5)}>
              Continuar
            </Button>
          </div>
        </>
      )}

      {/* —— 5 · Aviso + términos —— */}
      {step === 5 && (
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

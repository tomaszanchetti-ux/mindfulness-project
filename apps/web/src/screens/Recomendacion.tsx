// WS30 · C2.2 · Recomendación — el wizard (nueva / editar).
//
// Una recomendación es una ficha corta que dejas en tu Baúl: un libro, un video,
// un podcast, un documental u otra cosa que te hizo bien. Vive al lado de tus
// Pausas y con la misma visibilidad (privada o compartida con tu comunidad).
//
// El MISMO componente sirve para escribir una nueva (`/baul/recomendacion/nueva`,
// POST) y para retocar una que ya existe (`/baul/recomendacion/:id/editar`, PUT):
// se distinguen por `useParams`. Dos pasos, con la barra de puntos del onboarding
// y del wizard de Crear: qué recomiendas → por qué.
//
// Escribirlas es de quien es parte (el backend responde 403). A alguien free no
// se le enseña un formulario que va a rebotar: se le cuenta qué sostiene ser
// parte y se vuelve al Baúl.

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { SoloComunidad } from "../components/SoloComunidad";
import { api } from "../lib/api";
import { useStore } from "../store";
import { TIPOS_RECOMENDACION } from "../lib/types";
import type { ItemRecomendacion, TipoRecomendacion, Visibilidad } from "../lib/types";
import "./baul.css";

const PASOS = 2;

// Los mismos topes que aplica el backend (`db/models.py`: RECOMENDACION_*_MAX,
// RECOMENDACIONES_MAX). Acá viven para que el contador se dibuje sin ir y volver;
// la verdad la sigue teniendo la API, y su mensaje en español se muestra tal cual.
export const TITULO_MAX = 80;
export const TEXTO_MAX = 500;
export const RECOMENDACIONES_MAX = 30;

const URL_PREFIJO = "https://";

/** El enlace es opcional, pero si lo hay tiene que ser seguro y tener forma de web. */
function errorDeUrl(url: string): string | null {
  const v = url.trim();
  if (!v) return null;
  if (!v.toLowerCase().startsWith(URL_PREFIJO)) {
    return "El enlace tiene que empezar por https:// — así se abre seguro para quien lo reciba.";
  }
  try {
    const u = new URL(v);
    if (!u.hostname.includes(".")) throw new Error("sin dominio");
  } catch {
    return "Ese enlace no parece completo. Cópialo desde la barra del navegador.";
  }
  return null;
}

export function Recomendacion() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { perfil } = useStore();
  const editando = !!id;

  const [paso, setPaso] = useState(1);
  const [titulo, setTitulo] = useState("");
  const [tipo, setTipo] = useState<TipoRecomendacion | "">("");
  const [texto, setTexto] = useState("");
  const [url, setUrl] = useState("");
  const [visibilidad, setVisibilidad] = useState<Visibilidad>("privada");
  const [cuantas, setCuantas] = useState<number | null>(null);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [listo, setListo] = useState(false);

  const puedeRecomendar = perfil?.limites.recomendaciones === true;

  // —— Lo que hay hoy: para el "N de 30" y, si estamos editando, la ficha ——
  useEffect(() => {
    if (perfil && !puedeRecomendar) {
      setListo(true);
      return;
    }
    if (!perfil) return;
    let vivo = true;
    api
      .recomendaciones()
      .then((lista: ItemRecomendacion[]) => {
        if (!vivo) return;
        setCuantas(lista.length);
        if (editando) {
          const r = lista.find((x) => x.id === id);
          if (!r) {
            navigate("/baul", { replace: true });
            return;
          }
          setTitulo(r.titulo);
          setTipo(r.tipo_recomendacion);
          setTexto(r.texto);
          setUrl(r.url || "");
          setVisibilidad(r.visibilidad);
        }
        setListo(true);
      })
      .catch(() => {
        if (!vivo) return;
        // Editando no se puede seguir sin la ficha; escribiendo una nueva sí: lo
        // único que se pierde es el "N de 30" (el tope lo aplica igual la API).
        if (editando) navigate("/baul", { replace: true });
        else setListo(true);
      });
    return () => {
      vivo = false;
    };
  }, [perfil, puedeRecomendar, editando, id, navigate]);

  const tituloLargo = titulo.trim().length;
  const textoLargo = texto.trim().length;
  const avisoUrl = errorDeUrl(url);

  const puedeSeguir =
    (paso === 1 && tituloLargo > 0 && tituloLargo <= TITULO_MAX && !!tipo) ||
    (paso === 2 && textoLargo > 0 && textoLargo <= TEXTO_MAX && !avisoUrl);

  const guardar = async () => {
    if (!tipo) return;
    setGuardando(true);
    setError(null);
    const limpio = url.trim();
    try {
      if (editando && id) {
        // El contrato manda: `url: ""` borra el enlace, `null` no lo toca. Como
        // el campo vacío significa "sin enlace", va la cadena vacía.
        await api.editarRecomendacion(id, {
          titulo: titulo.trim(),
          tipo,
          texto: texto.trim(),
          url: limpio,
          visibilidad,
        });
      } else {
        await api.crearRecomendacion({
          titulo: titulo.trim(),
          tipo,
          texto: texto.trim(),
          url: limpio || null,
          visibilidad,
        });
      }
      navigate("/baul", { replace: true });
    } catch (e) {
      // La API habla en español (403 free · 409 el tope de 30 · 422 los largos y
      // el enlace): se muestra tal cual, junto al botón que lo disparó.
      const err = e as Error & { status?: number };
      setError(
        err.message ||
          "No pudimos guardar tu recomendación. Inténtalo de nuevo en un rato.",
      );
      setGuardando(false);
    }
  };

  // Sin perfil todavía no sabemos si es parte: no se dibuja nada.
  if (!perfil) return <div className="center-note">…</div>;

  if (!puedeRecomendar) {
    return (
      <div>
        <button className="back-link" onClick={() => navigate("/baul")}>← Baúl</button>
        <SoloComunidad
          onClose={() => navigate("/baul", { replace: true })}
        />
      </div>
    );
  }

  if (!listo) return <div className="center-note">…</div>;

  return (
    <div className="ob reco-wizard">
      <div className="ob-progress">
        {Array.from({ length: PASOS }).map((_, i) => (
          <div key={i} className={`ob-dot ${i < paso ? "on" : ""}`} />
        ))}
      </div>

      <div className="ob-body">
        {/* —— 1 · Qué recomiendas ————————————————————————————————————— */}
        {paso === 1 && (
          <>
            <h2 className="ob-q">
              {editando ? "Retoca tu recomendación" : "¿Qué quieres recomendar?"}
            </h2>
            <p className="ob-hint">
              Algo que te hizo bien y que le puede hacer bien a alguien más.
            </p>

            {!editando && cuantas !== null && (
              <p className="reco-cupo">
                Llevas {cuantas} de {RECOMENDACIONES_MAX}.
              </p>
            )}

            <div className="reco-tipos" role="radiogroup" aria-label="Qué es">
              {TIPOS_RECOMENDACION.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  role="radio"
                  aria-checked={tipo === t.id}
                  className={`reco-tipo ${tipo === t.id ? "on" : ""}`}
                  onClick={() => setTipo(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <label className="ob-field-label" htmlFor="reco-titulo">
              El título · cómo se llama
            </label>
            <input
              id="reco-titulo"
              className="reco-input"
              type="text"
              maxLength={TITULO_MAX}
              placeholder="El nombre del libro, del video, del podcast…"
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
            />
            <p className="counter">
              {titulo.length}/{TITULO_MAX}
            </p>
          </>
        )}

        {/* —— 2 · Por qué, el enlace y con quién ——————————————————————— */}
        {paso === 2 && (
          <>
            <h2 className="ob-q">¿Por qué lo recomiendas?</h2>
            <p className="ob-hint">
              Cuéntalo como se lo contarías a alguien: qué te dejó, cuándo te
              vino bien.
            </p>

            <textarea
              id="reco-texto"
              className="textarea"
              maxLength={TEXTO_MAX}
              placeholder="Lo que te dejó, en tus palabras."
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
            />
            <p className="counter">
              {texto.length}/{TEXTO_MAX}
            </p>

            <label className="ob-field-label" htmlFor="reco-url">
              El enlace (opcional)
            </label>
            <input
              id="reco-url"
              className="reco-input"
              type="url"
              inputMode="url"
              placeholder="https://…"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            {avisoUrl ? (
              <p className="reco-aviso">{avisoUrl}</p>
            ) : (
              <p className="helper">
                Si tienes dónde encontrarlo, pégalo aquí. Solo enlaces que
                empiecen por https://.
              </p>
            )}

            {/* La misma puerta que las Pausas, con las mismas palabras. */}
            <label className="toggle-row visibilidad-row" style={{ marginTop: 20 }}>
              <span className="visibilidad-label">Compartir con tu Comunidad</span>
              <span className="switch">
                <input
                  type="checkbox"
                  checked={visibilidad === "compartida"}
                  onChange={(e) => setVisibilidad(e.target.checked ? "compartida" : "privada")}
                />
                <span className="slider" />
              </span>
            </label>
            <p className="visibilidad-nota">
              Compartida, la ven las personas de tu comunidad. Privada, queda solo
              para ti.
            </p>
          </>
        )}
      </div>

      {error && <p className="reco-aviso">{error}</p>}

      <div className="ob-foot">
        {paso < PASOS ? (
          <Button variant="primary" full disabled={!puedeSeguir} onClick={() => setPaso(paso + 1)}>
            Continuar
          </Button>
        ) : (
          <Button
            variant="primary"
            full
            disabled={!puedeSeguir || guardando}
            onClick={guardar}
          >
            {guardando ? "Guardando…" : editando ? "Guardar cambios" : "Guardar"}
          </Button>
        )}
        <Button
          variant="tertiary"
          disabled={guardando}
          onClick={() => (paso === 1 ? navigate("/baul") : setPaso(paso - 1))}
        >
          {paso === 1 ? "Cancelar" : "Atrás"}
        </Button>
      </div>
    </div>
  );
}

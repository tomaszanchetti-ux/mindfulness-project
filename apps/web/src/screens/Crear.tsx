// WS27 · B2.2 · Crear — la pestaña donde escribes cartas para la comunidad.
//
// Dos pantallas en una, según el plan (el backend manda: `limites.propone_cartas`):
//
//  · FREE      → se explica qué es esto y, al entrar (o al tocar el botón), el
//                pop-up reusable `SoloComunidad` invita a ser parte. Nunca se
//                muestra un formulario apagado: no se le enseña a alguien una
//                puerta cerrada.
//  · PREMIUM   → el CTA "Escribir una carta" y, debajo, **Tus cartas**: la lista
//                prolija que pidió Tomás (Q/A visual WS24 §3) — miniatura, frase
//                y el estado con su rótulo y su color, más lo que corresponde a
//                cada estado (la sugerencia, el motivo, el impacto, retirar).
//
// Una carta en curso a la vez: con una en el recorrido el CTA se apaga y se
// explica por qué. El 409 del backend diría lo mismo, pero llegar hasta ahí para
// enterarse no es una invitación, es un portazo.
//
// WS30 · C2b · Crear es la ÚNICA puerta para hacer algo nuevo: arriba de "Tus
// cartas" van los dos accesos —escribir una carta y recomendar algo— y el Baúl
// (que perdió su CTA) vuelve a ser solo la lista. Las dos son de quien es parte:
// el free ve la misma invitación de siempre, sin formulario.

import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { CartaMini } from "../components/CartaMini";
import { SoloComunidad } from "../components/SoloComunidad";
import { api } from "../lib/api";
import { fechaCorta } from "../lib/format";
import { enCurso, impacto, rotulo, textoFirma, textoPuntaje } from "../lib/propuestas";
import { useStore } from "../store";
import type { CartaPropuesta } from "../lib/types";
import "./crear.css";

export function Crear() {
  const navigate = useNavigate();
  const { perfil } = useStore();
  const puedeEscribir = perfil?.limites.propone_cartas === true;
  const puedeRecomendar = perfil?.limites.recomendaciones === true;

  const [cartas, setCartas] = useState<CartaPropuesta[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Free: el pop-up se abre solo al entrar. Se puede cerrar y volver a abrirlo
  // con el botón — cerrarlo no deja la pantalla muda.
  const [verPopup, setVerPopup] = useState(false);
  const [aRetirar, setARetirar] = useState<CartaPropuesta | null>(null);
  const [retirando, setRetirando] = useState(false);

  const cargar = useCallback(() => {
    setError(null);
    api
      .cartasMias()
      .then(setCartas)
      .catch((e) => {
        setCartas([]);
        setError((e as Error).message);
      });
  }, []);

  useEffect(() => {
    if (perfil === null) return; // todavía no sabemos de qué plan es
    if (!puedeEscribir) {
      setCartas([]);
      setVerPopup(true);
      return;
    }
    cargar();
  }, [perfil, puedeEscribir, cargar]);

  const retirar = async () => {
    if (!aRetirar) return;
    setRetirando(true);
    try {
      await api.retirarCarta(aRetirar.id);
      setARetirar(null);
      cargar();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRetirando(false);
    }
  };

  // ——————————————————————————————————————————————————— Free
  if (perfil && !puedeEscribir) {
    return (
      <div className="crear">
        <div className="screen-head">
          <h1 className="screen-title">Crear</h1>
          <p className="screen-sub">Deja algo para la comunidad</p>
        </div>

        <div className="crear-porque">
          <p>
            Las cartas de Dwellia las escriben personas. Eliges un pilar y una
            acción inicial, escribes la frase y la Pausa que propones, y si entra
            al mazo le llega a alguien un día cualquiera, con tu apodo o en
            anónimo. También puedes dejar algo que te hizo bien, para que lo
            encuentre tu comunidad.
          </p>
        </div>

        {/* Las dos puertas también acá: el free ve QUÉ hay, y al tocar cualquiera
            recibe la misma invitación. Nunca un formulario apagado. */}
        <Puertas onCarta={() => setVerPopup(true)} onRecomendacion={() => setVerPopup(true)} />

        {verPopup && <SoloComunidad onClose={() => setVerPopup(false)} />}
      </div>
    );
  }

  if (!perfil || cartas === null) return <div className="center-note">…</div>;

  // ——————————————————————————————————————————————————— Premium
  const abierta = cartas.find((c) => enCurso(c.estado)) || null;

  return (
    <div className="crear">
      <div className="screen-head">
        <h1 className="screen-title">Crear</h1>
        <p className="screen-sub">Deja algo para la comunidad</p>
      </div>

      {error && <p className="crear-aviso">{error}</p>}

      {/* Las dos cosas que puedes dejar, antes de la lista de tus cartas. */}
      <Puertas
        cartaApagada={!!abierta}
        onCarta={() => navigate("/crear/nueva")}
        onRecomendacion={() =>
          puedeRecomendar ? navigate("/baul/recomendacion/nueva") : setVerPopup(true)
        }
      />
      {abierta && (
        <p className="crear-nota">
          Tienes una carta en evaluación. Cuando termine, puedes escribir otra.
        </p>
      )}

      {verPopup && <SoloComunidad onClose={() => setVerPopup(false)} />}

      {cartas.length === 0 ? (
        <div className="empty">
          <p className="empty-title">Todavía no escribiste ninguna carta.</p>
          <p className="empty-body">
            Cuando escribas la primera, aquí vas a poder seguir su recorrido.
          </p>
        </div>
      ) : (
        <div className="crear-lista">
          <h2 className="crear-lista-titulo">Tus cartas</h2>
          {cartas.map((c) => (
            <PropuestaItem
              key={c.id}
              propuesta={c}
              apodo={perfil.apodo}
              enRetiro={aRetirar?.id === c.id}
              retirando={retirando}
              onRetirar={() => setARetirar(c)}
              onCancelarRetiro={() => setARetirar(null)}
              onConfirmarRetiro={retirar}
              onEditar={(usarSugerencia) =>
                navigate(
                  `/crear/${c.id}/editar${usarSugerencia ? "?usar=sugerencia" : ""}`,
                )
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

// —— Las dos puertas ————————————————————————————————————————————————————————
// Dos tarjetas grandes, no dos botones: cada una dice qué es lo que vas a dejar,
// con una línea abajo. Es la única entrada a escribir una carta y a recomendar
// algo (el Baúl ya no tiene la suya).
function Puertas({
  cartaApagada,
  onCarta,
  onRecomendacion,
}: {
  cartaApagada?: boolean;
  onCarta: () => void;
  onRecomendacion: () => void;
}) {
  return (
    <div className="crear-puertas">
      <button
        type="button"
        className="crear-puerta es-carta"
        disabled={cartaApagada}
        onClick={onCarta}
      >
        <span className="crear-puerta-tit">Escribir una carta</span>
        <span className="crear-puerta-nota">
          Una carta que puede ser la Pausa de alguien más.
        </span>
      </button>
      <button type="button" className="crear-puerta" onClick={onRecomendacion}>
        <span className="crear-puerta-tit">Recomendar algo</span>
        <span className="crear-puerta-nota">
          Un libro, un video, un podcast que te hizo bien.
        </span>
      </button>
    </div>
  );
}

// —— Una carta de la lista ——————————————————————————————————————————————————
// Arriba, lo mismo para todas: miniatura, píldora de estado, frase y pilar.
// Abajo, SOLO lo que ese estado tiene para decir. Una carta rechazada no muestra
// un impacto en cero, y una aprobada no muestra un reproche viejo.
function PropuestaItem({
  propuesta,
  apodo,
  enRetiro,
  retirando,
  onRetirar,
  onCancelarRetiro,
  onConfirmarRetiro,
  onEditar,
}: {
  propuesta: CartaPropuesta;
  apodo: string | null;
  enRetiro: boolean;
  retirando: boolean;
  onRetirar: () => void;
  onCancelarRetiro: () => void;
  onConfirmarRetiro: () => void;
  onEditar: (usarSugerencia: boolean) => void;
}) {
  const { estado, carta, motivo, sugerencia } = propuesta;
  const r = rotulo(estado);
  const cat = carta.categoria;

  return (
    <article className="prop">
      <div className="prop-cabecera">
        <CartaMini carta={carta} />
        <div className="prop-datos">
          <div className="prop-top">
            <span className={`pill-estado es-${r.tono}`}>{r.texto}</span>
            <span className="prop-fecha">{fechaCorta(propuesta.created_at)}</span>
          </div>
          <p className="prop-frase">{carta.frase}</p>
          <p className="prop-cat" style={{ color: cat?.color_text }}>
            {cat?.nombre}
            {carta.accion?.nombre ? ` · ${carta.accion.nombre.toLowerCase()}` : ""}
          </p>
        </div>
      </div>

      {/* —— Necesita un retoque: el motivo, la sugerencia y las dos salidas —— */}
      {estado === "a_revisar" && (
        <div className="prop-extra">
          {motivo && <p className="prop-motivo">{motivo}</p>}
          {sugerencia && (
            <div className="prop-sugerencia">
              <span className="prop-lbl">La sugerencia</span>
              {sugerencia.frase && <p className="prop-sug-frase">“{sugerencia.frase}”</p>}
              {sugerencia.prompt && <p className="prop-sug-prompt">{sugerencia.prompt}</p>}
            </div>
          )}
          <div className="prop-acciones">
            {sugerencia && (
              <Button variant="primary" full onClick={() => onEditar(true)}>
                Usar la sugerencia
              </Button>
            )}
            <Button
              variant={sugerencia ? "secondary" : "primary"}
              full
              onClick={() => onEditar(false)}
            >
              Editar y reenviar
            </Button>
          </div>
        </div>
      )}

      {/* —— No aprobada: el motivo, y nada más —— */}
      {estado === "rechazada" && motivo && (
        <div className="prop-extra">
          <p className="prop-motivo">{motivo}</p>
        </div>
      )}

      {/* —— Cargada a la comunidad: a cuánta gente le llegó, cómo le fue y cómo
             salió firmada. El impacto y el puntaje son dos cosas distintas: a
             cuántos acompañó, y qué les pareció (decisión de Tomás, WS28). —— */}
      {estado === "aprobada" && (
        <div className="prop-extra">
          <p className="prop-impacto">{impacto(propuesta.personas_acompanadas)}</p>
          <p className="prop-puntaje">
            {textoPuntaje(propuesta.estrellas_promedio, propuesta.veces_puntuada)}
          </p>
          <p className="prop-firma">{textoFirma(propuesta.firma, apodo)}</p>
        </div>
      )}

      {/* —— En curso: retirarla, con la pregunta en la pantalla (nunca confirm()) —— */}
      {enCurso(estado) && (
        <div className="prop-extra">
          {enRetiro ? (
            <div className="confirm-inline">
              <p className="confirm-inline-pregunta">¿Retirar esta carta?</p>
              <p className="confirm-inline-nota">
                Se baja del recorrido y queda guardada como retirada. Después
                puedes escribir otra.
              </p>
              <div className="actions-stack">
                <Button variant="danger" full disabled={retirando} onClick={onConfirmarRetiro}>
                  {retirando ? "Retirando…" : "Sí, retirarla"}
                </Button>
                <Button variant="tertiary" disabled={retirando} onClick={onCancelarRetiro}>
                  Dejarla en evaluación
                </Button>
              </div>
            </div>
          ) : (
            <button className="link prop-retirar" onClick={onRetirar}>
              Retirar esta carta
            </button>
          )}
        </div>
      )}
    </article>
  );
}

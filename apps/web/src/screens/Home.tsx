// Home / Hoy (§19). El lugar más simple de la app: recibir la consigna y decidir
// qué hacer con ella. Carta cerrada (frente) → "Ver mi pausa" revela el dorso.
// Si ya guardaste la pausa de hoy, la Home pasa a modo "hecho" (en calma).
//
// QA 10/06: la carta "llega" al horario elegido (hora_aviso). Antes de esa hora la
// Home muestra una espera con cuenta regresiva — salvo que la pausa de hoy ya esté
// guardada (p. ej. cambiaste el horario después de vivirla), donde manda "hecho".
//
// Primer uso (WS14): dos nudges contextuales sobre la carta REAL — señalan la carta
// y el botón Guardar. Se ven una sola vez por usuario/dispositivo (lib/nudges).
//
// WS24 · A2.2: "Otra carta" — cambiar la carta del día. Cuántas veces se puede lo
// dice el backend (`perfil.limites.cambios_carta`, 0 en free ⇒ el botón no existe)
// y cuántas van, la entrega (`entrega.cambios`). Sigue llegando UNA carta por día:
// el cambio reemplaza la de hoy, y la nueva vuelve al frente para descubrirla.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Campana } from "../components/Campana";
import { Spotlight } from "../components/Spotlight";
import { StoryArt } from "../components/StoryArt";
import { useAuth } from "../auth";
import { api } from "../lib/api";
import { cuentaRegresiva, fechaLarga, horaAvisoDeHoy, saludo } from "../lib/format";
import { marcarNudgeVisto, nudgeVisto } from "../lib/nudges";
import { useStore } from "../store";
import type { CartaDelDia } from "../lib/types";

export function Home() {
  const navigate = useNavigate();
  const { perfil } = useStore();
  const uid = useAuth().user?.uid ?? "anon";
  const [data, setData] = useState<CartaDelDia | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [flipped, setFlipped] = useState(false);
  const [ahora, setAhora] = useState(() => new Date());
  const [nudgeCarta, setNudgeCarta] = useState(() => !nudgeVisto(uid, "carta"));
  const [nudgeGuardar, setNudgeGuardar] = useState(() => !nudgeVisto(uid, "guardar"));
  const [cambiando, setCambiando] = useState(false);
  const [avisoCambio, setAvisoCambio] = useState<string | null>(null);

  useEffect(() => {
    api
      .cartaDelDia()
      .then((d) => {
        setData(d);
        // Modo "hecho": si ya guardaste hoy, mostramos la carta girada (la frase a la vista).
        if (d.entrega.completada) setFlipped(true);
      })
      .catch((e) => setError((e as Error).message));
  }, []);

  // Tic del reloj: mantiene vivos el saludo y la cuenta regresiva de la espera.
  useEffect(() => {
    const t = setInterval(() => setAhora(new Date()), 20_000);
    return () => clearInterval(t);
  }, []);

  if (error) return <div className="center-note">{error}</div>;
  if (!data) return <div className="center-note">Preparando tu pausa…</div>;

  const { carta, entrega } = data;
  const hecha = entrega.completada;

  // —— Cambiar la carta del día (WS24 · A2.2) ——
  // La Pausa "cerrada" es la misma que mira el backend: guardada, puntuada o con
  // reflexión. Una vez vivida, la carta de hoy ya no se toca.
  const cerrada = hecha || entrega.estrellas != null || !!entrega.reflexion;
  const cambiosMax = perfil?.limites.cambios_carta ?? 0;
  const cambiosRestantes = cambiosMax - (entrega.cambios ?? 0);
  const puedeCambiar = cambiosMax > 0 && !cerrada;

  const otraCarta = async () => {
    if (cambiando) return;
    setCambiando(true);
    setAvisoCambio(null);
    try {
      const nueva = await api.cambiarCarta(entrega.id);
      // La carta vuelve al frente y recién ahí entra la nueva: el relevo se ve
      // como un descubrir, no como un parpadeo.
      setFlipped(false);
      await new Promise((r) => setTimeout(r, 220));
      setData(nueva);
    } catch (e) {
      setAvisoCambio((e as Error).message);
    } finally {
      setCambiando(false);
    }
  };

  // ¿El horario elegido aún no llegó hoy? → la carta todavía "no llegó".
  const horaCarta = horaAvisoDeHoy(perfil?.hora_aviso);
  const esperando = !hecha && horaCarta !== null && ahora < horaCarta;

  if (esperando) {
    return (
      <div>
        <div className="home-greet campana-fila">
          <div className="campana-fila-txt">
            <p className="screen-kicker">
              {saludo()}
              {perfil?.apodo ? `, ${perfil.apodo}` : ""}.
            </p>
            <p className="home-date">{fechaLarga(entrega.fecha)}</p>
          </div>
          <Campana />
        </div>
        <div className="home-wait">
          <div className="home-wait-art">
            <StoryArt escena="recibe" />
          </div>
          <p className="home-wait-title">
            A las {perfil?.hora_aviso?.slice(0, 5)} te llegará tu carta de hoy.
          </p>
          <p className="home-wait-count">{cuentaRegresiva(horaCarta, ahora)}</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="home-greet campana-fila">
        <div className="campana-fila-txt">
          <p className="screen-kicker">
            {saludo()}
            {perfil?.apodo ? `, ${perfil.apodo}` : ""}.
          </p>
          <p className="home-date">{fechaLarga(entrega.fecha)}</p>
        </div>
        <Campana />
      </div>

      <div
        className={`home-card-wrap ${cambiando ? "is-cambiando" : ""}`}
        data-nudge="home-card"
      >
        {/* key por carta: al cambiarla, la nueva entra con su propia transición. */}
        <div key={carta.id} className="home-card-relevo">
          <Card carta={carta} flipped={flipped} onFlip={() => setFlipped((f) => !f)} />
        </div>
      </div>

      {hecha ? (
        // —— Modo "hecho": pausa de hoy ya guardada. En calma, sin nada que exigir. ——
        <>
          <p className="home-done-note">
            Ya viviste tu pausa de hoy.{" "}
            {perfil?.hora_aviso
              ? `Mañana a las ${perfil.hora_aviso.slice(0, 5)} te espera una nueva.`
              : "Mañana te espera una nueva."}
          </p>
          <div className="actions-stack">
            <Button
              variant="primary"
              full
              onClick={() => navigate(`/baul/${entrega.id}`)}
            >
              {entrega.reflexion ? "Ver mi reflexión" : "Ver mi pausa de hoy"}
            </Button>
          </div>
        </>
      ) : !flipped ? (
        <div className="actions-stack">
          <Button variant="primary" full onClick={() => setFlipped(true)}>
            Ver mi pausa
          </Button>
        </div>
      ) : (
        <div className="actions-stack">
          <Button
            variant="primary"
            full
            data-nudge="guardar"
            onClick={() => navigate(`/reflexionar/${entrega.id}`)}
          >
            Guardar
          </Button>
          <Button
            variant="secondary"
            full
            onClick={() => navigate(`/compartir/${entrega.id}`)}
          >
            Compartir
          </Button>
        </div>
      )}

      {/* —— Otra carta (premium): discreto, debajo de las acciones de la carta —— */}
      {puedeCambiar && (
        <div className="home-otra-carta">
          {cambiosRestantes > 0 ? (
            <Button
              variant="tertiary"
              disabled={cambiando}
              onClick={otraCarta}
            >
              {cambiando
                ? "Buscando otra carta…"
                : `Otra carta · ${
                    cambiosRestantes === 1 ? "queda 1" : `quedan ${cambiosRestantes}`
                  }`}
            </Button>
          ) : (
            <p className="home-otra-carta-fin">
              Hoy ya cambiaste tu carta {cambiosMax} veces. Mañana llega una nueva.
            </p>
          )}
          {avisoCambio && <p className="home-otra-carta-aviso">{avisoCambio}</p>}
        </div>
      )}

      {/* —— Nudges de primer uso (solo con la pausa de hoy pendiente) —— */}
      {!hecha && !flipped && nudgeCarta && (
        <Spotlight
          targetSelector='[data-nudge="home-card"]'
          titulo="Esta es tu carta de hoy"
          cuerpo="Cada día recibes una nueva. Tócala para descubrir tu pausa."
          onDone={() => {
            marcarNudgeVisto(uid, "carta");
            setNudgeCarta(false);
          }}
        />
      )}
      {!hecha && flipped && nudgeGuardar && (
        <Spotlight
          targetSelector='[data-nudge="guardar"]'
          titulo="Vive tu pausa, lejos del teléfono"
          cuerpo="Deja que la acción te lleve a la calma. Al volver, escribe en tu diario lo que sentiste y toca Guardar. Si quieres regalar la carta, toca Compartir."
          onDone={() => {
            marcarNudgeVisto(uid, "guardar");
            setNudgeGuardar(false);
          }}
        />
      )}
    </div>
  );
}

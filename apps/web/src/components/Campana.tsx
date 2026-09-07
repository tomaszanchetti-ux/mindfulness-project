// WS28 · B2.2a · La campana de avisos.
//
// Vive en la cabecera de Hoy y de Crear. No es un centro de notificaciones: es
// una campana con un punto — si hay algo sin leer, se enciende; si no, se queda
// quieta. Lo que hay que leer está en `/avisos`, no en un pop-up encima de la
// pausa de alguien.
//
// Se refresca al montar y al volver a la pestaña visible (el caso real: la carta
// se aprueba mientras la app está abierta en otra solapa del teléfono). Nunca en
// un intervalo: una app de calma no hace polling.
//
// WS29 · C0 · vive en el cluster de arriba a la derecha (`AccionesArriba`), en
// las cuatro pestañas. Su CSS (`.campana*`) es global: está en `app.css`.

import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";

export function Campana() {
  const navigate = useNavigate();
  const [noLeidos, setNoLeidos] = useState(0);

  const cargar = useCallback(() => {
    // Si la bandeja falla, la campana se queda apagada: un error de red no puede
    // romper la cabecera de la Home.
    api
      .avisos()
      .then((b) => setNoLeidos(b.no_leidos))
      .catch(() => {});
  }, []);

  useEffect(() => {
    cargar();
    const alVolver = () => {
      if (document.visibilityState === "visible") cargar();
    };
    document.addEventListener("visibilitychange", alVolver);
    return () => document.removeEventListener("visibilitychange", alVolver);
  }, [cargar]);

  const hay = noLeidos > 0;

  return (
    <button
      type="button"
      className={`campana ${hay ? "tiene" : ""}`}
      aria-label={
        hay
          ? `Avisos · ${noLeidos === 1 ? "1 sin leer" : `${noLeidos} sin leer`}`
          : "Avisos"
      }
      onClick={() => navigate("/avisos")}
    >
      {/* Línea fina, el mismo trazo de los íconos de la tab bar. */}
      <svg
        width={22}
        height={22}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.7}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
      >
        <path d="M17.8 17.2H6.2l1.3-2.3v-3.7a4.5 4.5 0 0 1 9 0v3.7z" />
        <path d="M12 4.9V3.6" />
        <path d="M10.3 19.6a1.9 1.9 0 0 0 3.4 0" />
      </svg>
      {hay && <span className="campana-badge">{noLeidos > 9 ? "9+" : noLeidos}</span>}
    </button>
  );
}

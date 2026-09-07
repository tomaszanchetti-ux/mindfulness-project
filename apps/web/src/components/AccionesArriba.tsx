// WS29 · C0 · El cluster de arriba a la derecha: avisos y perfil.
//
// Con la cuarta pestaña (Comunidad), Perfil deja de ser una pestaña y sube a la
// esquina, al lado de la campana. Los dos son el mismo botón redondo de 42 px:
// el de avisos en papel, el de perfil en verde — es tu cara dentro de Dwellia,
// y se distingue de un vistazo.
//
// Vive una sola vez, en el Frame, y se ve en las cuatro pestañas. Las pantallas
// de foco (ritual, wizard, detalle del Baúl) no lo llevan: ahí no hay tab bar.

import { useLocation, useNavigate } from "react-router-dom";
import { Campana } from "./Campana";

export function AccionesArriba() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const enPerfil = pathname.startsWith("/perfil");

  return (
    <div className="acciones-arriba">
      <Campana />
      <button
        type="button"
        className={`campana boton-perfil ${enPerfil ? "es-activo" : ""}`}
        aria-label="Perfil"
        aria-current={enPerfil ? "page" : undefined}
        onClick={() => navigate("/perfil")}
      >
        {/* El mismo ícono de persona que tenía la tab bar, con el mismo trazo. */}
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
          <circle cx="12" cy="8" r="3.6" />
          <path d="M5.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6" />
        </svg>
      </button>
    </div>
  );
}

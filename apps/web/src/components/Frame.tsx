// El marco mobile-first (§24): contenedor centrado en desktop, fondo cálido alrededor.
// WS29 · C0: la tab bar sigue siendo de CUATRO, pero cambia quiénes son —
// Hoy · Baúl · Comunidad · Crear. Perfil deja de ser pestaña y sube al cluster de
// arriba a la derecha, junto a la campana (`AccionesArriba`), que se ve en las
// cuatro. "Crear" pasa de la pluma a un signo +, y va en verde: es lo único que
// se hace desde la barra, no un lugar al que se va.
// `/admin` NO es una pestaña: es el escritorio de Dwellia y se entra desde Perfil.
// La tab bar se oculta en pantallas de ritual/público (foco total).

import type { ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { AccionesArriba } from "./AccionesArriba";

const TABS = [
  { to: "/hoy", label: "Hoy", glyph: "sun", clase: "" },
  { to: "/baul", label: "Baúl", glyph: "chest", clase: "" },
  { to: "/comunidad", label: "Comunidad", glyph: "personas", clase: "" },
  { to: "/crear", label: "Crear", glyph: "mas", clase: "tab-crear" },
];

// Rutas sin tab bar (experiencias de foco): ritual, compartir, onboarding, login,
// público, y el detalle del Baúl (pager a pantalla completa · "/baul/" ≠ "/baul").
// WS24: "/premium" SÍ lleva tabs (se lee y se vuelve, como el método); la vuelta
// del Checkout "/premium/gracias" no, es un momento de cierre a pantalla limpia.
// WS27: el wizard de Crear ("/crear/" ≠ "/crear") es un foco como el onboarding,
// y el adminland es otro lugar: se entra y se sale por su propio enlace.
// WS29 · C0: la ficha de otra persona y la Pausa extra son lecturas a pantalla
// completa, igual que el detalle del Baúl. El perfil ajeno ("/comunidad/:id") sí
// lleva tabs: sigue siendo un recorrido dentro de Comunidad.
const SIN_TABS = [
  "/onboarding",
  "/login",
  "/c/",
  "/reflexionar",
  "/cierre",
  "/compartir",
  "/baul/",
  "/crear/",
  "/comunidad/ficha/",
  "/pausa/",
  "/admin",
  "/terminos",
  "/premium/gracias",
];

// Pantallas que no son el teléfono: el escritorio de Dwellia respira más ancho.
const ANCHAS = ["/admin"];

export function Frame({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const showTabs = !SIN_TABS.some((p) => pathname.startsWith(p));
  const ancha = ANCHAS.some((p) => pathname.startsWith(p));

  return (
    <div className="frame">
      <div
        className={`frame-inner ${showTabs ? "with-tabs" : ""} ${ancha ? "is-wide" : ""}`}
      >
        {showTabs && <AccionesArriba />}
        {children}
      </div>
      {showTabs && (
        <nav className="tabbar" aria-label="Navegación principal">
          {TABS.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              className={({ isActive }) =>
                `tab ${t.clase} ${isActive ? "tab-active" : ""}`
              }
            >
              <TabIcon name={t.glyph} />
              <span>{t.label}</span>
            </NavLink>
          ))}
        </nav>
      )}
    </div>
  );
}

function TabIcon({ name }: { name: string }) {
  const common = {
    width: 22,
    height: 22,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  if (name === "sun")
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="4.2" />
        <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4" />
      </svg>
    );
  if (name === "chest")
    return (
      <svg {...common}>
        <rect x="4" y="8" width="16" height="11" rx="2" />
        <path d="M4 12h16M12 8v11" />
        <path d="M5 8c0-2.2 1.8-4 4-4h6c2.2 0 4 1.8 4 4" />
      </svg>
    );
  // Comunidad: el mismo trazo del ícono de persona, pero tres — una al frente y
  // dos detrás. Las de atrás son medias cabezas: quedan a la sombra de la de
  // adelante y el ícono no se ensucia a 22 px.
  if (name === "personas")
    return (
      <svg {...common}>
        <circle cx="12" cy="9" r="3.1" />
        <path d="M6.6 19.6c0-3.1 2.4-5.2 5.4-5.2s5.4 2.1 5.4 5.2" />
        <path d="M17.6 6.4a2.6 2.6 0 0 1 0 5.2" />
        <path d="M19 13.6c1.8.7 2.9 2.2 2.9 4.1" />
        <path d="M6.4 6.4a2.6 2.6 0 0 0 0 5.2" />
        <path d="M5 13.6c-1.8.7-2.9 2.2-2.9 4.1" />
      </svg>
    );
  // Crear: un + limpio. Se hace algo, no se va a ningún lado.
  if (name === "mas")
    return (
      <svg {...common}>
        <path d="M12 6v12M6 12h12" />
      </svg>
    );
  return (
    <svg {...common}>
      <circle cx="12" cy="8" r="3.6" />
      <path d="M5.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6" />
    </svg>
  );
}

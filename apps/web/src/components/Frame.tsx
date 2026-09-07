// El marco mobile-first (§24): contenedor centrado en desktop, fondo cálido alrededor.
// WS27 · B2.2: la tab bar pasa a CUATRO — Hoy · Baúl · Crear · Perfil (§4 del
// roadmap v2). "Crear" lleva una pluma, el mismo sello que cierra toda pausa.
// `/admin` NO es una pestaña: es el escritorio de Dwellia y se entra desde Perfil.
// La tab bar se oculta en pantallas de ritual/público (foco total).

import type { ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";

const TABS = [
  { to: "/hoy", label: "Hoy", glyph: "sun" },
  { to: "/baul", label: "Baúl", glyph: "chest" },
  { to: "/crear", label: "Crear", glyph: "pluma" },
  { to: "/perfil", label: "Perfil", glyph: "person" },
];

// Rutas sin tab bar (experiencias de foco): ritual, compartir, onboarding, login,
// público, y el detalle del Baúl (pager a pantalla completa · "/baul/" ≠ "/baul").
// WS24: "/premium" SÍ lleva tabs (se lee y se vuelve, como el método); la vuelta
// del Checkout "/premium/gracias" no, es un momento de cierre a pantalla limpia.
// WS27: el wizard de Crear ("/crear/" ≠ "/crear") es un foco como el onboarding,
// y el adminland es otro lugar: se entra y se sale por su propio enlace.
const SIN_TABS = [
  "/onboarding",
  "/login",
  "/c/",
  "/reflexionar",
  "/cierre",
  "/compartir",
  "/baul/",
  "/crear/",
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
        {children}
      </div>
      {showTabs && (
        <nav className="tabbar" aria-label="Navegación principal">
          {TABS.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              className={({ isActive }) => `tab ${isActive ? "tab-active" : ""}`}
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
  // La pluma: el mismo gesto del sello de la carta (escribir es el cierre).
  if (name === "pluma")
    return (
      <svg {...common}>
        <path d="M6.4 18.6c1-5.2 4.4-9.4 11.2-12-1.4 6.6-4.6 10.6-9.8 12.2" />
        <path d="M6.4 18.6 4 21" />
        <path d="M9.2 16.2c1.6-2.6 3.8-4.8 6.6-6.4" strokeWidth="1.2" />
      </svg>
    );
  return (
    <svg {...common}>
      <circle cx="12" cy="8" r="3.6" />
      <path d="M5.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6" />
    </svg>
  );
}

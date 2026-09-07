import { StrictMode, useEffect } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import "./theme.css";
import "./app.css";

import { Frame } from "./components/Frame";
import { AuthProvider, useAuth } from "./auth";
import { StoreProvider, useStore } from "./store";
import { initInstallPrompt } from "./pwa";

import { Login } from "./screens/Login";
import { LoginEmail } from "./screens/LoginEmail";
import { Onboarding } from "./screens/Onboarding";
import { Home } from "./screens/Home";
import { Reflect } from "./screens/Reflect";
import { Completion } from "./screens/Completion";
import { Baul } from "./screens/Baul";
import { EntryDetail } from "./screens/EntryDetail";
import { Share } from "./screens/Share";
import { PublicShare } from "./screens/PublicShare";
import { Profile } from "./screens/Profile";
import { Metodo } from "./screens/Metodo";
import { Terms } from "./screens/Terms";
import { Premium } from "./screens/Premium";
import { PremiumGracias } from "./screens/PremiumGracias";
// WS27/28 · B2.2 · Crear (la pestaña), el wizard, los avisos y el adminland.
import { Crear } from "./screens/Crear";
import { CartaNueva } from "./screens/CartaNueva";
import { Avisos } from "./screens/Avisos";
import { Admin } from "./screens/Admin";

// Guarda de sesión: sin usuario logueado, todo lo privado vuelve al login.
function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, cargandoAuth } = useAuth();
  if (cargandoAuth) return <div className="center-note">…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

// WS25 · el regalo (`/c/:token`) también exige login, pero NO onboarding: quien
// recibe el enlace por WhatsApp puede abrirlo antes de configurar nada. Como el
// login manda a /hoy o /onboarding, guardamos a dónde iba para volver después.
const DESTINO_KEY = "dwellia-destino";

function RequireAuthRegalo({ children }: { children: JSX.Element }) {
  const { user, cargandoAuth } = useAuth();
  const loc = useLocation();
  if (cargandoAuth) return <div className="center-note">…</div>;
  if (!user) {
    try {
      sessionStorage.setItem(DESTINO_KEY, loc.pathname + loc.search);
    } catch {
      /* sessionStorage no disponible: se pierde el destino, no la sesión */
    }
    return <Navigate to="/login" replace />;
  }
  return children;
}

// Con sesión ya iniciada, retomar el destino guardado (el regalo) una sola vez.
function VolverAlDestino() {
  const { user } = useAuth();
  const loc = useLocation();
  const navigate = useNavigate();
  useEffect(() => {
    if (!user) return;
    // Ya estamos en el regalo (o volviendo al login): nada que retomar.
    if (loc.pathname.startsWith("/c/") || loc.pathname.startsWith("/login")) return;
    let destino: string | null = null;
    try {
      destino = sessionStorage.getItem(DESTINO_KEY);
      if (destino) sessionStorage.removeItem(DESTINO_KEY);
    } catch {
      /* ignorar */
    }
    if (destino) navigate(destino, { replace: true });
  }, [user, loc.pathname, navigate]);
  return null;
}

// El login con sesión activa no se muestra: cubre también el retorno del
// signInWithRedirect de Google.
function SoloAnonimo({ children }: { children: JSX.Element }) {
  const { user, cargandoAuth } = useAuth();
  // En dev el usuario sintético siempre existe: dejamos ver el Login igual.
  if (import.meta.env.DEV) return children;
  if (cargandoAuth) return <div className="center-note">…</div>;
  if (user) return <Navigate to="/" replace />;
  return children;
}

// Guarda de entrada: si el onboarding no está completo, va al onboarding.
function Gate() {
  const { perfil, loading } = useStore();
  if (loading) return <div className="center-note">…</div>;
  if (perfil?.onboarding_completo) return <Navigate to="/hoy" replace />;
  return <Navigate to="/onboarding" replace />;
}

function RequireOnboarding({ children }: { children: JSX.Element }) {
  const { perfil, loading } = useStore();
  const loc = useLocation();
  if (loading) return <div className="center-note">…</div>;
  if (!perfil?.onboarding_completo)
    return <Navigate to="/onboarding" replace state={{ from: loc.pathname }} />;
  return children;
}

// WS28 · B2.2 · El escritorio de Dwellia no es una pestaña ni una URL secreta:
// quien no es admin no lo ve. La verdad la tiene el backend (`perfil.es_admin`,
// que sale de MINDFUL_ADMIN_UIDS y responde 403 igual); acá solo se cierra la
// puerta para que nadie choque contra una pantalla vacía.
function RequireAdmin({ children }: { children: JSX.Element }) {
  const { perfil, loading } = useStore();
  if (loading || !perfil) return <div className="center-note">…</div>;
  if (!perfil.es_admin) return <Navigate to="/perfil" replace />;
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
      <StoreProvider>
        <Frame>
          <VolverAlDestino />
          <Routes>
            <Route path="/" element={<RequireAuth><Gate /></RequireAuth>} />
            <Route path="/login" element={<SoloAnonimo><Login /></SoloAnonimo>} />
            <Route path="/login/email" element={<LoginEmail />} />
            <Route path="/onboarding" element={<RequireAuth><Onboarding /></RequireAuth>} />

            <Route path="/hoy" element={<RequireAuth><RequireOnboarding><Home /></RequireOnboarding></RequireAuth>} />
            <Route path="/reflexionar/:id" element={<RequireAuth><RequireOnboarding><Reflect /></RequireOnboarding></RequireAuth>} />
            <Route path="/cierre/:id" element={<RequireAuth><RequireOnboarding><Completion /></RequireOnboarding></RequireAuth>} />
            <Route path="/baul" element={<RequireAuth><RequireOnboarding><Baul /></RequireOnboarding></RequireAuth>} />
            <Route path="/baul/:id" element={<RequireAuth><RequireOnboarding><EntryDetail /></RequireOnboarding></RequireAuth>} />
            <Route path="/compartir/:id" element={<RequireAuth><RequireOnboarding><Share /></RequireOnboarding></RequireAuth>} />
            <Route path="/perfil" element={<RequireAuth><RequireOnboarding><Profile /></RequireOnboarding></RequireAuth>} />
            <Route path="/metodo" element={<RequireAuth><RequireOnboarding><Metodo /></RequireOnboarding></RequireAuth>} />
            {/* WS24 · premium (Stripe por web). /premium/gracias = vuelta del Checkout. */}
            <Route path="/premium" element={<RequireAuth><RequireOnboarding><Premium /></RequireOnboarding></RequireAuth>} />
            <Route path="/premium/gracias" element={<RequireAuth><RequireOnboarding><PremiumGracias /></RequireOnboarding></RequireAuth>} />

            {/* WS27/28 · B2.2 · escribir cartas para la comunidad. El wizard sirve
                a la carta nueva y al reenvío de la que necesita un retoque. */}
            <Route path="/crear" element={<RequireAuth><RequireOnboarding><Crear /></RequireOnboarding></RequireAuth>} />
            <Route path="/crear/nueva" element={<RequireAuth><RequireOnboarding><CartaNueva /></RequireOnboarding></RequireAuth>} />
            <Route path="/crear/:id/editar" element={<RequireAuth><RequireOnboarding><CartaNueva /></RequireOnboarding></RequireAuth>} />
            <Route path="/avisos" element={<RequireAuth><RequireOnboarding><Avisos /></RequireOnboarding></RequireAuth>} />
            {/* El escritorio de Dwellia: solo `perfil.es_admin`. */}
            <Route path="/admin" element={<RequireAuth><RequireOnboarding><RequireAdmin><Admin /></RequireAdmin></RequireOnboarding></RequireAuth>} />

            {/* WS25 · el regalo exige login, pero no onboarding completo. */}
            <Route path="/c/:token" element={<RequireAuthRegalo><PublicShare /></RequireAuthRegalo>} />
            {/* Público: términos y privacidad (onboarding + Perfil enlazan acá). */}
            <Route path="/terminos" element={<Terms />} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Frame>
      </StoreProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

// PWA: capturar el prompt de instalación + registrar el service worker.
initInstallPrompt();
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

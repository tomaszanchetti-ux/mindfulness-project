import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";

import "./theme.css";
import "./app.css";

import { Frame } from "./components/Frame";
import { TourController } from "./components/TourController";
import { AuthProvider, useAuth } from "./auth";
import { StoreProvider, useStore } from "./store";
import { TutorialProvider } from "./tutorial";
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

// Guarda de sesión: sin usuario logueado, todo lo privado vuelve al login.
function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, cargandoAuth } = useAuth();
  if (cargandoAuth) return <div className="center-note">…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
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

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
      <StoreProvider>
        <TutorialProvider>
        <Frame>
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

            {/* Público: el receptor del regalo, sin login. */}
            <Route path="/c/:token" element={<PublicShare />} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <TourController />
        </Frame>
        </TutorialProvider>
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

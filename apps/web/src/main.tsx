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
import { StoreProvider, useStore } from "./store";

import { Login } from "./screens/Login";
import { Onboarding } from "./screens/Onboarding";
import { Home } from "./screens/Home";
import { Reflect } from "./screens/Reflect";
import { Completion } from "./screens/Completion";
import { Baul } from "./screens/Baul";
import { EntryDetail } from "./screens/EntryDetail";
import { Share } from "./screens/Share";
import { PublicShare } from "./screens/PublicShare";
import { Profile } from "./screens/Profile";

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
      <StoreProvider>
        <Frame>
          <Routes>
            <Route path="/" element={<Gate />} />
            <Route path="/login" element={<Login />} />
            <Route path="/onboarding" element={<Onboarding />} />

            <Route path="/hoy" element={<RequireOnboarding><Home /></RequireOnboarding>} />
            <Route path="/reflexionar/:id" element={<RequireOnboarding><Reflect /></RequireOnboarding>} />
            <Route path="/cierre/:id" element={<RequireOnboarding><Completion /></RequireOnboarding>} />
            <Route path="/baul" element={<RequireOnboarding><Baul /></RequireOnboarding>} />
            <Route path="/baul/:id" element={<RequireOnboarding><EntryDetail /></RequireOnboarding>} />
            <Route path="/compartir/:id" element={<RequireOnboarding><Share /></RequireOnboarding>} />
            <Route path="/perfil" element={<RequireOnboarding><Profile /></RequireOnboarding>} />

            {/* Público: el receptor del regalo, sin login. */}
            <Route path="/c/:token" element={<PublicShare />} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Frame>
      </StoreProvider>
    </BrowserRouter>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

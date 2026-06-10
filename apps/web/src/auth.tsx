// Estado de autenticación. En producción escucha Firebase (onAuthStateChanged);
// en dev (vite dev) corto-circuito con un usuario sintético — la identidad real
// la resuelve la API por los headers X-Debug-* (ver lib/api.ts).

import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { onAuthStateChanged } from "firebase/auth";
import { auth, completarRedirect } from "./lib/firebase";

export interface UsuarioAuth {
  uid: string;
  email: string | null;
}

interface AuthState {
  user: UsuarioAuth | null;
  cargandoAuth: boolean;
}

const DEV = import.meta.env.DEV;
const USER_DEV: UsuarioAuth = { uid: "dev|user", email: "demo@dwellia.local" };

const Ctx = createContext<AuthState>({ user: null, cargandoAuth: true });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UsuarioAuth | null>(DEV ? USER_DEV : null);
  const [cargandoAuth, setCargandoAuth] = useState(!DEV);

  useEffect(() => {
    if (DEV) return;
    // Cierra un posible retorno de signInWithRedirect antes de fiarnos del estado.
    completarRedirect();
    return onAuthStateChanged(auth, (u) => {
      setUser(u ? { uid: u.uid, email: u.email } : null);
      setCargandoAuth(false);
    });
  }, []);

  return <Ctx.Provider value={{ user, cargandoAuth }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  return useContext(Ctx);
}

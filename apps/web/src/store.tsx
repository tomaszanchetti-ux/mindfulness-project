// Estado liviano compartido: el perfil del usuario + el catálogo de pilares
// (contenido global). Suficiente para el prototipo; sin librería de estado.
// WS23: el catálogo de acciones ya no se carga — la carta trae su acción en el
// payload y el usuario no elige nada (canon WS22).

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useAuth } from "./auth";
import { api } from "./lib/api";
import type { CategoriaContenido, Perfil } from "./lib/types";

interface Store {
  perfil: Perfil | null;
  categorias: CategoriaContenido[];
  loading: boolean;
  refrescarPerfil: () => Promise<Perfil | null>;
}

const Ctx = createContext<Store | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const { user, cargandoAuth } = useAuth();
  const [perfil, setPerfil] = useState<Perfil | null>(null);
  const [categorias, setCategorias] = useState<CategoriaContenido[]>([]);
  const [loading, setLoading] = useState(true);

  const refrescarPerfil = useCallback(async () => {
    try {
      const p = await api.perfil();
      setPerfil(p);
      return p;
    } catch {
      setPerfil(null);
      return null;
    }
  }, []);

  // El perfil se carga (y recarga) por usuario logueado; sin sesión no hay nada
  // que pedir — las rutas privadas quedan detrás de RequireAuth.
  useEffect(() => {
    if (cargandoAuth) return;
    if (!user) {
      setPerfil(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    (async () => {
      const [, cats] = await Promise.all([
        refrescarPerfil(),
        api.categorias().catch(() => [] as CategoriaContenido[]),
      ]);
      setCategorias(cats);
      setLoading(false);
    })();
  }, [refrescarPerfil, user?.uid, cargandoAuth]);

  return (
    <Ctx.Provider value={{ perfil, categorias, loading, refrescarPerfil }}>
      {children}
    </Ctx.Provider>
  );
}

export function useStore(): Store {
  const v = useContext(Ctx);
  if (!v) throw new Error("useStore fuera de StoreProvider");
  return v;
}

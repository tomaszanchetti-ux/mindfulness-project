// Cliente de la API. En local pega a /api (Vite lo proxea a :8000).
//
// Modo dev: la API auto-provisiona el usuario `dev|user` por los headers X-Debug-*.
// Cuando exista Firebase (front Expo), esto se reemplaza por el ID token en
// Authorization: Bearer <token> — el resto del contrato no cambia.

import type {
  CartaDelDia,
  CategoriaContenido,
  Compartido,
  ItemBaul,
  Perfil,
  Regalo,
} from "./types";

const DEV_HEADERS: Record<string, string> = {
  "X-Debug-Sub": "dev|user",
  "X-Debug-Email": "dev@mindful.local",
};

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...DEV_HEADERS,
      ...(init.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* sin cuerpo JSON */
    }
    const err = new Error(detail) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  // —— Contenido global (Mundo 1) ——
  categorias: () => req<CategoriaContenido[]>("/api/contenido/categorias"),

  // —— Perfil / onboarding (M1) ——
  perfil: () => req<Perfil>("/api/perfil"),
  setCategorias: (categorias: string[]) =>
    req<Perfil>("/api/perfil/categorias", {
      method: "PUT",
      body: JSON.stringify({ categorias }),
    }),
  setPerfil: (body: Partial<{
    nombre: string;
    apellido: string;
    apodo: string;
    tz: string;
    hora_aviso: string;
    aviso_activo: boolean;
    aceptar_terminos: boolean;
  }>) =>
    req<Perfil>("/api/perfil", {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  // —— Carta del día + cierre del ritual (M2 / M3) ——
  cartaDelDia: () => req<CartaDelDia>("/api/carta-del-dia"),
  cerrarRitual: (
    entregaId: string,
    body: { estrellas?: number | null; reflexion?: string | null; completada?: boolean },
  ) =>
    req<CartaDelDia>(`/api/entregas/${entregaId}/cierre`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),

  // —— Baúl (M4) ——
  baul: (orden: "reciente" | "valoradas" = "reciente") =>
    req<ItemBaul[]>(`/api/baul?orden=${orden}`),
  borrarEntrada: (entregaId: string) =>
    req<void>(`/api/baul/${entregaId}`, { method: "DELETE" }),

  // —— Compartir (M5) ——
  compartir: (entregaId: string, modo: "carta_sola" | "ejercicio", nota?: string) =>
    req<Compartido>("/api/compartir", {
      method: "POST",
      body: JSON.stringify({ entrega_id: entregaId, modo, nota: nota || null }),
    }),

  // —— Regalo público (sin login) ——
  regalo: (token: string) => req<Regalo>(`/api/c/${token}`),
};

// Las imágenes/glifos viven en /public/assets (copiados de M0). La API guarda
// la ruta relativa "assets/..."; acá la resolvemos a la raíz del sitio.
export function assetUrl(path: string): string {
  if (!path) return "";
  return path.startsWith("/") ? path : `/${path}`;
}

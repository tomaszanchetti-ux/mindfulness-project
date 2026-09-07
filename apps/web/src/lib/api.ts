// Cliente de la API. En local pega a /api (Vite lo proxea a :8000).
//
// Identidad:
//  - dev (vite dev): la API auto-provisiona un usuario efímero por X-Debug-*.
//  - producción: Firebase ID token en Authorization: Bearer <token>.

import { auth, cerrarSesion } from "./firebase";

import type {
  AccionContenido,
  BandejaAvisos,
  BaulAjeno,
  FichaAjena,
  ItemFicha,
  ItemRecomendacion,
  MiComunidad,
  ModoPausa,
  PausaHecha,
  Persona,
  RecomendacionBody,
  ReenviosRecibidos,
  CartaDelDia as EntregaCompleta,
  CartaDelDia,
  CartaPropuesta,
  CartaPropuestaBody,
  CategoriaContenido,
  ComentarioAdmin,
  Compartido,
  EstadoPagos,
  FiltroAdmin,
  FotoSubida,
  ItemBaul,
  MatrizViable,
  Perfil,
  PropuestaAdmin,
  Regalo,
  ResumenAdmin,
  SugerenciaCarta,
  Visibilidad,
} from "./types";

// —— Identidad efímera por sesión (SOLO dev) ——
// En vite dev cada apertura genera un usuario nuevo (`demo|<uuid>`), aislado, para
// probar el funnel desde cero. Vive en sessionStorage: un refresh no corta la
// prueba, reabrir arranca de nuevo. En producción la identidad es Firebase.
const DEV = import.meta.env.DEV;
const SUB_KEY = "dwellia-demo-sub";

function nuevoSub(): string {
  const rnd =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Math.random().toString(36).slice(2)}${Math.random().toString(36).slice(2)}`;
  return `demo|${rnd}`;
}

function demoSub(): string {
  try {
    let sub = sessionStorage.getItem(SUB_KEY);
    if (!sub) {
      sub = nuevoSub();
      sessionStorage.setItem(SUB_KEY, sub);
    }
    return sub;
  } catch {
    // sessionStorage no disponible (modo privado raro): identidad por carga.
    return nuevoSub();
  }
}

// Borra la identidad de demo y recarga: arranca un funnel completamente nuevo.
export function reiniciarDemo(): void {
  try {
    sessionStorage.removeItem(SUB_KEY);
  } catch {
    /* ignorar */
  }
  window.location.href = "/";
}

// Headers de identidad. En dev: X-Debug-*. En prod: Bearer con el ID token de
// Firebase (el SDK lo cachea y refresca solo). Sin usuario (página pública
// /c/:token) la request va sin Authorization.
async function authHeaders(forzarRefresh = false): Promise<Record<string, string>> {
  if (DEV) {
    return { "X-Debug-Sub": demoSub(), "X-Debug-Email": "demo@dwellia.local" };
  }
  const user = auth.currentUser;
  if (!user) return {};
  return { Authorization: `Bearer ${await user.getIdToken(forzarRefresh)}` };
}

async function hacerFetch(
  path: string,
  init: RequestInit,
  forzarRefresh: boolean,
): Promise<Response> {
  // Con FormData el navegador pone solo el Content-Type multipart (con boundary).
  const esForm = init.body instanceof FormData;
  return fetch(path, {
    ...init,
    headers: {
      ...(esForm ? {} : { "Content-Type": "application/json" }),
      ...(await authHeaders(forzarRefresh)),
      ...(init.headers || {}),
    },
  });
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res = await hacerFetch(path, init, false);
  // 401 en prod con sesión: un reintento con token refrescado a la fuerza;
  // si persiste, la sesión ya no vale → cerrar y volver al login.
  if (res.status === 401 && !DEV && auth.currentUser) {
    res = await hacerFetch(path, init, true);
    if (res.status === 401) {
      await cerrarSesion().catch(() => {});
      window.location.href = "/login";
    }
  }
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
  // WS27 · B2.2 · las 4 acciones iniciales: el paso 2 del wizard de Crear.
  acciones: () => req<AccionContenido[]>("/api/contenido/acciones"),
  // WS28 · qué acciones combinan con cada pilar (canon R8.1): filtra el paso 2 del wizard.
  matriz: () => req<MatrizViable>("/api/contenido/matriz"),

  // —— Perfil / onboarding (M1) ——
  perfil: () => req<Perfil>("/api/perfil"),
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
    body: {
      estrellas?: number | null;
      reflexion?: string | null;
      comentario_carta?: string | null; // WS24: feedback privado debajo de las estrellas
      completada?: boolean;
    },
  ) =>
    req<CartaDelDia>(`/api/entregas/${entregaId}/cierre`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  // WS24 · A1.3 · cambiar la carta de hoy (premium, hasta `limites.cambios_carta` veces).
  // Errores: 403 free · 409 ya cerrada / sin cambios restantes / no es la de hoy.
  cambiarCarta: (entregaId: string) =>
    req<CartaDelDia>(`/api/entregas/${entregaId}/cambiar`, { method: "POST" }),

  // —— Pagos (WS24 · A1.2 · Stripe por web, sin tiendas) ——
  pagosEstado: () => req<EstadoPagos>("/api/pagos/estado"),
  // Devuelven la URL de Stripe a la que hay que redirigir (window.location.href).
  pagosCheckout: () => req<{ url: string }>("/api/pagos/checkout", { method: "POST" }),
  pagosPortal: () => req<{ url: string }>("/api/pagos/portal", { method: "POST" }),

  // —— Fotos de la pausa (M3 captura / M4 muestra) ——
  subirFoto: (entregaId: string, file: File) => {
    const fd = new FormData();
    fd.append("foto", file);
    return req<FotoSubida>(`/api/entregas/${entregaId}/fotos`, {
      method: "POST",
      body: fd,
    });
  },
  borrarFoto: (fotoId: string) =>
    req<void>(`/api/fotos/${fotoId}`, { method: "DELETE" }),

  // —— Baúl (M4) ——
  baul: (orden: "reciente" | "valoradas" = "reciente") =>
    req<ItemBaul[]>(`/api/baul?orden=${orden}`),
  borrarEntrada: (entregaId: string) =>
    req<void>(`/api/baul/${entregaId}`, { method: "DELETE" }),
  // WS25 · abrir/cerrar la ficha a la comunidad. Devuelve el ítem ya actualizado.
  setVisibilidad: (entregaId: string, visibilidad: Visibilidad) =>
    req<ItemBaul>(`/api/baul/${entregaId}/visibilidad`, {
      method: "PUT",
      body: JSON.stringify({ visibilidad }),
    }),

  // —— Compartir (M5) ——
  // WS25 · viaja la ficha entera tal como está: el backend deriva el modo
  // (`ejercicio` si hay reflexión o fotos, `carta_sola` si no) y ya no mira el plan.
  compartir: (entregaId: string, nota?: string) =>
    req<Compartido>("/api/compartir", {
      method: "POST",
      body: JSON.stringify({ entrega_id: entregaId, nota: nota || null }),
    }),

  // —— Push del aviso diario (WS21) ——
  pushSuscribir: (body: { endpoint: string; p256dh: string; auth: string }) =>
    req<{ ok: boolean }>("/api/push/suscripcion", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  pushBaja: (endpoint: string) =>
    req<{ ok: boolean }>("/api/push/baja", {
      method: "POST",
      body: JSON.stringify({ endpoint }),
    }),

  // —— Regalo por enlace (WS25: también exige login) ——
  regalo: (token: string) => req<Regalo>(`/api/c/${token}`),

  // ———————————————————————————————————————————————————————————————————————
  // WS27 · B2.2 · Cartas de la comunidad (pestaña Crear)
  // Los errores llegan en español desde el backend (422 contenido · 403 free ·
  // 409 "ya tienes una en curso"): se muestran TAL CUAL, sin traducirlos acá.
  // ———————————————————————————————————————————————————————————————————————
  cartasMias: () => req<CartaPropuesta[]>("/api/cartas-comunidad/mias"),
  proponerCarta: (body: CartaPropuestaBody) =>
    req<CartaPropuesta>("/api/cartas-comunidad", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  // Reenviar una carta que necesita un retoque (solo desde `a_revisar`).
  // La cesión NO se vuelve a pedir: se aceptó al proponerla.
  reenviarCarta: (id: string, body: CartaPropuestaBody) =>
    req<CartaPropuesta>(`/api/cartas-comunidad/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  retirarCarta: (id: string) =>
    req<void>(`/api/cartas-comunidad/${id}`, { method: "DELETE" }),

  // —— Avisos (la campana) ——
  avisos: () => req<BandejaAvisos>("/api/avisos"),
  avisoLeido: (id: string) =>
    req<{ id: string; leido: boolean }>(`/api/avisos/${id}/leido`, { method: "PUT" }),
  avisosLeidos: () =>
    req<{ marcados: number; no_leidos: number }>("/api/avisos/leidos", { method: "PUT" }),

  // ———————————————————————————————————————————————————————————————————————
  // WS27 · B2.2 · Adminland (403 si el uid no está en MINDFUL_ADMIN_UIDS)
  // ———————————————————————————————————————————————————————————————————————
  adminResumen: () => req<ResumenAdmin>("/api/admin/resumen"),
  adminCartas: (estado: FiltroAdmin) =>
    req<PropuestaAdmin[]>(`/api/admin/cartas?estado=${estado}`),
  adminAprobar: (id: string, concepto?: string) =>
    req<PropuestaAdmin>(`/api/admin/cartas/${id}/aprobar`, {
      method: "POST",
      body: JSON.stringify({ concepto: concepto || null }),
    }),
  adminRechazar: (id: string, motivo: string) =>
    req<PropuestaAdmin>(`/api/admin/cartas/${id}/rechazar`, {
      method: "POST",
      body: JSON.stringify({ motivo }),
    }),
  // `fix` es opcional: sin él se conserva la sugerencia que ya había escrito el juez.
  adminARevisar: (id: string, sugerencia: string, fix?: SugerenciaCarta | null) =>
    req<PropuestaAdmin>(`/api/admin/cartas/${id}/a-revisar`, {
      method: "POST",
      body: JSON.stringify({ sugerencia, fix: fix || null }),
    }),
  adminComentarios: (limit = 500) =>
    req<ComentarioAdmin[]>(`/api/admin/comentarios?limit=${limit}`),

  // ————————————————————————————————————————————————————————————————————————
  // WS29 · Bloque C · Comunidad (contrato en WS/WS29 §4). Los agentes de C1
  // implementan estos endpoints; los de C2 los consumen desde acá.
  // ————————————————————————————————————————————————————————————————————————

  // —— C1.1 · personas, solicitudes, foto de perfil ——
  buscarPersonas: (q: string) =>
    req<Persona[]>(`/api/comunidad/buscar?q=${encodeURIComponent(q)}`),
  miComunidad: () => req<MiComunidad>("/api/comunidad"),
  pedirVinculo: (usuarioId: string) =>
    req<Persona>(`/api/comunidad/solicitudes/${usuarioId}`, { method: "POST" }),
  aceptarVinculo: (usuarioId: string) =>
    req<Persona>(`/api/comunidad/solicitudes/${usuarioId}/aceptar`, { method: "POST" }),
  // Rechazar (si me la mandaron) o cancelar (si la mandé yo): la misma puerta.
  descartarSolicitud: (usuarioId: string) =>
    req<void>(`/api/comunidad/solicitudes/${usuarioId}`, { method: "DELETE" }),
  quitarDeMiComunidad: (usuarioId: string) =>
    req<void>(`/api/comunidad/${usuarioId}`, { method: "DELETE" }),
  subirFotoPerfil: (file: File) => {
    const fd = new FormData();
    fd.append("foto", file);
    return req<{ foto_url: string }>("/api/perfil/foto", { method: "POST", body: fd });
  },
  quitarFotoPerfil: () => req<void>("/api/perfil/foto", { method: "DELETE" }),

  // —— C1.2 · fichas ajenas, descubrir, reenviar, guardar, hacer la Pausa ——
  descubrir: () => req<FichaAjena[]>("/api/fichas/descubrir"),
  baulDe: (usuarioId: string) => req<BaulAjeno>(`/api/fichas/de/${usuarioId}`),
  fichaAjena: (entregaId: string) => req<FichaAjena>(`/api/fichas/${entregaId}`),
  reenviar: (entregaId: string, aUsuarioId: string) =>
    req<{ id: string }>("/api/reenvios", {
      method: "POST",
      body: JSON.stringify({ entrega_id: entregaId, a_usuario_id: aUsuarioId }),
    }),
  reenviosRecibidos: () => req<ReenviosRecibidos>("/api/reenvios/recibidos"),
  reenvioLeido: (id: string) => req<void>(`/api/reenvios/${id}/leido`, { method: "PUT" }),
  guardarFicha: (entregaId: string) =>
    req<void>(`/api/guardadas/${entregaId}`, { method: "POST" }),
  quitarGuardada: (entregaId: string) =>
    req<void>(`/api/guardadas/${entregaId}`, { method: "DELETE" }),
  hacerPausa: (entregaId: string, modo: ModoPausa) =>
    req<PausaHecha>("/api/pausas/hacer", {
      method: "POST",
      body: JSON.stringify({ entrega_id: entregaId, modo }),
    }),
  // Una entrega MÍA por id (la Pausa extra en /pausa/:id). Misma forma que la carta del día.
  entrega: (entregaId: string) => req<EntregaCompleta>(`/api/entregas/${entregaId}`),

  // —— C1.3 · recomendaciones (premium) ——
  // El Baúl propio devuelve Pausas y recomendaciones mezcladas (ItemFicha).
  baulCompleto: (orden: "reciente" | "valoradas" = "reciente") =>
    req<ItemFicha[]>(`/api/baul?orden=${orden}`),
  recomendaciones: () => req<ItemRecomendacion[]>("/api/recomendaciones"),
  crearRecomendacion: (body: RecomendacionBody) =>
    req<ItemRecomendacion>("/api/recomendaciones", { method: "POST", body: JSON.stringify(body) }),
  editarRecomendacion: (id: string, body: Partial<RecomendacionBody>) =>
    req<ItemRecomendacion>(`/api/recomendaciones/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  borrarRecomendacion: (id: string) =>
    req<void>(`/api/recomendaciones/${id}`, { method: "DELETE" }),
  setVisibilidadRecomendacion: (id: string, visibilidad: Visibilidad) =>
    req<ItemRecomendacion>(`/api/recomendaciones/${id}/visibilidad`, {
      method: "PUT",
      body: JSON.stringify({ visibilidad }),
    }),
};

// Las imágenes/glifos viven en /public/assets (copiados de M0). La API guarda
// la ruta relativa "assets/..."; acá la resolvemos a la raíz del sitio.
export function assetUrl(path: string): string {
  if (!path) return "";
  return path.startsWith("/") ? path : `/${path}`;
}

// —— Fotos privadas ——
// Un <img> no puede mandar el Bearer/X-Debug, así que la imagen se baja con
// fetch autenticado y se sirve como object URL. Cache por sesión de página.
const fotoCache = new Map<string, Promise<string>>();

export function fotoPrivadaUrl(url: string): Promise<string> {
  let p = fotoCache.get(url);
  if (!p) {
    p = (async () => {
      const res = await fetch(url, { headers: await authHeaders() });
      if (!res.ok) throw new Error("No pudimos cargar la foto");
      return URL.createObjectURL(await res.blob());
    })();
    fotoCache.set(url, p);
    p.catch(() => fotoCache.delete(url));
  }
  return p;
}

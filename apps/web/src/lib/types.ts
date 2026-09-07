// Tipos espejo de los contratos de la API (apps/api/mindful_api).

export interface CategoriaContenido {
  slug: string;
  nombre: string;
  color_accent: string;
  color_text: string;
  img: string;
}

export interface CategoriaCarta {
  slug: string;
  nombre: string;
  color_accent: string;
  color_text: string;
  img: string;
}

export interface AccionCarta {
  slug: string;
  nombre: string;
  glifo: string; // ruta a un .svg (assets/acciones/...)
}

// Catálogo de actividades global (Mundo 1), para elegir en onboarding/perfil.
export interface AccionContenido {
  slug: string;
  nombre: string;
  glifo: string;
}

export interface Carta {
  id: string;
  frase: string;
  prompt: string;
  categoria: CategoriaCarta;
  accion: AccionCarta;
  // WS27 · B0: de dónde viene y quién la firma (null = de Dwellia o anónima).
  origen?: "dwellia" | "comunidad";
  firma_publica?: string | null;
}

export interface Entrega {
  id: string;
  fecha: string; // ISO
  estrellas: number | null;
  completada: boolean;
  reflexion: string | null;
  comentario_carta?: string | null; // WS24: feedback privado de la carta (nunca se publica)
  cambios?: number; // WS24: veces que cambió la carta hoy (restantes = limites.cambios_carta - cambios)
  ya_existia?: boolean;
}

export interface CartaDelDia {
  entrega: Entrega;
  carta: Carta;
  // WS24 · A1.3: presentes en la respuesta de POST /api/entregas/{id}/cambiar
  cambios?: number;
  cambios_restantes?: number;
}

// WS24 · lo que el usuario puede hacer según su plan. El backend los aplica;
// el front SOLO los muestra (nunca hardcodear 150 / 1 foto en pantalla).
export interface Limites {
  plan: "free" | "premium";
  reflexion_max: number;
  fotos_max: number;
  cambios_carta: number;
  propone_cartas: boolean;
  recomendaciones: boolean;
}

// WS24 · A1.2 · GET /api/pagos/estado
export interface EstadoPagos {
  plan: "free" | "premium";
  plan_hasta: string | null;
  configurado: boolean; // false = Stripe apagado en este entorno (sin botón de compra)
}

// WS25 · quién ve la ficha además de su dueño. "compartida" = visible para la
// comunidad del usuario; "privada" = sólo él. Las estrellas nunca viajan.
export type Visibilidad = "privada" | "compartida";

export interface ItemBaul {
  id: string;
  fecha: string;
  estrellas: number | null;
  completada: boolean;
  reflexion: string | null;
  fotos: string[]; // URLs de la API (/api/fotos/{id}) — privadas, se piden con auth
  carta: Carta;
  visibilidad: Visibilidad; // WS25 · PUT /api/baul/{id}/visibilidad
}

// Respuesta al subir una foto de la pausa (hasta 3 por entrega).
export interface FotoSubida {
  id: string;
  url: string;
}

export interface Perfil {
  email: string;
  nombre: string | null;
  apellido: string | null;
  apodo: string | null;
  tz: string;
  hora_aviso: string;
  aviso_activo: boolean;
  terminos_aceptados: boolean;
  onboarding_completo: boolean;
  // WS24 · plan vigente (premium vencido ⇒ "free") y sus límites.
  plan: "free" | "premium";
  plan_hasta: string | null;
  limites: Limites;
  // WS27 · B2 · si esta cuenta entra al adminland (MINDFUL_ADMIN_UIDS).
  // El backend lo resuelve; el front solo muestra u oculta la puerta.
  es_admin: boolean;
}

export interface Compartido {
  token: string;
  url: string;
  modo: "carta_sola" | "ejercicio";
}

export interface Regalo {
  modo: "carta_sola" | "ejercicio";
  nota: string | null;
  de: string | null; // apodo del remitente
  carta: Carta;
  reflexion?: string | null;
  fotos?: string[];
}

// ─────────────────────────────────────────────────────────────────────────────
// WS27 · B2.2 · Cartas de la comunidad (pestaña Crear), avisos y adminland.
// Espejo de `services/cartas_comunidad.py`, `services/avisos.py` y
// `services/admin.py`. El vocabulario de estados es CERRADO (db/models.py): si
// mañana nace uno nuevo, TypeScript avisa acá antes que el usuario en pantalla.
// ─────────────────────────────────────────────────────────────────────────────

export type EstadoPropuesta =
  | "en_revision"        // el juez la está mirando
  | "revision_dwellia"   // le toca a Dwellia
  | "a_revisar"          // vuelve al autor con una sugerencia
  | "aprobada"           // cargada al mazo
  | "rechazada"
  | "retirada";          // la bajó el autor

// Los tres estados en los que la carta todavía está "en curso": mientras haya
// una así, el autor no puede escribir otra (el backend responde 409).
export const ESTADOS_EN_CURSO: EstadoPropuesta[] = [
  "en_revision",
  "revision_dwellia",
  "a_revisar",
];

export type FirmaCarta = "anonima" | "apodo";

/** El retoque concreto: frase y/o prompt reescritos (`fix_sugerido`). */
export interface SugerenciaCarta {
  frase: string | null;
  prompt: string | null;
}

/** Una carta propuesta, como la ve SU AUTOR en la pestaña Crear. */
export interface CartaPropuesta {
  id: string;
  estado: EstadoPropuesta;
  firma: FirmaCarta;
  motivo: string | null;       // lo que se le explica al autor (a_revisar / rechazada)
  sugerencia: SugerenciaCarta | null;
  concepto: string | null;
  carta_id: string | null;     // la carta publicada, si se aprobó
  personas_acompanadas: number;
  // WS28 · B2.2 · cómo le fue: promedio de estrellas a 1 decimal (null si nadie
  // la puntuó todavía) y cuántas Pausas la puntuaron.
  estrellas_promedio: number | null;
  veces_puntuada: number;
  created_at: string;
  updated_at: string;
  carta: Carta;                // ya enriquecida: se dibuja con <Card>
}

/** Lo que manda el wizard (POST) o el reenvío (PUT). */
export interface CartaPropuestaBody {
  categoria: string;
  accion: string;
  frase: string;
  prompt: string;
  firma: FirmaCarta;
  cesion_aceptada?: boolean; // solo al proponer; el reenvío no la vuelve a pedir
}

// —— Avisos (la campana) ——
export interface Aviso {
  id: string;
  tipo: string;
  referencia_id: string | null;
  texto: string;
  leido: boolean;
  created_at: string;
}

export interface BandejaAvisos {
  no_leidos: number;
  avisos: Aviso[];
}

// ─────────────────────────────────────────────────────────────────────────────
// Adminland (solo `perfil.es_admin`)
// ─────────────────────────────────────────────────────────────────────────────

/** Un incumplimiento del canon marcado por el juez. `mayor` = R1-R5 y S. */
export interface Hallazgo {
  regla: string;
  mayor: boolean;
  detalle: string;
}

/** El veredicto CRUDO. Lo escribe un modelo: todo es opcional a propósito. */
export interface Veredicto {
  resultado?: string | null;
  hallazgos?: Hallazgo[] | null;
  concepto?: string | null;
  fix_sugerido?: SugerenciaCarta | null;
  motivo?: string | null;
  fuente?: string | null; // "juez" | "dwellia"
  anterior?: Veredicto | null;
}

/** El mismo veredicto ya masticado por el backend para dibujar la columna v2. */
export interface VeredictoResumen {
  resultado: string | null;
  motivo: string | null;
  fix: SugerenciaCarta | null;
  fuente: string | null;
  hallazgos: number;
}

/** Una vuelta del funnel: la carta tal como se escribió (o se reenvió). */
export interface Redaccion {
  version: number;
  frase: string;
  prompt: string;
  categoria: string;
  accion: string;
  firma: string;
  fecha: string;
  por: string;
}

/** Una propuesta vista desde el escritorio de Dwellia. */
export interface PropuestaAdmin {
  id: string;
  estado: EstadoPropuesta;
  firma: FirmaCarta;
  motivo: string | null;
  concepto: string | null;
  veredicto: Veredicto | null;
  veredicto_resumen: VeredictoResumen | null;
  historial: Redaccion[];
  carta_id: string | null;
  created_at: string;
  updated_at: string;
  autor: { apodo: string | null; email: string | null; nombre: string | null };
  carta: Carta;
}

/** Filtros de la cola. `pendientes` = en_revision + revision_dwellia. */
export type FiltroAdmin = "pendientes" | "a_revisar" | "aprobada" | "rechazada";

export interface ResumenPilar {
  slug: string;
  nombre: string;
  total: number;
  dwellia: number;
  comunidad: number;
}

/** El termómetro (`GET /api/admin/resumen`). */
export interface ResumenAdmin {
  cartas: {
    total: number;
    dwellia: number;
    comunidad: number;
    por_pilar: ResumenPilar[];
  };
  propuestas: Record<string, number>; // los 6 estados + "pendientes"
  usuarios: {
    total: number;
    con_onboarding: number;
    premium: number;
    free: number;
    crearon_cartas: number;
    sin_cartas: number;
  };
  comentarios: { total: number; ultimos_7_dias: number };
}

/** El feedback privado de una carta (debajo de las estrellas). Sin email. */
export interface ComentarioAdmin {
  entrega_id: string;
  fecha: string;
  estrellas: number | null;
  comentario: string;
  carta_id: string;
  frase: string;
  categoria: string; // slug del pilar (el color lo pone el catálogo del store)
  apodo: string | null;
}

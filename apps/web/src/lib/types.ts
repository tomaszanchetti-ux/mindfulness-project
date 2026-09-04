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
}

export interface Entrega {
  id: string;
  fecha: string; // ISO
  estrellas: number | null;
  completada: boolean;
  reflexion: string | null;
  comentario_carta?: string | null; // WS24: feedback privado de la carta (nunca se publica)
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
  compartir_ejercicio: boolean;
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

export interface ItemBaul {
  id: string;
  fecha: string;
  estrellas: number | null;
  completada: boolean;
  reflexion: string | null;
  fotos: string[]; // URLs de la API (/api/fotos/{id}) — privadas, se piden con auth
  carta: Carta;
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

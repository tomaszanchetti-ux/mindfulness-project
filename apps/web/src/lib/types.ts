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
  ya_existia?: boolean;
}

export interface CartaDelDia {
  entrega: Entrega;
  carta: Carta;
}

export interface ItemBaul {
  id: string;
  fecha: string;
  estrellas: number | null;
  completada: boolean;
  reflexion: string | null;
  fotos: string[];
  carta: Carta;
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
  categorias: string[];
  onboarding_completo: boolean;
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

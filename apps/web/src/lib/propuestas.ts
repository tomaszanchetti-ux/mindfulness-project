// WS27 · B2.2 · Los RÓTULOS visibles de una carta propuesta.
//
// El backend habla en estados (`en_revision`, `revision_dwellia`…); el usuario
// lee frases. La traducción vive acá, en un solo lugar, porque la usan tanto la
// pestaña Crear como el adminland — y porque el roadmap v2 §4 fija estos cuatro
// rótulos, no cinco ni unos parecidos.
//
//   en_revision / revision_dwellia → "En proceso de evaluación"  (gris)
//   aprobada                       → "Cargado a la comunidad"    (verde Dwellia)
//   a_revisar                      → "Necesita un retoque"       (ámbar suave)
//   rechazada                      → "No aprobada"               (rojo suave)
//   retirada                       → "Retirada"                  (gris claro)
//
// Para el AUTOR, `en_revision` y `revision_dwellia` son lo mismo a propósito: que
// la carta esté con el juez o con Dwellia es asunto nuestro, no suyo.

import type { EstadoPropuesta } from "./types";
import { ESTADOS_EN_CURSO } from "./types";

/** El tono de la píldora. Cada uno tiene su clase en app.css (`.pill-estado.es-*`). */
export type TonoEstado = "gris" | "verde" | "ambar" | "rojo" | "tenue";

export interface RotuloEstado {
  texto: string;
  tono: TonoEstado;
}

const ROTULOS: Record<EstadoPropuesta, RotuloEstado> = {
  en_revision: { texto: "En proceso de evaluación", tono: "gris" },
  revision_dwellia: { texto: "En proceso de evaluación", tono: "gris" },
  aprobada: { texto: "Cargado a la comunidad", tono: "verde" },
  a_revisar: { texto: "Necesita un retoque", tono: "ambar" },
  rechazada: { texto: "No aprobada", tono: "rojo" },
  retirada: { texto: "Retirada", tono: "tenue" },
};

export function rotulo(estado: EstadoPropuesta): RotuloEstado {
  // Un estado que no conocemos no puede dejar la píldora en blanco: se muestra
  // tal cual vino, en gris, y el problema se ve en pantalla en vez de esconderse.
  return ROTULOS[estado] ?? { texto: estado, tono: "gris" };
}

/** ¿La carta sigue su recorrido? Mientras haya una así, no se escribe otra. */
export function enCurso(estado: EstadoPropuesta): boolean {
  return ESTADOS_EN_CURSO.includes(estado);
}

/** "3 personas la recibieron" · el cero se dice en cristiano, no como "0". */
export function impacto(personas: number): string {
  if (personas <= 0) return "Todavía nadie la recibió.";
  if (personas === 1) return "1 persona la recibió.";
  return `${personas} personas la recibieron.`;
}

/**
 * "★ 4,5 · 3 valoraciones" · cómo le fue a una carta que ya está en el mazo.
 *
 * El promedio llega del backend con un decimal y se escribe con COMA, que es
 * como se lee un número en español. Sin nadie que la haya puntuado no se dibuja
 * un "★ 0,0": se dice que todavía nadie la puntuó, que es otra cosa.
 */
export function textoPuntaje(promedio: number | null, veces: number): string {
  if (promedio === null || veces <= 0) return "Todavía nadie la puntuó.";
  const nota = promedio.toFixed(1).replace(".", ",");
  return `★ ${nota} · ${veces === 1 ? "1 valoración" : `${veces} valoraciones`}`;
}

/** Cómo salió firmada (lo que lee la comunidad en el dorso). */
export function textoFirma(firma: string, apodo: string | null): string {
  if (firma === "apodo" && apodo) return `Firmada como ${apodo}.`;
  if (firma === "apodo") return "Firmada con tu apodo.";
  return "Firmada como alguien de la comunidad.";
}

// —— Los límites del contenido (Roadmap v2 §0). El backend los aplica igual: acá
// solo se usan para el contador y para no dejar mandar algo que va a rebotar. ——
export const FRASE_MAX = 40;   // WS28 · Tomás: más de 50 ya es mucho
export const PROMPT_MIN = 100;
export const PROMPT_MAX = 150; // WS28 · Tomás

// WS28 · B2.2b · Piezas compartidas por los tres bloques del escritorio.
//
// Todo lo de acá es defensivo a propósito: el adminland lee datos que escribió
// un modelo (el veredicto), una migración o un seed a mano. Un campo en null no
// puede dejar la pantalla en blanco — tiene que verse que falta.

import { assetUrl } from "../../lib/api";
import type { AccionCarta, Carta, CategoriaCarta } from "../../lib/types";

/** 403 = este uid no está en la lista de Dwellia. */
export function es403(e: unknown): boolean {
  return (e as { status?: number } | null)?.status === 403;
}

/** El error del backend, tal cual (ya viene en español). */
export function mensaje(e: unknown): string {
  const m = (e as Error | null)?.message;
  return m || "Algo no salió bien. Vuelve a intentarlo.";
}

export interface PilarVista {
  nombre: string;
  accent: string;
  text: string;
  img: string;
}

/** El pilar de una carta, tolerante a que el catálogo no lo tenga. */
export function pilarDe(carta: Carta): PilarVista {
  const c = carta.categoria as CategoriaCarta | null;
  return {
    nombre: c?.nombre || "Sin pilar",
    accent: c?.color_accent || "var(--sand-line)",
    text: c?.color_text || "var(--warm-taupe)",
    img: c?.img || "",
  };
}

/** El nombre de la acción de una carta ("" si no vino). */
export function accionDe(carta: Carta): string {
  const a = carta.accion as AccionCarta | null;
  return a?.nombre || "";
}

/** "amor-propio" → "amor propio" · para los slugs que viajan sin nombre. */
export function legible(slug: string | null | undefined): string {
  return (slug || "").replace(/[-_]/g, " ");
}

/** Un número, en español y sin decimales. */
export function num(n: number | null | undefined): string {
  return typeof n === "number" && Number.isFinite(n) ? n.toLocaleString("es-ES") : "—";
}

/** "4,3" · promedio a un decimal con coma, como se escribe en español. */
export function promedioTexto(p: number | null): string {
  return p === null ? "—" : p.toFixed(1).replace(".", ",");
}

/** Cómo la firmó su autor, dicho en cristiano. */
export function firmaTexto(firma: string | null | undefined): string {
  return firma === "apodo" ? "firmada con su apodo" : "firmada en anónimo";
}

/** Quién escribió esa vuelta del historial. */
export function porTexto(por: string | null | undefined): string {
  if (por === "usuario") return "la escribió el autor";
  if (por === "dwellia") return "la escribió Dwellia";
  return por ? `la escribió ${legible(por)}` : "";
}

/**
 * La carta en miniatura del escritorio: la banda del pilar y su dibujo.
 * No es la `Card` (que necesita el ancho de una carta de verdad): es la señal
 * de qué pilar es, y al tocarla se abre la carta entera.
 */
export function Mini({ carta, onClick }: { carta: Carta; onClick: () => void }) {
  const p = pilarDe(carta);
  return (
    <button
      type="button"
      className="adm-mini"
      onClick={onClick}
      aria-label="Ver la carta en grande"
    >
      <span className="adm-mini-band" style={{ background: p.accent }} />
      {p.img && <img className="adm-mini-dibujo" src={assetUrl(p.img)} alt="" />}
      <span className="adm-mini-ver">ver</span>
    </button>
  );
}

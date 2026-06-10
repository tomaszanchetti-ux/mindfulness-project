// Nudges de primer uso: globos contextuales que se muestran UNA vez por usuario
// y dispositivo. Viven en localStorage (jamás en la DB) y se marcan vistos al
// tocar el CTA del globo, no al mostrarse.

const key = (uid: string) => `dwellia-nudges:${uid}`;

function leer(uid: string): string[] {
  try {
    const raw = localStorage.getItem(key(uid));
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

export function nudgeVisto(uid: string, id: string): boolean {
  return leer(uid).includes(id);
}

export function marcarNudgeVisto(uid: string, id: string): void {
  try {
    const vistos = leer(uid);
    if (!vistos.includes(id)) {
      vistos.push(id);
      localStorage.setItem(key(uid), JSON.stringify(vistos));
    }
  } catch {
    /* modo privado sin localStorage: el nudge reaparece, inofensivo */
  }
}

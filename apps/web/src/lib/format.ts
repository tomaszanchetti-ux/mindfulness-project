// Helpers de presentación (fechas en español, recortes).

const MESES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];

const DIAS = [
  "domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado",
];

/** "Martes 9 de junio" — fecha cálida, sin año (la app vive en el presente). */
export function fechaLarga(iso: string): string {
  const d = new Date(iso);
  const dia = DIAS[d.getDay()];
  return `${dia[0].toUpperCase()}${dia.slice(1)} ${d.getDate()} de ${MESES[d.getMonth()]}`;
}

/** "9 jun" — compacto para el Baúl. */
export function fechaCorta(iso: string): string {
  const d = new Date(iso);
  return `${d.getDate()} ${MESES[d.getMonth()].slice(0, 3)}`;
}

/**
 * Saludo según la hora local REAL del dispositivo.
 * (QA 10/06: antes usaba la `hora_aviso` elegida y a las 13:56 decía "Buenas
 * noches" a quien eligió el turno noche.)
 */
export function saludo(): string {
  const h = new Date().getHours();
  if (h < 13) return "Buenos días";
  if (h < 20) return "Buenas tardes";
  return "Buenas noches";
}

/** "21:00" de hoy como Date local; null si no hay horario válido. */
export function horaAvisoDeHoy(hora?: string | null): Date | null {
  if (!hora || !/^\d{2}:\d{2}/.test(hora)) return null;
  const d = new Date();
  d.setHours(parseInt(hora.slice(0, 2), 10), parseInt(hora.slice(3, 5), 10), 0, 0);
  return d;
}

/** "Faltan 7 h 4 min" / "Falta menos de un minuto" hasta `objetivo`. */
export function cuentaRegresiva(objetivo: Date, ahora: Date): string {
  const min = Math.ceil((objetivo.getTime() - ahora.getTime()) / 60000);
  if (min <= 1) return "Falta menos de un minuto";
  const h = Math.floor(min / 60);
  const m = min % 60;
  if (h === 0) return `Faltan ${m} min`;
  if (m === 0) return `Faltan ${h} h`;
  return `Faltan ${h} h ${m} min`;
}

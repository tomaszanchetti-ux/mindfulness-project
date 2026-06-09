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
 * Saludo que matchea el momento que el usuario eligió (su `hora_aviso`, HH:MM).
 * Si no hay horario, cae a la hora local actual.
 */
export function saludo(hora?: string): string {
  const h = hora ? parseInt(hora.slice(0, 2), 10) : new Date().getHours();
  if (h < 13) return "Buenos días";
  if (h < 20) return "Buenas tardes";
  return "Buenas noches";
}

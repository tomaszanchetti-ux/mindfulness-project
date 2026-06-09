// Valoración opcional y discreta (1-5). Nunca es métrica de vanidad; es para el
// Baúl "Más valoradas". Sin estrella = válido (la reflexión no la exige).
//
// En modo lectura se renderiza con <span> (no <button>): así puede vivir dentro de
// otros botones — p.ej. cada entrada del Baúl es un botón — sin romper el HTML.

interface Props {
  value: number | null;
  onChange?: (v: number) => void;
  readOnly?: boolean;
}

export function Stars({ value, onChange, readOnly }: Props) {
  if (readOnly) {
    return (
      <span className="stars" aria-label={value != null ? `${value} de 5` : undefined}>
        {[1, 2, 3, 4, 5].map((n) => (
          <span key={n} className={`star ${value != null && n <= value ? "star-on" : ""}`}>
            {value != null && n <= value ? "★" : "☆"}
          </span>
        ))}
      </span>
    );
  }

  return (
    <div className="stars" role="radiogroup" aria-label="Valoración">
      {[1, 2, 3, 4, 5].map((n) => {
        const on = value != null && n <= value;
        return (
          <button
            key={n}
            type="button"
            className={`star ${on ? "star-on" : ""}`}
            aria-label={`${n} de 5`}
            aria-checked={value === n}
            role="radio"
            onClick={() => onChange?.(n)}
          >
            {on ? "★" : "☆"}
          </button>
        );
      })}
    </div>
  );
}

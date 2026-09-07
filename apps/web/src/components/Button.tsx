// Sistema de botones (doc §13). Máximo un primario por pantalla.
//
// WS30 · C2b · "danger" se suma como variante propia: es el rojo de barro de
// `.btn-danger` (app.css), y se reserva para la acción que BORRA o QUITA de
// verdad. El que solo abre la pregunta sigue siendo secundario o terciario.
import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "tertiary" | "danger";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  full?: boolean;
}

export function Button({ variant = "primary", full, className = "", ...rest }: Props) {
  return (
    <button
      className={`btn btn-${variant} ${full ? "btn-full" : ""} ${className}`}
      {...rest}
    />
  );
}

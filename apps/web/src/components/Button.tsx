// Sistema de botones (doc §13). Máximo un primario por pantalla.
import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "tertiary";

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

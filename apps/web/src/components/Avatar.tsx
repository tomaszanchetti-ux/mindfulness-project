// WS29 · C0 · La cara de una persona en Dwellia: su foto de perfil (privada,
// se baja con login como cualquier foto) o, si no subió ninguna, la inicial de
// su apodo sobre un círculo del color del papel. Un solo componente para la
// búsqueda, la comunidad, las fichas ajenas y el propio perfil.

import { FotoPrivada } from "./FotoPrivada";

export function Avatar({
  apodo,
  fotoUrl,
  size = 40,
  className,
}: {
  apodo: string;
  fotoUrl: string | null | undefined;
  size?: number;
  className?: string;
}) {
  const inicial = (apodo || "?").trim().charAt(0).toUpperCase() || "?";
  const estilo = { width: size, height: size, fontSize: Math.round(size * 0.42) };
  if (fotoUrl) {
    return (
      <span className={`avatar ${className || ""}`} style={estilo} aria-hidden>
        <FotoPrivada src={fotoUrl} className="avatar-img" />
      </span>
    );
  }
  return (
    <span className={`avatar avatar-inicial ${className || ""}`} style={estilo} aria-hidden>
      {inicial}
    </span>
  );
}

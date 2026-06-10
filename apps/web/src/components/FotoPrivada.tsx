// Una foto de la pausa. Las imágenes son privadas (la API exige login), así que
// no se puede poner la URL directo en un <img>: se baja con fetch autenticado
// (lib/api.fotoPrivadaUrl, con cache) y se muestra como object URL.

import { useEffect, useState } from "react";
import { fotoPrivadaUrl } from "../lib/api";

export function FotoPrivada({
  src,
  className,
  alt = "",
}: {
  src: string;
  className?: string;
  alt?: string;
}) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    let viva = true;
    setUrl(null);
    fotoPrivadaUrl(src)
      .then((u) => {
        if (viva) setUrl(u);
      })
      .catch(() => {
        /* la foto ya no está; queda el placeholder */
      });
    return () => {
      viva = false;
    };
  }, [src]);

  if (!url) return <span className={`foto-cargando ${className || ""}`} aria-hidden />;
  return <img className={className} src={url} alt={alt} />;
}

// WS30 · Q/A de Tomás · la recomendación de OTRA persona, en su propia pantalla.
// Lugar reservado: el agente de la ola C2b lo llena. Se lee desde la vitrina del
// dueño (`api.baulDe(usuarioId)`): no hay endpoint por id para las ajenas.
// Ruta: /comunidad/:usuarioId/recomendacion/:recomendacionId

export function RecomendacionAjena() {
  return (
    <div>
      <div className="screen-head">
        <h1 className="screen-title">Recomendación</h1>
      </div>
      <div className="center-note">Muy pronto.</div>
    </div>
  );
}

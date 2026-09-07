// WS30 · C2.1 · Comunidad — la pestaña.
//
// Formato Instagram (decisión de Tomás, WS29 §3.6): arriba el buscador y, con el
// buscador vacío, cuatro cosas en este orden —
//
//   1. Te enviaron   · las Pausas que alguien me hizo llegar (sin leer, primero)
//   2. Solicitudes   · las que me llegaron y las que mandé (se esconde si no hay)
//   3. Tu comunidad  · una tira de caras, para entrar a la vitrina de cada una
//   4. Descubrir     · fichas, NO perfiles: la grilla de dos columnas con lo que
//                      la gente compartió (foto o dibujo del pilar, la frase, y
//                      la persona bien visible abajo)
//
// Con algo escrito (≥2 letras) el buscador reemplaza todo eso: la búsqueda es la
// pantalla, no un cajón que empuja el resto hacia abajo. Busca por correo exacto,
// apodo, nombre y apellido, y devuelve una LISTA (el correo no es único en el
// esquema y jamás viaja de vuelta: nunca se muestra el correo ajeno).

import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Avatar } from "../components/Avatar";
import { FotoPrivada } from "../components/FotoPrivada";
import { api, assetUrl } from "../lib/api";
import type {
  EstadoVinculo,
  FichaAjena,
  MiComunidad,
  Persona,
  ReenvioRecibido,
} from "../lib/types";
import "./comunidad.css";

// Lo que se tarda en dejar de escribir antes de preguntarle al backend.
const ESPERA_BUSQUEDA = 280;
const MIN_BUSQUEDA = 2;

export function Comunidad() {
  const navigate = useNavigate();

  const [q, setQ] = useState("");
  const [resultados, setResultados] = useState<Persona[] | null>(null);
  const [buscando, setBuscando] = useState(false);
  const ultimaBusqueda = useRef("");

  const [mia, setMia] = useState<MiComunidad | null>(null);
  const [reenvios, setReenvios] = useState<ReenvioRecibido[]>([]);
  const [descubrir, setDescubrir] = useState<FichaAjena[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cargarComunidad = useCallback(
    () => api.miComunidad().then(setMia).catch(() => setMia({ gente: [], recibidas: [], enviadas: [] })),
    [],
  );

  useEffect(() => {
    let vivo = true;
    void cargarComunidad();
    api
      .reenviosRecibidos()
      .then((r) => vivo && setReenvios(r.reenvios))
      .catch(() => vivo && setReenvios([]));
    api
      .descubrir()
      .then((f) => vivo && setDescubrir(f))
      .catch((e) => {
        if (!vivo) return;
        setDescubrir([]);
        setError((e as Error).message);
      });
    return () => {
      vivo = false;
    };
  }, [cargarComunidad]);

  // —— El buscador ——
  // Se busca al tipear, con un respiro. La respuesta que llega tarde para una
  // palabra que ya cambió se descarta: manda lo último que se escribió.
  useEffect(() => {
    const texto = q.trim();
    ultimaBusqueda.current = texto;
    if (texto.length < MIN_BUSQUEDA) {
      setResultados(null);
      setBuscando(false);
      return;
    }
    setBuscando(true);
    const t = setTimeout(() => {
      api
        .buscarPersonas(texto)
        .then((r) => {
          if (ultimaBusqueda.current !== texto) return;
          setResultados(r);
          setBuscando(false);
        })
        .catch((e) => {
          if (ultimaBusqueda.current !== texto) return;
          setResultados([]);
          setBuscando(false);
          setError((e as Error).message);
        });
    }, ESPERA_BUSQUEDA);
    return () => clearTimeout(t);
  }, [q]);

  // Un vínculo cambió: se refleja en el acto en la fila que se tocó y se vuelve
  // a pedir la comunidad (las secciones de abajo salen de ahí).
  const vinculoCambio = (usuarioId: string, vinculo: EstadoVinculo) => {
    setResultados((cur) =>
      cur ? cur.map((p) => (p.usuario_id === usuarioId ? { ...p, vinculo } : p)) : cur,
    );
    void cargarComunidad();
  };

  const abrirReenvio = (r: ReenvioRecibido) => {
    if (!r.leido) {
      setReenvios((cur) => cur.map((x) => (x.id === r.id ? { ...x, leido: true } : x)));
      api.reenvioLeido(r.id).catch(() => {});
    }
    navigate(`/comunidad/ficha/${r.ficha.id}`);
  };

  const buscandoAlgo = q.trim().length >= MIN_BUSQUEDA;

  return (
    <div className="comunidad">
      <div className="screen-head">
        <h1 className="screen-title">Comunidad</h1>
        <p className="screen-sub">Las personas con las que compartes tus Pausas.</p>
      </div>

      <div className="com-buscador">
        <input
          type="search"
          value={q}
          placeholder="Busca por apodo, nombre o correo"
          aria-label="Buscar personas en Dwellia"
          onChange={(e) => setQ(e.target.value)}
        />
        {q && (
          <button
            type="button"
            className="com-buscador-limpiar"
            aria-label="Limpiar la búsqueda"
            onClick={() => setQ("")}
          >
            ×
          </button>
        )}
      </div>

      {error && <p className="com-aviso">{error}</p>}

      {buscandoAlgo ? (
        <Resultados
          resultados={resultados}
          buscando={buscando}
          onVinculo={vinculoCambio}
          onError={setError}
          onAbrir={(id) => navigate(`/comunidad/${id}`)}
        />
      ) : (
        <>
          {/* —— 1 · Te enviaron —— */}
          {reenvios.length > 0 && (
            <section className="com-seccion">
              <h2 className="com-seccion-titulo">Te enviaron</h2>
              {[...reenvios]
                .sort((a, z) => Number(a.leido) - Number(z.leido))
                .map((r) => (
                  <button
                    key={r.id}
                    type="button"
                    className={`com-reenvio ${r.leido ? "" : "es-no-leido"}`}
                    onClick={() => abrirReenvio(r)}
                  >
                    <Miniatura ficha={r.ficha} />
                    <span className="com-reenvio-txt">
                      <span className="com-reenvio-quien">{r.de.apodo} te envió una Pausa</span>
                      <span className="com-reenvio-frase">{r.ficha.carta.frase}</span>
                    </span>
                    {!r.leido && <span className="com-punto" aria-label="Sin leer" />}
                  </button>
                ))}
            </section>
          )}

          {/* —— 2 · Solicitudes (solo si hay algo que resolver) —— */}
          {mia && (mia.recibidas.length > 0 || mia.enviadas.length > 0) && (
            <section className="com-seccion">
              <h2 className="com-seccion-titulo">Solicitudes</h2>
              {mia.recibidas.length > 0 && (
                <>
                  <p className="com-sub">Quieren ser parte de tu comunidad</p>
                  {mia.recibidas.map((p) => (
                    <FilaPersona
                      key={p.usuario_id}
                      persona={p}
                      onVinculo={vinculoCambio}
                      onError={setError}
                      onAbrir={(id) => navigate(`/comunidad/${id}`)}
                    />
                  ))}
                </>
              )}
              {mia.enviadas.length > 0 && (
                <>
                  <p className="com-sub">Esperando respuesta</p>
                  {mia.enviadas.map((p) => (
                    <FilaPersona
                      key={p.usuario_id}
                      persona={p}
                      onVinculo={vinculoCambio}
                      onError={setError}
                      onAbrir={(id) => navigate(`/comunidad/${id}`)}
                    />
                  ))}
                </>
              )}
            </section>
          )}

          {/* —— 3 · Tu comunidad —— */}
          <section className="com-seccion">
            <h2 className="com-seccion-titulo">Tu comunidad</h2>
            {mia === null ? (
              <p className="com-seccion-nota">…</p>
            ) : mia.gente.length === 0 ? (
              <p className="com-seccion-nota">
                Todavía no tienes a nadie. Busca a alguien por su apodo o su correo y
                envíale una solicitud.
              </p>
            ) : (
              <div className="com-tira">
                {mia.gente.map((p) => (
                  <button
                    key={p.usuario_id}
                    type="button"
                    className="com-tira-uno"
                    onClick={() => navigate(`/comunidad/${p.usuario_id}`)}
                  >
                    <Avatar apodo={p.apodo} fotoUrl={p.foto_url} size={56} />
                    <span className="com-tira-apodo">{p.apodo}</span>
                  </button>
                ))}
              </div>
            )}
          </section>

          {/* —— 4 · Descubrir —— */}
          <section className="com-seccion">
            <h2 className="com-seccion-titulo">Descubrir</h2>
            {descubrir === null ? (
              <p className="com-seccion-nota">…</p>
            ) : descubrir.length === 0 ? (
              <p className="com-seccion-nota">
                Aquí van a aparecer las Pausas que comparta tu comunidad. Cuando alguien
                abra una, la vas a ver.
              </p>
            ) : (
              <div className="com-grilla">
                {descubrir.map((f) => (
                  <button
                    key={f.id}
                    type="button"
                    className="com-tile"
                    onClick={() => navigate(`/comunidad/ficha/${f.id}`)}
                  >
                    <span className="com-tile-art">
                      <span
                        className="com-tile-band"
                        style={{ background: f.carta.categoria.color_accent }}
                      />
                      {f.fotos.length > 0 ? (
                        <FotoPrivada className="com-tile-foto" src={f.fotos[0]} />
                      ) : (
                        <img
                          className="com-tile-dibujo"
                          src={assetUrl(f.carta.categoria.img)}
                          alt=""
                        />
                      )}
                    </span>
                    <span className="com-tile-frase">{f.carta.frase}</span>
                    <span className="com-tile-de">
                      <Avatar apodo={f.de.apodo} fotoUrl={f.de.foto_url} size={22} />
                      <span>{f.de.apodo}</span>
                    </span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}

// —— La búsqueda ————————————————————————————————————————————————————————————
function Resultados({
  resultados,
  buscando,
  onVinculo,
  onError,
  onAbrir,
}: {
  resultados: Persona[] | null;
  buscando: boolean;
  onVinculo: (usuarioId: string, vinculo: EstadoVinculo) => void;
  onError: (msg: string) => void;
  onAbrir: (usuarioId: string) => void;
}) {
  if (buscando && resultados === null) return <p className="com-buscando">Buscando…</p>;
  if (resultados === null) return null;
  if (resultados.length === 0)
    return (
      <div className="empty">
        <p className="empty-title">No encontramos a nadie así.</p>
        <p className="empty-body">
          Prueba con su apodo, su nombre o el correo con el que entra a Dwellia.
        </p>
      </div>
    );
  return (
    <section className="com-seccion">
      {resultados.map((p) => (
        <FilaPersona
          key={p.usuario_id}
          persona={p}
          onVinculo={onVinculo}
          onError={onError}
          onAbrir={onAbrir}
        />
      ))}
    </section>
  );
}

// —— Una persona, con lo que se puede hacer con ella ————————————————————————
function FilaPersona({
  persona,
  onVinculo,
  onError,
  onAbrir,
}: {
  persona: Persona;
  onVinculo: (usuarioId: string, vinculo: EstadoVinculo) => void;
  onError: (msg: string) => void;
  onAbrir: (usuarioId: string) => void;
}) {
  return (
    <div className="com-fila">
      <button
        type="button"
        className="com-fila-quien"
        onClick={() => onAbrir(persona.usuario_id)}
      >
        <Avatar apodo={persona.apodo} fotoUrl={persona.foto_url} size={46} />
        <span className="com-fila-datos">
          <span className="com-fila-apodo">{persona.apodo}</span>
          {(persona.nombre || persona.apellido) && (
            <span className="com-fila-nombre">
              {[persona.nombre, persona.apellido].filter(Boolean).join(" ")}
            </span>
          )}
        </span>
      </button>
      <CtaVinculo persona={persona} onVinculo={onVinculo} onError={onError} />
    </div>
  );
}

// —— El botón del vínculo ———————————————————————————————————————————————————
// Un solo lugar decide qué se puede hacer con una persona según en qué punto
// está el vínculo. Lo usan la búsqueda, las solicitudes y el perfil ajeno.
export function CtaVinculo({
  persona,
  onVinculo,
  onError,
}: {
  persona: Persona;
  onVinculo: (usuarioId: string, vinculo: EstadoVinculo) => void;
  onError: (msg: string) => void;
}) {
  const [ocupado, setOcupado] = useState(false);
  const vinculo = persona.vinculo ?? "ninguno";

  const correr = async (fn: () => Promise<unknown>, siSale: EstadoVinculo) => {
    if (ocupado) return;
    setOcupado(true);
    try {
      await fn();
      onVinculo(persona.usuario_id, siSale);
    } catch (e) {
      // El backend responde en español (409 "Ya hay un vínculo", 422, 404):
      // se muestra tal cual, sin traducirlo acá.
      onError((e as Error).message);
    } finally {
      setOcupado(false);
    }
  };

  if (vinculo === "aceptada") return <span className="com-estado">En tu comunidad</span>;

  if (vinculo === "pendiente_recibida")
    return (
      <span className="com-fila-cta">
        <button
          type="button"
          className="com-btn es-si"
          disabled={ocupado}
          onClick={() => correr(() => api.aceptarVinculo(persona.usuario_id), "aceptada")}
        >
          Aceptar
        </button>
        <button
          type="button"
          className="com-btn"
          disabled={ocupado}
          onClick={() => correr(() => api.descartarSolicitud(persona.usuario_id), "ninguno")}
        >
          Rechazar
        </button>
      </span>
    );

  if (vinculo === "pendiente_enviada")
    return (
      <button
        type="button"
        className="com-btn"
        disabled={ocupado}
        onClick={() => correr(() => api.descartarSolicitud(persona.usuario_id), "ninguno")}
      >
        Cancelar solicitud
      </button>
    );

  return (
    <button
      type="button"
      className="com-btn es-si"
      disabled={ocupado}
      onClick={() => correr(() => api.pedirVinculo(persona.usuario_id), "pendiente_enviada")}
    >
      Enviar solicitud
    </button>
  );
}

// —— La ficha en miniatura de "Te enviaron" ————————————————————————————————
// La foto de la Pausa si la hay; si no, el dibujo del pilar sobre su banda, el
// mismo gesto de `.ficha-mini` del Baúl y de `.carta-mini` de Crear.
export function Miniatura({ ficha }: { ficha: FichaAjena }) {
  const cat = ficha.carta.categoria;
  return (
    <span className="com-mini">
      <span className="com-mini-band" style={{ background: cat.color_accent }} />
      {ficha.fotos.length > 0 ? (
        <FotoPrivada className="com-mini-foto" src={ficha.fotos[0]} />
      ) : (
        <img className="com-mini-dibujo" src={assetUrl(cat.img)} alt="" />
      )}
    </span>
  );
}

// WS28 · B2.2b · Bloque 2 · El termómetro del sistema.
//
// Números del SISTEMA, nunca de una persona (decisión de Tomás, WS27 §6): sirven
// para una sola cosa, ver si un pilar quedó desparejo y escribir cartas de
// Dwellia para emparejarlo. Solo lectura: acá no se toca nada.

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { rotulo } from "../../lib/propuestas";
import type { EstadoPropuesta, ResumenAdmin } from "../../lib/types";
import { useStore } from "../../store";
import { es403, mensaje, num } from "./comun";

// Los seis estados, en el orden del recorrido de una carta. Los dos primeros
// comparten rótulo a propósito (para el autor son lo mismo): en el escritorio se
// distinguen con una aclaración chica, sin nombrar el estado técnico.
const ESTADOS: { estado: EstadoPropuesta; hint?: string }[] = [
  { estado: "en_revision", hint: "con el juez" },
  { estado: "revision_dwellia", hint: "te toca a ti" },
  { estado: "a_revisar" },
  { estado: "aprobada" },
  { estado: "rechazada" },
  { estado: "retirada" },
];

export function Termometro({ onCerrado }: { onCerrado: () => void }) {
  const { categorias } = useStore();
  const [r, setR] = useState<ResumenAdmin | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vivo = true;
    api
      .adminResumen()
      .then((res) => {
        if (vivo) setR(res);
      })
      .catch((e: unknown) => {
        if (!vivo) return;
        if (es403(e)) {
          onCerrado();
          return;
        }
        setError(mensaje(e));
      });
    return () => {
      vivo = false;
    };
  }, [onCerrado]);

  if (error) return <p className="adm-error">{error}</p>;
  if (!r) return <div className="center-note">…</div>;

  // La barra se mide contra el pilar más grande: así se ve el hueco, que es
  // justamente para lo que existe este tablero.
  const techo = Math.max(1, ...r.cartas.por_pilar.map((p) => p.total));

  return (
    <section>
      <div className="adm-cards">
        <div className="adm-card">
          <h3 className="adm-card-t">Personas</h3>
          <div className="adm-nums">
            <Num k="En total" v={r.usuarios.total} fuerte />
            <Num k="Terminaron el onboarding" v={r.usuarios.con_onboarding} />
            <Num k="Premium" v={r.usuarios.premium} />
            <Num k="Gratis" v={r.usuarios.free} />
            <Num k="Escribieron cartas" v={r.usuarios.crearon_cartas} />
          </div>
        </div>

        <div className="adm-card">
          <h3 className="adm-card-t">Mazo</h3>
          <div className="adm-nums">
            <Num k="Cartas en total" v={r.cartas.total} fuerte />
            <Num k="De Dwellia" v={r.cartas.dwellia} />
            <Num k="De la comunidad" v={r.cartas.comunidad} />
          </div>
        </div>

        <div className="adm-card">
          <h3 className="adm-card-t">Cartas propuestas</h3>
          <div className="adm-nums">
            <Num k="Esperando una mirada" v={r.propuestas.pendientes ?? 0} fuerte />
            {ESTADOS.map(({ estado, hint }) => (
              <Num
                key={estado}
                k={rotulo(estado).texto}
                hint={hint}
                v={r.propuestas[estado] ?? 0}
              />
            ))}
          </div>
        </div>

        <div className="adm-card">
          <h3 className="adm-card-t">Comentarios</h3>
          <div className="adm-nums">
            <Num k="En total" v={r.comentarios.total} fuerte />
            <Num k="Últimos 7 días" v={r.comentarios.ultimos_7_dias} />
          </div>
        </div>
      </div>

      <h3 className="adm-sub-t">Cartas por pilar</h3>
      <div className="adm-leyenda">
        <span className="adm-leyenda-item">
          <span className="adm-punto" style={{ background: "var(--sage)" }} /> de Dwellia
        </span>
        <span className="adm-leyenda-item">
          <span className="adm-punto" style={{ background: "var(--dust-taupe)" }} /> de la
          comunidad (en el color del pilar)
        </span>
      </div>

      <div className="adm-pilares">
        {r.cartas.por_pilar.map((p) => {
          const cat = categorias.find((c) => c.slug === p.slug);
          const accent = cat?.color_accent || "var(--dust-taupe)";
          const text = cat?.color_text || "var(--deep-umber)";
          return (
            <div className="adm-pilar" key={p.slug}>
              <span className="adm-pilar-n" style={{ color: text }}>
                {cat?.nombre || p.nombre}
              </span>
              <span
                className="adm-pilar-barra"
                role="img"
                aria-label={`${p.total} cartas: ${p.dwellia} de Dwellia y ${p.comunidad} de la comunidad`}
              >
                <span
                  className="adm-seg"
                  style={{
                    width: `${(p.dwellia / techo) * 100}%`,
                    background: "var(--sage)",
                  }}
                />
                <span
                  className="adm-seg"
                  style={{
                    width: `${(p.comunidad / techo) * 100}%`,
                    background: accent,
                  }}
                />
              </span>
              <span className="adm-pilar-cifras">
                <span className="adm-pilar-total">{num(p.total)}</span>
                {num(p.dwellia)} · {num(p.comunidad)}
              </span>
            </div>
          );
        })}
      </div>

      <p className="adm-pie">
        Estos números son del sistema: no hay nada por persona, ni aquí ni en
        ninguna otra parte del escritorio.
      </p>
    </section>
  );
}

function Num({
  k,
  v,
  hint,
  fuerte,
}: {
  k: string;
  v: number;
  hint?: string;
  fuerte?: boolean;
}) {
  return (
    <div className={`adm-num ${fuerte ? "is-fuerte" : ""}`}>
      <span className="adm-num-k">
        {k}
        {hint && <span className="adm-num-hint">{hint}</span>}
      </span>
      <span className="adm-num-v">{num(v)}</span>
    </div>
  );
}

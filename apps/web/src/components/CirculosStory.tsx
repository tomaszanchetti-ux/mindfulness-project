// Visuales educativos del onboarding (storytelling WS18).
// Mismo lenguaje que StoryArt: línea fina umber, acentos sage, sin rellenos pesados.
//
//  · PilaresCirculo — los 6 pilares interconectados, con la persona en el centro.
//    Usa los colores y nombres REALES del contenido (store), no copias.
//  · EscrituraCirculo — el diario en el centro (escribir ES la pausa) y las 4
//    actividades de desconexión orbitando como disparadores.

import type { AccionContenido, CategoriaContenido } from "../lib/types";

const LINEA = "var(--deep-umber)";
const ACENTO = "var(--sage)";
const ACENTO_PROFUNDO = "var(--sage-deep)";

// Persona serena (cabeza + hombros), el centro del crecimiento.
function Persona({ cx, cy }: { cx: number; cy: number }) {
  return (
    <g stroke={LINEA} strokeWidth="2.4" fill="none" strokeLinecap="round">
      <circle cx={cx} cy={cy - 14} r="11" />
      <path d={`M${cx - 17} ${cy + 18}c0-13 7-19 17-19s17 6 17 19`} />
    </g>
  );
}

export function PilaresCirculo({ pilares }: { pilares: CategoriaContenido[] }) {
  const CX = 150;
  const CY = 122;
  const R = 88;
  const nodos = pilares.map((p, i) => {
    const ang = (-90 + i * (360 / Math.max(pilares.length, 1))) * (Math.PI / 180);
    return { ...p, x: CX + R * Math.cos(ang), y: CY + R * Math.sin(ang) };
  });

  return (
    <svg viewBox="0 0 300 252" fill="none" aria-hidden>
      {/* el anillo que los conecta entre sí */}
      <circle
        cx={CX}
        cy={CY}
        r={R}
        stroke={ACENTO_PROFUNDO}
        strokeWidth="1.6"
        strokeDasharray="3 7"
        opacity="0.5"
      />
      {/* hilos suaves de cada pilar a la persona */}
      {nodos.map((n) => (
        <line
          key={`hilo-${n.slug}`}
          x1={CX + (n.x - CX) * 0.28}
          y1={CY + (n.y - CY) * 0.28}
          x2={CX + (n.x - CX) * 0.82}
          y2={CY + (n.y - CY) * 0.82}
          stroke={LINEA}
          strokeWidth="1.2"
          opacity="0.18"
        />
      ))}
      <Persona cx={CX} cy={CY} />
      {nodos.map((n) => {
        const arriba = n.y < CY - 30;
        return (
          <g key={n.slug}>
            <circle cx={n.x} cy={n.y} r="9" fill={n.color_accent} stroke="var(--soft-ivory)" strokeWidth="2.5" />
            <text
              x={n.x}
              y={arriba ? n.y - 17 : n.y + 26}
              textAnchor="middle"
              fontSize="12.5"
              fontWeight="600"
              fill={LINEA}
            >
              {n.nombre}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export function EscrituraCirculo({ acciones }: { acciones: AccionContenido[] }) {
  const CX = 150;
  const CY = 122;
  const R = 92;
  const complementos = acciones.filter((a) => a.slug !== "escribir");
  const nodos = complementos.map((a, i) => {
    const ang = (-90 + i * (360 / Math.max(complementos.length, 1))) * (Math.PI / 180);
    return { ...a, x: CX + R * Math.cos(ang), y: CY + R * Math.sin(ang) };
  });

  return (
    <svg viewBox="0 0 300 252" fill="none" aria-hidden>
      {/* el núcleo: el diario abierto y la pluma (escribir ES la pausa) */}
      <circle cx={CX} cy={CY} r="46" stroke={ACENTO} strokeWidth="2.4" fill="var(--soft-ivory)" />
      <g stroke={LINEA} strokeWidth="2.2" fill="none" strokeLinecap="round" strokeLinejoin="round">
        <path d={`M${CX - 26} ${CY - 6}c9-4.5 17-4.5 26-1.2 9-3.3 17-3.3 26 1.2`} />
        <path d={`M${CX - 26} ${CY - 6}v21c9-4.5 17-4.5 26-1.2 9-3.3 17-3.3 26 1.2v-21`} />
        <path d={`M${CX} ${CY - 7.2}v21`} />
        <path d={`M${CX - 19} ${CY + 1}h12M${CX - 19} ${CY + 7}h9`} stroke={ACENTO_PROFUNDO} strokeWidth="1.7" />
        <path d={`M${CX + 8} ${CY + 9}l14-17`} strokeWidth="2.4" />
        <path d={`M${CX + 8} ${CY + 9}l-3 4.4 4.7-1.5z`} fill={ACENTO} stroke="none" />
      </g>
      <text x={CX} y={CY + 33} textAnchor="middle" fontSize="12.5" fontWeight="700" fill={ACENTO_PROFUNDO}>
        Escribir
      </text>

      {/* las actividades, disparando hacia el centro */}
      {nodos.map((n) => {
        const arriba = n.y < CY - 30;
        return (
          <g key={n.slug}>
            <line
              x1={CX + (n.x - CX) * 0.82}
              y1={CY + (n.y - CY) * 0.82}
              x2={CX + (n.x - CX) * 0.56}
              y2={CY + (n.y - CY) * 0.56}
              stroke={ACENTO_PROFUNDO}
              strokeWidth="1.8"
              strokeDasharray="3 5"
              opacity="0.65"
              markerEnd="url(#flecha)"
            />
            <circle cx={n.x} cy={n.y} r="7.5" stroke={LINEA} strokeWidth="2" fill="var(--soft-ivory)" />
            <text
              x={n.x}
              y={arriba ? n.y - 15 : n.y + 24}
              textAnchor="middle"
              fontSize="12.5"
              fontWeight="600"
              fill={LINEA}
            >
              {n.nombre}
            </text>
          </g>
        );
      })}
      <defs>
        <marker id="flecha" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">
          <path d="M0 0L7 3.5L0 7z" fill={ACENTO_PROFUNDO} opacity="0.65" />
        </marker>
      </defs>
    </svg>
  );
}

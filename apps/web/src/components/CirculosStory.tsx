// Visuales educativos del storytelling (canon WS22).
// Mismo lenguaje que StoryArt: línea fina umber, acentos sage, sin rellenos pesados.
//
//  · AnillosCirculo — la persona en el centro, la calma como halo (el agua) y los
//    6 pilares en TRES anillos de a dos: adentro (amor propio · sentido), la
//    experiencia (gratitud · perspectiva), afuera y adelante (vínculos ·
//    resiliencia). Usa colores y nombres REALES del contenido (store).
//  · PausaDosTiempos — la anatomía de toda pausa: una acción → la calma (el agua
//    que se aquieta) → escribir en el diario.

import type { CategoriaContenido } from "../lib/types";

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

// Cada pilar vive en su anillo (canon WS22, fundamentos §4).
const ANILLO_DE: Record<string, number> = {
  "amor-propio": 0,
  sentido: 0,
  gratitud: 1,
  perspectiva: 1,
  vinculos: 2,
  resiliencia: 2,
};

// Posiciones: 2 nodos por anillo, diametralmente opuestos; cada anillo rotado
// 60° respecto del anterior → los 6 quedan repartidos, con aire para los nombres.
const RADIOS = [56, 82, 106];
const ANGULOS: [number, number][] = [
  [-90, 90],   // anillo interior: arriba / abajo
  [-30, 150],  // medio: arriba-derecha / abajo-izquierda
  [-150, 30],  // exterior: arriba-izquierda / abajo-derecha
];

export function AnillosCirculo({ pilares }: { pilares: CategoriaContenido[] }) {
  const CX = 150;
  const CY = 128;

  const usados: Record<number, number> = { 0: 0, 1: 0, 2: 0 };
  const nodos = pilares
    .filter((p) => ANILLO_DE[p.slug] !== undefined)
    .map((p) => {
      const anillo = ANILLO_DE[p.slug];
      const ang = ANGULOS[anillo][usados[anillo]++ % 2] * (Math.PI / 180);
      return {
        ...p,
        x: CX + RADIOS[anillo] * Math.cos(ang),
        y: CY + RADIOS[anillo] * Math.sin(ang),
      };
    });

  return (
    <svg viewBox="0 0 300 256" fill="none" aria-hidden>
      {/* los tres anillos del recorrido */}
      {RADIOS.map((r, i) => (
        <circle
          key={r}
          cx={CX}
          cy={CY}
          r={r}
          stroke={ACENTO_PROFUNDO}
          strokeWidth="1.5"
          strokeDasharray="3 7"
          opacity={0.46 - i * 0.1}
        />
      ))}
      {/* la calma: el agua que rodea a la persona (el vehículo de todo) */}
      <circle cx={CX} cy={CY} r="25" stroke={ACENTO} strokeWidth="1.6" opacity="0.55" strokeDasharray="1 0" />
      <circle cx={CX} cy={CY} r="32" stroke={ACENTO} strokeWidth="1.3" opacity="0.3" />
      <Persona cx={CX} cy={CY} />
      <text
        x={CX}
        y={CY + 44}
        textAnchor="middle"
        fontSize="10.5"
        fontStyle="italic"
        fill={ACENTO_PROFUNDO}
      >
        calma
      </text>

      {nodos.map((n) => {
        const arriba = n.y < CY;
        return (
          <g key={n.slug}>
            <circle cx={n.x} cy={n.y} r="9" fill={n.color_accent} stroke="var(--soft-ivory)" strokeWidth="2.5" />
            <text
              x={n.x}
              y={arriba ? n.y - 16 : n.y + 25}
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

// La pausa de dos tiempos: una acción → la calma (el agua se aquieta) → escribir.
export function PausaDosTiempos() {
  const Y = 86;

  return (
    <svg viewBox="0 0 300 168" fill="none" aria-hidden>
      {/* 1 · una acción (los pasos que arrancan la pausa) */}
      <g>
        <circle cx="52" cy={Y} r="24" stroke={LINEA} strokeWidth="2.2" fill="var(--soft-ivory)" />
        <g stroke={LINEA} strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round">
          <path d={`M44 ${Y - 9}l9 9-9 9`} />
          <path d={`M54 ${Y - 9}l9 9-9 9`} opacity="0.45" />
        </g>
        <text x="52" y={Y + 44} textAnchor="middle" fontSize="12.5" fontWeight="600" fill={LINEA}>
          una acción
        </text>
      </g>

      {/* 2 · la calma: el agua que se aquieta (ondas concéntricas) */}
      <g>
        <circle cx="150" cy={Y} r="11" stroke={ACENTO_PROFUNDO} strokeWidth="2" opacity="0.9" />
        <circle cx="150" cy={Y} r="20" stroke={ACENTO} strokeWidth="1.8" opacity="0.6" />
        <circle cx="150" cy={Y} r="29" stroke={ACENTO} strokeWidth="1.5" opacity="0.32" />
        <text
          x="150"
          y={Y + 50}
          textAnchor="middle"
          fontSize="12.5"
          fontWeight="700"
          fill={ACENTO_PROFUNDO}
        >
          la calma
        </text>
      </g>

      {/* 3 · escribir (la pluma sobre el diario: el cierre de toda pausa) */}
      <g>
        <circle cx="248" cy={Y} r="24" stroke={LINEA} strokeWidth="2.2" fill="var(--soft-ivory)" />
        <g stroke={LINEA} strokeWidth="2.2" fill="none" strokeLinecap="round" strokeLinejoin="round">
          <path d={`M240 ${Y + 10}l15-19`} strokeWidth="2.4" />
          <path d={`M240 ${Y + 10}l-3.2 4.6 5-1.6z`} fill={ACENTO} stroke="none" />
          <path d={`M249 ${Y - 4}l6 4M246 ${Y}l6 4`} strokeWidth="1.5" opacity="0.6" />
        </g>
        <text x="248" y={Y + 44} textAnchor="middle" fontSize="12.5" fontWeight="600" fill={LINEA}>
          escribir
        </text>
      </g>

      {/* el viaje: dos arcos suaves con flecha */}
      <g
        stroke={ACENTO_PROFUNDO}
        strokeWidth="1.8"
        strokeDasharray="3 5"
        opacity="0.65"
        fill="none"
      >
        <path d={`M82 ${Y - 14}q34 -26 44 -8`} markerEnd="url(#flecha-pausa)" />
        <path d={`M184 ${Y - 20}q26 -16 38 0`} markerEnd="url(#flecha-pausa)" />
      </g>
      <defs>
        <marker id="flecha-pausa" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">
          <path d="M0 0L7 3.5L0 7z" fill={ACENTO_PROFUNDO} opacity="0.65" />
        </marker>
      </defs>
    </svg>
  );
}

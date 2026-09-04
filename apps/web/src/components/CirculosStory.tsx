// Visuales educativos del storytelling (canon WS22).
// Mismo lenguaje que StoryArt: línea fina umber, acentos sage, sin rellenos pesados.
//
//  · AnillosCirculo — la persona en el centro, la calma como halo (el agua) y los
//    6 pilares repartidos como las horas de un reloj, todos a la misma distancia
//    (WS25 · R1). Los tres anillos punteados siguen de fondo, contando el
//    recorrido: adentro (amor propio · sentido), la experiencia (gratitud ·
//    perspectiva), afuera y adelante (vínculos · resiliencia). Usa colores y
//    nombres REALES del contenido (store).
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

// WS25 · R1 — los 6 pilares a UN MISMO radio, como las horas de un reloj:
// 12 amor propio · 2 gratitud · 4 vínculos · 6 sentido · 8 perspectiva · 10 resiliencia.
// El ángulo lo fija el slug (nunca el orden en que llega el catálogo), así el
// dibujo sale siempre simétrico. Los tres anillos punteados quedan de fondo:
// siguen contando el recorrido (adentro · la experiencia · afuera), pero ya no
// mandan sobre la posición de los nodos.
const ANGULO_DE: Record<string, number> = {
  "amor-propio": -90,
  gratitud: -30,
  vinculos: 30,
  sentido: 90,
  perspectiva: 150,
  resiliencia: -150,
};

const RADIOS = [56, 82, 106]; // los tres anillos del recorrido (solo fondo)
const RADIO_PILAR = 86; // todos los pilares, a la misma distancia del centro

export function AnillosCirculo({ pilares }: { pilares: CategoriaContenido[] }) {
  const CX = 180;
  const CY = 140;

  const nodos = pilares
    .filter((p) => ANGULO_DE[p.slug] !== undefined)
    .map((p) => {
      const grados = ANGULO_DE[p.slug];
      const ang = grados * (Math.PI / 180);
      return {
        ...p,
        grados,
        x: CX + RADIO_PILAR * Math.cos(ang),
        y: CY + RADIO_PILAR * Math.sin(ang),
      };
    });

  return (
    <svg viewBox="0 0 360 276" fill="none" aria-hidden>
      {/* los tres anillos del recorrido — apenas insinuados, que no compitan */}
      {RADIOS.map((r, i) => (
        <circle
          key={r}
          cx={CX}
          cy={CY}
          r={r}
          stroke={ACENTO_PROFUNDO}
          strokeWidth="1.2"
          strokeDasharray="2 8"
          opacity={0.24 - i * 0.05}
        />
      ))}
      {/* la calma: un aura serena alrededor de la persona (sin palabras) */}
      <defs>
        <radialGradient id="aura-calma" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="var(--sage)" stopOpacity="0.35" />
          <stop offset="60%" stopColor="var(--sage)" stopOpacity="0.16" />
          <stop offset="100%" stopColor="var(--sage)" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx={CX} cy={CY} r="42" fill="url(#aura-calma)" />
      <Persona cx={CX} cy={CY} />

      {nodos.map((n) => {
        // El nombre sale hacia afuera: arriba y abajo centrado, a los lados
        // pegado al nodo y en horizontal. Así ninguno pisa a otro ni a la
        // persona del centro, sin importar cuán largo sea.
        const vertical = n.grados === -90 || n.grados === 90;
        const derecha = n.grados === -30 || n.grados === 30;
        return (
          <g key={n.slug}>
            <circle cx={n.x} cy={n.y} r="9" fill={n.color_accent} stroke="var(--soft-ivory)" strokeWidth="2.5" />
            <text
              x={vertical ? n.x : n.x + (derecha ? 15 : -15)}
              y={vertical ? (n.grados === -90 ? n.y - 18 : n.y + 27) : n.y + 4.5}
              textAnchor={vertical ? "middle" : derecha ? "start" : "end"}
              fontSize="12.5"
              fontWeight="600"
              fill={LINEA}
              /* halo del color del papel: el punteado del anillo nunca toca las letras */
              stroke="var(--warm-cream)"
              strokeWidth="4"
              strokeLinejoin="round"
              paintOrder="stroke"
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
  const LABEL_Y = Y + 44; // las tres palabras, en la misma línea de base

  return (
    <svg viewBox="0 0 300 168" fill="none" aria-hidden>
      {/* 1 · una acción (los pasos que arrancan la pausa) */}
      <g>
        <circle cx="52" cy={Y} r="24" stroke={LINEA} strokeWidth="2.2" fill="var(--soft-ivory)" />
        <g stroke={LINEA} strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round">
          <path d={`M44 ${Y - 9}l9 9-9 9`} />
          <path d={`M54 ${Y - 9}l9 9-9 9`} opacity="0.45" />
        </g>
        <text x="52" y={LABEL_Y} textAnchor="middle" fontSize="12.5" fontWeight="600" fill={LINEA}>
          acción
        </text>
      </g>

      {/* 2 · la calma: el agua que se aquieta (ondas concéntricas) */}
      <g>
        <circle cx="150" cy={Y} r="11" stroke={ACENTO_PROFUNDO} strokeWidth="2" opacity="0.9" />
        <circle cx="150" cy={Y} r="20" stroke={ACENTO} strokeWidth="1.8" opacity="0.6" />
        <circle cx="150" cy={Y} r="29" stroke={ACENTO} strokeWidth="1.5" opacity="0.32" />
        <text
          x="150"
          y={LABEL_Y}
          textAnchor="middle"
          fontSize="12.5"
          fontWeight="700"
          fill={ACENTO_PROFUNDO}
        >
          calma
        </text>
      </g>

      {/* 3 · escribir (la pluma: el cierre de toda pausa) */}
      <g>
        <circle cx="248" cy={Y} r="24" stroke={LINEA} strokeWidth="2.2" fill="var(--soft-ivory)" />
        <g stroke={LINEA} strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round">
          {/* la hoja de la pluma */}
          <path d={`M239 ${Y + 11} C241 ${Y + 2} 246 ${Y - 6} 257 ${Y - 11} C254 ${Y - 2} 248 ${Y + 6} 239 ${Y + 11} Z`} />
          {/* la vena central */}
          <path d={`M239 ${Y + 11} C243 ${Y + 4} 249 ${Y - 3} 257 ${Y - 11}`} strokeWidth="1.3" opacity="0.55" />
          {/* la punta que escribe */}
          <path d={`M239 ${Y + 11}l-4 4`} strokeWidth="2.2" />
        </g>
        <text x="248" y={LABEL_Y} textAnchor="middle" fontSize="12.5" fontWeight="600" fill={LINEA}>
          escribir
        </text>
      </g>

      {/* el viaje: rectas punteadas con el triángulo alineado a la línea */}
      <g
        stroke={ACENTO_PROFUNDO}
        strokeWidth="1.8"
        strokeDasharray="3 5"
        opacity="0.65"
        fill="none"
      >
        {/* las líneas terminan en un hueco del punteado; el triángulo va después,
            sin pisar ningún punto (QA Tomás) */}
        <line x1="82" y1={Y} x2="104" y2={Y} markerEnd="url(#flecha-pausa)" />
        <line x1="187" y1={Y} x2="209" y2={Y} markerEnd="url(#flecha-pausa)" />
      </g>
      <defs>
        <marker id="flecha-pausa" markerWidth="8" markerHeight="8" refX="1" refY="3.5" orient="auto">
          <path d="M0 0L7 3.5L0 7z" fill={ACENTO_PROFUNDO} opacity="0.65" />
        </marker>
      </defs>
    </svg>
  );
}

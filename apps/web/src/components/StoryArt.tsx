// Escenas ilustradas del onboarding (slideshow) y estados de espera.
// Línea fina de la marca (umber + acento sage), dibujadas inline para poder usar
// las variables de color del tema. Trazo redondeado, sin rellenos salvo el acento.
// Referencias de contenido: NewCo - Proyectos/Mindfulness App/Onboarding/*.png
// (allí el estilo es flat-color; acá se traduce al estilo Dwellia).

export type Escena =
  | "amanecer"
  | "recibe"
  | "pausa"
  | "diario"
  | "guarda"
  | "comparte";

const LINEA = "var(--deep-umber)";
const ACENTO = "var(--sage)";
const ACENTO_PROFUNDO = "var(--sage-deep)";

function Lienzo({ children }: { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 180 132"
      fill="none"
      stroke={LINEA}
      strokeWidth="2.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {children}
    </svg>
  );
}

// Estrella de 4 puntas (el "momento para ti").
function Destello({ x, y, s = 1 }: { x: number; y: number; s?: number }) {
  return (
    <path
      d={`M${x} ${y - 6 * s}l${1.8 * s} ${4.2 * s} ${4.2 * s} ${1.8 * s} ${-4.2 * s} ${1.8 * s} ${-1.8 * s} ${4.2 * s} ${-1.8 * s} ${-4.2 * s} ${-4.2 * s} ${-1.8 * s} ${4.2 * s} ${-1.8 * s}z`}
      fill={ACENTO}
      stroke="none"
    />
  );
}

// — El amanecer de la marca: abre y cierra el slideshow.
function Amanecer() {
  return (
    <Lienzo>
      <path d="M24 96h132" />
      <path d="M62 96a28 28 0 0 1 56 0" stroke={ACENTO} strokeWidth="2.6" />
      <circle cx="90" cy="87" r="6.5" fill={ACENTO} stroke="none" />
      {/* rayos */}
      <path d="M90 54V43M65 61l-7.5-7.5M115 61l7.5-7.5M52 80H39M128 80h13" stroke={ACENTO_PROFUNDO} strokeWidth="2.2" />
      {/* nubes suaves y colinas */}
      <path d="M34 40c6-4 13-4 19 0" opacity="0.45" />
      <path d="M124 32c7-4 15-4 22 0" opacity="0.45" />
      <path d="M28 112c16-7 34-7 50 0" opacity="0.35" />
      <path d="M102 112c16-7 34-7 50 0" opacity="0.35" />
    </Lienzo>
  );
}

// — Paso 1 · La carta del día llega a tu teléfono.
function Recibe() {
  return (
    <Lienzo>
      {/* teléfono */}
      <rect x="104" y="28" width="46" height="78" rx="9" />
      <path d="M119 36h16" opacity="0.5" />
      <circle cx="127" cy="95" r="2.6" fill={LINEA} stroke="none" />
      {/* la carta en viaje, con el amanecer de la marca */}
      <g transform="rotate(-8 52 64)">
        <rect x="28" y="48" width="48" height="34" rx="4" fill="var(--soft-ivory)" />
        <path d="M28 51l24 15 24-15" />
        <circle cx="52" cy="73" r="3.4" fill={ACENTO} stroke="none" />
      </g>
      {/* líneas de viaje */}
      <path d="M8 46h13M4 62h11M10 78h9" stroke={ACENTO_PROFUNDO} strokeWidth="2.2" />
      {/* sol asomando */}
      <path d="M118 14c5-6 14-6 19 0" stroke={ACENTO} strokeWidth="2" />
    </Lienzo>
  );
}

// — Paso 2 · Vives la pausa lejos del móvil, a tu manera.
function Pausa() {
  return (
    <Lienzo>
      {/* la persona, en calma */}
      <circle cx="96" cy="42" r="10" />
      <path d="M80 94c0-22 6-34 16-34s16 12 16 34" />
      {/* piernas cruzadas */}
      <path d="M64 100c9-9 18-12 32-12s23 3 32 12" />
      <path d="M64 100h64" />
      {/* la respiración */}
      <path d="M118 34c3-2 6-2 9 0" stroke={ACENTO} strokeWidth="2" />
      <path d="M119 41c4-2.4 8-2.4 12 0" stroke={ACENTO} strokeWidth="2" opacity="0.7" />
      {/* suelo */}
      <path d="M52 110h84" opacity="0.5" />
      {/* el teléfono quedó lejos, boca abajo */}
      <rect x="16" y="101" width="22" height="9" rx="3" />
      {/* el momento para ti */}
      <Destello x={52} y={34} />
      <Destello x={140} y={58} s={0.75} />
    </Lienzo>
  );
}

// — Paso 3 · Escribes en tu diario físico lo que sentiste.
function Diario() {
  return (
    <Lienzo>
      {/* mesa */}
      <path d="M16 110h148" opacity="0.4" />
      {/* cuaderno abierto */}
      <path d="M40 66c14-7 28-7 42-2 14-5 28-5 42 2" />
      <path d="M40 66v36c14-7 28-7 42-2 14-5 28-5 42 2V66" />
      <path d="M82 64v36" />
      {/* lo escrito */}
      <path d="M50 76h22M50 84h18M50 92h20" stroke={ACENTO_PROFUNDO} strokeWidth="2" />
      {/* el lápiz, escribiendo la página derecha */}
      <path d="M104 90l24-30" strokeWidth="2.6" />
      <path d="M104 90l-4.5 6.5 7-2.2z" fill={ACENTO} stroke="none" />
      <path d="M124 56l6.5 5" />
      {/* una taza acompañando */}
      <path d="M146 94h16v7a8 8 0 0 1-16 0z" />
      <path d="M151 84c-1.5 3 1.5 4 0 7M158 84c-1.5 3 1.5 4 0 7" opacity="0.5" />
    </Lienzo>
  );
}

// — Paso 4 · Guardas la experiencia en tu Baúl.
function Guarda() {
  return (
    <Lienzo>
      {/* baúl */}
      <rect x="52" y="74" width="76" height="38" rx="6" />
      <path d="M52 74c0-9 76-9 76 0" />
      <circle cx="90" cy="88" r="2.8" fill={ACENTO} stroke="none" />
      {/* la carta bajando */}
      <g transform="rotate(-6 90 28)">
        <rect x="70" y="14" width="40" height="27" rx="4" fill="var(--soft-ivory)" />
        <circle cx="90" cy="25" r="4.2" fill={ACENTO} stroke="none" />
        <path d="M80 33h20" stroke={ACENTO_PROFUNDO} strokeWidth="1.8" />
      </g>
      <path d="M90 48v12" stroke={ACENTO_PROFUNDO} strokeWidth="2.2" />
      <path d="M85 56l5 7 5-7" stroke={ACENTO_PROFUNDO} strokeWidth="2.2" />
      {/* lo que se va juntando brilla */}
      <Destello x={38} y={62} s={0.7} />
      <Destello x={142} y={56} s={0.85} />
    </Lienzo>
  );
}

// — Paso 5 · La compartes con tus seres queridos.
function Comparte() {
  return (
    <Lienzo>
      {/* la carta-regalo */}
      <g transform="rotate(-6 44 60)">
        <rect x="20" y="44" width="48" height="34" rx="4" fill="var(--soft-ivory)" />
        <path
          d="M44 70c-5-3.5-8-6.5-8-9.6a4.4 4.4 0 0 1 8-2.6 4.4 4.4 0 0 1 8 2.6c0 3.1-3 6.1-8 9.6z"
          fill={ACENTO}
          stroke="none"
        />
      </g>
      {/* el viaje del regalo */}
      <path d="M76 50c18-15 34-17 50-7" strokeDasharray="4 6" stroke={ACENTO_PROFUNDO} strokeWidth="2.2" />
      <path d="M120 38l9 6-10 3.5" stroke={ACENTO_PROFUNDO} strokeWidth="2.2" />
      {/* quienes lo reciben */}
      <circle cx="128" cy="72" r="9" />
      <path d="M112 110c0-14 7-19 16-19s16 5 16 19" />
      <circle cx="155" cy="79" r="7" />
      <path d="M143 110c0-11 5.5-15 12-15s12 4 12 15" />
    </Lienzo>
  );
}

export function StoryArt({ escena }: { escena: Escena }) {
  switch (escena) {
    case "amanecer":
      return <Amanecer />;
    case "recibe":
      return <Recibe />;
    case "pausa":
      return <Pausa />;
    case "diario":
      return <Diario />;
    case "guarda":
      return <Guarda />;
    case "comparte":
      return <Comparte />;
  }
}

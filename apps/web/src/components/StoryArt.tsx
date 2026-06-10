// Viñetas del onboarding (WS14): 5 ilustraciones de línea fina, dibujadas inline
// para poder usar las variables de color del tema (línea umber + acento sage).
// Estilo: trazo 2px redondeado, sin rellenos salvo el acento, mucho aire.

export type Escena = "recibe" | "pausa" | "diario" | "guarda" | "comparte";

const LINEA = "var(--deep-umber)";
const ACENTO = "var(--sage)";
const ACENTO_PROFUNDO = "var(--sage-deep)";

function Lienzo({ children }: { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      stroke={LINEA}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      {children}
    </svg>
  );
}

// 1 · Recibes una carta en el teléfono.
function Recibe() {
  return (
    <Lienzo>
      <rect x="20" y="18" width="24" height="40" rx="5" />
      <circle cx="32" cy="51" r="1.6" fill={LINEA} stroke="none" />
      {/* la carta entrando, con el amanecer de la marca */}
      <g transform="rotate(8 44 10)">
        <rect x="35" y="3" width="18" height="13" rx="2" fill="var(--soft-ivory)" />
        <circle cx="44" cy="8" r="2.4" fill={ACENTO} stroke="none" />
        <path d="M39 12h10" stroke={ACENTO_PROFUNDO} strokeWidth="1.5" />
      </g>
      <path d="M30 8c-3 1-5 3-6 6" stroke={ACENTO} strokeWidth="1.5" />
      <path d="M27 3c-5 2-8 5-9 10" stroke={ACENTO} strokeWidth="1.5" opacity="0.55" />
    </Lienzo>
  );
}

// 2 · Vives la pausa (respirar), lejos del teléfono.
function Pausa() {
  return (
    <Lienzo>
      <circle cx="30" cy="19" r="7" />
      <path d="M16 48c0-12 6-17 14-17s14 5 14 17" />
      {/* el aire que va y viene */}
      <path d="M44 16c2.5-1.6 5-1.6 7.5 0" stroke={ACENTO} strokeWidth="1.8" />
      <path d="M45 22c3-1.8 6-1.8 9 0" stroke={ACENTO} strokeWidth="1.8" opacity="0.7" />
      <path d="M12 54h40" stroke={LINEA} opacity="0.35" />
    </Lienzo>
  );
}

// 3 · Escribes en tu diario físico lo que sentiste.
function Diario() {
  return (
    <Lienzo>
      <path d="M8 22c8-4 16-4 24-1 8-3 16-3 24 1" />
      <path d="M8 22v24c8-4 16-4 24-1 8-3 16-3 24 1V22" />
      <path d="M32 21v24" />
      {/* lo escrito */}
      <path d="M14 30h11M14 36h9" stroke={ACENTO_PROFUNDO} strokeWidth="1.6" />
      {/* el lápiz sobre la página derecha */}
      <path d="M40 36 52 24" strokeWidth="2.2" />
      <path d="M40 36l-2.5 3 3-1z" fill={ACENTO} stroke="none" />
    </Lienzo>
  );
}

// 4 · La guardas en tu Baúl.
function Guarda() {
  return (
    <Lienzo>
      <rect x="14" y="34" width="36" height="18" rx="4" />
      <path d="M14 34c0-8 36-8 36 0" />
      <circle cx="32" cy="42" r="2" fill={ACENTO} stroke="none" />
      {/* la carta bajando */}
      <g transform="rotate(-6 32 10)">
        <rect x="25" y="4" width="14" height="10" rx="2" fill="var(--soft-ivory)" />
        <circle cx="32" cy="8" r="1.8" fill={ACENTO} stroke="none" />
      </g>
      <path d="M32 17v9" stroke={ACENTO_PROFUNDO} strokeWidth="1.8" />
      <path d="M29 23l3 4 3-4" stroke={ACENTO_PROFUNDO} strokeWidth="1.8" fill="none" />
    </Lienzo>
  );
}

// 5 · La compartes si quieres: el regalo viaja a otra persona.
function Comparte() {
  return (
    <Lienzo>
      <g transform="rotate(-4 21 30)">
        <rect x="8" y="22" width="22" height="16" rx="2" fill="var(--soft-ivory)" />
        <path
          d="M19 33c-2.6-1.8-4-3.4-4-5a2.3 2.3 0 0 1 4-1.5 2.3 2.3 0 0 1 4 1.5c0 1.6-1.4 3.2-4 5z"
          fill={ACENTO}
          stroke="none"
        />
      </g>
      {/* el viaje del regalo */}
      <path d="M34 28c7-6 12-6 18-2" stroke={ACENTO_PROFUNDO} strokeWidth="1.8" strokeDasharray="3 4" />
      <path d="M50 22l3 4-5 .5" stroke={ACENTO_PROFUNDO} strokeWidth="1.8" fill="none" />
      {/* quien lo recibe */}
      <circle cx="50" cy="40" r="5" />
      <path d="M41 56c0-8 4.5-11 9-11s9 3 9 11" />
    </Lienzo>
  );
}

export function StoryArt({ escena }: { escena: Escena }) {
  switch (escena) {
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

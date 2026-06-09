// Tour guiado (cierre del onboarding · canon M1). En lugar de una pantalla aparte,
// recorremos el FUNNEL REAL de ejemplo (Hoy → Reflexionar → Cierre → Compartir)
// y en cada paso un recuadro (Spotlight) señala el botón/elemento que toca.
//
// Mientras el tour está activo, las pantallas reales entran en "modo tutorial":
// usan una carta de ejemplo y NO escriben nada en la base (no toca el Baúl).
// Nada se persiste; al terminar, el usuario entra a su Hoy real con el Baúl vacío.

import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { Carta } from "./lib/types";

// id centinela que viaja en las rutas del tour: /reflexionar/tutorial, etc.
export const TOUR_ID = "tutorial";

// Carta de ejemplo: datos reales del Motor de Contenido (M0 · calma + respirar).
// A propósito NO es "escribir": la pausa es la excusa para detenerse; el escribir
// va aparte, en el diario físico.
export const CARTA_DEMO: Carta = {
  id: "tutorial-demo",
  frase: "Respirar es volver a estar aquí.",
  prompt: "Haz diez respiraciones lentas, sintiendo cómo el aire entra y sale.",
  categoria: {
    slug: "calma",
    nombre: "Calma",
    color_accent: "#becdd7",
    color_text: "#757f85",
    img: "assets/categorias/cat_calma.png",
  },
  accion: {
    slug: "respirar",
    nombre: "Respirar",
    glifo: "assets/acciones/act_respirar.svg",
  },
};

export interface PasoTour {
  route: string | null; // ruta donde vive este paso (null = se queda donde está)
  target: string | null; // selector del elemento a resaltar (null = recuadro centrado)
  titulo: string;
  cuerpo: string;
  cta?: string; // etiqueta del botón de avance (default "Siguiente")
  final?: boolean;
}

// Los 11 pasos, en el orden del ritual real.
export const TOUR_STEPS: PasoTour[] = [
  {
    route: "/hoy",
    target: '[data-tour="home-card"]',
    titulo: "Tu carta del día",
    cuerpo: "Cada día recibes una. Tócala para abrirla y descubrir tu pausa.",
  },
  {
    route: "/hoy",
    target: '[data-tour="reflect-btn"]',
    titulo: "Vive tu pausa, lejos del teléfono",
    cuerpo:
      "La carta te propone una pausa para vivir sin el teléfono. Al terminarla, escribe en tu diario lo que despertó en ti. Cuando vuelvas, toca Reflexionar.",
  },
  {
    route: `/reflexionar/${TOUR_ID}`,
    target: '[data-tour="refl-text"]',
    titulo: "Registra lo que sentiste",
    cuerpo: "Anota lo que despertó en ti. Una palabra, una frase… o nada. Esto es tuyo.",
  },
  {
    route: `/reflexionar/${TOUR_ID}`,
    target: '[data-tour="refl-stars"]',
    titulo: "¿Cuánto te llegó?",
    cuerpo: "Si quieres, puntúa la pausa. Es opcional y solo para ti.",
  },
  {
    route: `/reflexionar/${TOUR_ID}`,
    target: '[data-tour="refl-photo"]',
    titulo: "Súmale una foto",
    cuerpo: "Puedes conmemorar el momento con una foto. También es opcional.",
  },
  {
    route: `/reflexionar/${TOUR_ID}`,
    target: '[data-tour="refl-save"]',
    titulo: "Guárdala en tu Baúl",
    cuerpo:
      "Tu Baúl es tu colección privada de pausas vividas. Vuelves a ellas cuando quieras.",
  },
  {
    route: `/cierre/${TOUR_ID}`,
    target: '[data-tour="send-btn"]',
    titulo: "Y si quieres, compártela",
    cuerpo:
      "Puedes regalarle esta carta a alguien. Es un gesto: no hace falta que tenga la app.",
  },
  {
    route: `/compartir/${TOUR_ID}`,
    target: '[data-tour="share-note"]',
    titulo: "Escribe un mensaje",
    cuerpo: "Acompaña la carta con una nota personal para quien la reciba.",
  },
  {
    route: `/compartir/${TOUR_ID}`,
    target: '[data-tour="share-generate"]',
    titulo: "Genera el enlace",
    cuerpo: "Se crea un enlace único. Quien lo abra verá tu regalo sin instalar nada.",
  },
  {
    route: `/compartir/${TOUR_ID}`,
    target: '[data-tour="share-link"]',
    titulo: "Envíalo por donde quieras",
    cuerpo: "Copia el enlace y mándalo por WhatsApp, mail o donde prefieras.",
  },
  {
    route: null,
    target: null,
    titulo: "Ya sabes cómo funciona",
    cuerpo:
      "Esto fue una prueba, no se guardó nada. Mañana te espera tu primera carta real.",
    cta: "Empezar",
    final: true,
  },
];

// índice del paso donde Compartir ya muestra el enlace generado.
export const PASO_SHARE_LINK = 9;

interface TutorialState {
  activo: boolean;
  paso: number;
  steps: PasoTour[];
  start: () => void;
  stop: () => void;
  next: () => void;
  prev: () => void;
}

const Ctx = createContext<TutorialState | null>(null);

export function TutorialProvider({ children }: { children: ReactNode }) {
  const [activo, setActivo] = useState(false);
  const [paso, setPaso] = useState(0);

  const start = useCallback(() => {
    setPaso(0);
    setActivo(true);
  }, []);
  const stop = useCallback(() => {
    setActivo(false);
    setPaso(0);
  }, []);
  const next = useCallback(
    () => setPaso((p) => Math.min(p + 1, TOUR_STEPS.length - 1)),
    [],
  );
  const prev = useCallback(() => setPaso((p) => Math.max(p - 1, 0)), []);

  const value = useMemo(
    () => ({ activo, paso, steps: TOUR_STEPS, start, stop, next, prev }),
    [activo, paso, start, stop, next, prev],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTutorial(): TutorialState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useTutorial fuera de TutorialProvider");
  return v;
}

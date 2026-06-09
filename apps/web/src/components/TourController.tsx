// Orquesta el tour: mantiene la ruta sincronizada con el paso actual y monta el
// Spotlight encima. Vive dentro del Router (en App), por eso puede navegar.

import { useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useTutorial } from "../tutorial";
import { Spotlight } from "./Spotlight";

export function TourController() {
  const { activo, paso, steps, next, prev, stop } = useTutorial();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const ultimaRuta = useRef<string | null>(null);

  const step = steps[paso];

  // Sincroniza la ruta con el paso (solo cuando cambia, para no pelear con el router).
  useEffect(() => {
    if (!activo || !step?.route) return;
    if (pathname !== step.route && ultimaRuta.current !== step.route) {
      ultimaRuta.current = step.route;
      navigate(step.route);
    }
    if (pathname === step.route) ultimaRuta.current = step.route;
  }, [activo, step, pathname, navigate]);

  if (!activo || !step) return null;

  const esFinal = !!step.final;

  const onNext = () => {
    if (esFinal) {
      stop();
      navigate("/hoy", { replace: true });
    } else {
      next();
    }
  };

  const onSkip = () => {
    stop();
    navigate("/hoy", { replace: true });
  };

  return (
    <Spotlight
      key={paso}
      targetSelector={step.target}
      titulo={step.titulo}
      cuerpo={step.cuerpo}
      paso={paso}
      total={steps.length}
      esFinal={esFinal}
      ctaSiguiente={step.cta || "Siguiente"}
      onNext={onNext}
      onPrev={prev}
      onSkip={onSkip}
    />
  );
}

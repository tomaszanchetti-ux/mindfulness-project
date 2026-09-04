// WS24 · A2.1 · "Apoya Dwellia": qué incluye premium (8,99 €/año) + botón que abre
// Stripe Checkout.
//
// Tono (canon de marca): se invita, nunca se exige. La pantalla no vende una lista
// de funciones — cuenta que el aporte sostiene un lugar sin anuncios ni feed, y de
// paso enumera lo que se abre. Cero urgencia, cero contadores, cero "¡mejora ya!".
//
// Tres estados, uno solo visible a la vez:
//   premium            → gracias + "Gestionar suscripción" (portal de Stripe)
//   free, configurado  → "Apoyar Dwellia · 8,99 €/año" (abre el Checkout)
//   free, sin Stripe   → botón apagado + "muy pronto" (así es local y cualquier
//                        entorno sin MINDFUL_STRIPE_SECRET_KEY: la pantalla se ve entera)

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { api } from "../lib/api";
import { useStore } from "../store";
import "./premium.css";

// Lo que abre el aporte. `pronto` = ya está decidido y llega en los próximos
// bloques (cartas de la comunidad = Bloque B; recomendaciones = Bloque C).
const INCLUYE: { nombre: string; texto: string; pronto?: boolean }[] = [
  {
    nombre: "Cambiar la carta del día",
    texto:
      "Hasta tres veces. Si la de hoy no es la tuya, pides otra y sigues con tu pausa.",
  },
  {
    nombre: "Reflexiones más largas",
    texto: "Hasta 500 caracteres, cuando lo que sentiste no entra en dos líneas.",
  },
  {
    nombre: "Tres fotos por Pausa",
    texto: "El lugar, la luz, lo que estaba pasando: hasta tres imágenes tuyas.",
  },
  {
    nombre: "Compartir el ejercicio completo",
    texto: "No solo la carta: también lo que escribiste y tus fotos, con quien elijas.",
  },
  {
    nombre: "Escribir cartas para la comunidad",
    texto: "Tus palabras pueden ser la pausa de alguien más, con tu apodo o en anónimo.",
    pronto: true,
  },
  {
    nombre: "Recomendaciones en tu perfil",
    texto: "Los libros, videos y podcasts que a ti te hicieron bien.",
    pronto: true,
  },
];

// "hasta el 4 de septiembre de 2027" — fecha larga, en español, sin hora.
export function fechaLarga(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("es-ES", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export function Premium() {
  const navigate = useNavigate();
  const { perfil } = useStore();
  // null = todavía no sabemos si el cobro está encendido en este entorno.
  const [configurado, setConfigurado] = useState<boolean | null>(null);
  const [abriendo, setAbriendo] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  useEffect(() => {
    let vivo = true;
    api
      .pagosEstado()
      .then((e) => vivo && setConfigurado(e.configurado))
      // Si ni siquiera podemos preguntar, tratamos el cobro como apagado:
      // la pantalla se lee igual y nadie choca contra un botón que no funciona.
      .catch(() => vivo && setConfigurado(false));
    return () => {
      vivo = false;
    };
  }, []);

  const esPremium = perfil?.plan === "premium";

  // Checkout y portal devuelven una URL de Stripe: se sale de la app hacia allí.
  // Si falla, el aviso lo escribimos nosotros: el `detail` de la API está en
  // idioma de sistema ("Pagos no configurados") y no es lo que lee un usuario.
  const irA = async (pedirUrl: () => Promise<{ url: string }>, falla: string) => {
    setAbriendo(true);
    setAviso(null);
    try {
      const { url } = await pedirUrl();
      window.location.href = url;
    } catch (e) {
      const status = (e as Error & { status?: number }).status;
      setAviso(status === 409 ? "Todavía no hay una suscripción que gestionar." : falla);
      setAbriendo(false);
    }
  };

  return (
    <div className="premium">
      <button className="back-link" onClick={() => (history.length > 1 ? navigate(-1) : navigate("/perfil"))}>
        ← Volver
      </button>

      <div className="screen-head">
        <p className="screen-kicker">Dwellia premium</p>
        <h1 className="screen-title">Apoya Dwellia</h1>
        <div className="premium-precio">
          <span className="premium-precio-cifra">8,99 €</span>
          <span className="premium-precio-periodo">al año</span>
        </div>
        <p className="premium-precio-nota">Menos de un café al mes.</p>
      </div>

      <div className="premium-porque">
        <p>
          Dwellia no tiene anuncios, ni feed, ni likes, ni nada que hacer con tus
          datos. Una carta al día y el silencio alrededor: eso es todo, y es a
          propósito.
        </p>
        <p>
          Ese silencio lo sostienen las personas que aportan. Si quieres ser una de
          ellas, esto es lo que se abre para ti.
        </p>
      </div>

      <div className="profile-section" style={{ marginTop: 22 }}>
        <h3>Lo que incluye</h3>
        <ul className="premium-lista">
          {INCLUYE.map((f) => (
            <li key={f.nombre} className={`premium-item ${f.pronto ? "es-pronto" : ""}`}>
              <span className="premium-item-glifo" aria-hidden="true" />
              <div>
                <p className="premium-item-nombre">
                  {f.nombre}
                  {f.pronto && <span className="premium-pronto">pronto</span>}
                </p>
                <p className="premium-item-texto">{f.texto}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {esPremium ? (
        <>
          <div className="premium-vigente">
            <p className="premium-vigente-titulo">
              Ya eres parte de Dwellia premium
              {perfil?.plan_hasta ? ` hasta el ${fechaLarga(perfil.plan_hasta)}` : ""}.
            </p>
            <p className="premium-vigente-texto">
              Gracias por sostener este lugar. Las funciones de arriba ya son tuyas.
            </p>
          </div>
          <div className="premium-cta">
            {aviso && <p className="premium-aviso">{aviso}</p>}
            <div className="actions-stack">
              <Button
                variant="secondary"
                full
                disabled={abriendo}
                onClick={() =>
                  irA(
                    api.pagosPortal,
                    "No pudimos abrir la gestión de tu suscripción. Inténtalo en un rato.",
                  )
                }
              >
                {abriendo ? "Abriendo…" : "Gestionar suscripción"}
              </Button>
            </div>
          </div>
        </>
      ) : (
        <div className="premium-cta">
          {aviso && <p className="premium-aviso">{aviso}</p>}
          <div className="actions-stack">
            <Button
              full
              disabled={configurado !== true || abriendo}
              onClick={() =>
                irA(api.pagosCheckout, "No pudimos abrir el pago. Inténtalo en un rato.")
              }
            >
              {abriendo ? "Abriendo…" : "Apoyar Dwellia · 8,99 €/año"}
            </Button>
          </div>
          {configurado === false ? (
            <p className="premium-cta-nota">
              Muy pronto podrás apoyar Dwellia desde aquí.
            </p>
          ) : (
            <p className="premium-cta-nota">
              Se renueva una vez al año y puedes cancelarlo cuando quieras, sin dar
              explicaciones. Mientras tanto, el método Dwellia sigue completo y
              gratuito.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

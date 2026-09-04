// WS24 · A2.1 · "Apoya Dwellia": qué incluye premium (8,99 €/año) + botón que abre
// Stripe Checkout.
//
// Tono (canon de marca): se invita, nunca se exige. La pantalla no vende una lista
// de funciones — cuenta que el aporte sostiene un lugar sin anuncios ni feed, y de
// paso enumera lo que se abre. Cero urgencia, cero contadores, cero "¡mejora ya!".
//
// Tres estados, uno solo visible a la vez (WS25 · R5):
//   premium            → gracias + "Quiero dejar la comunidad" (portal de Stripe)
//   free, configurado  → "Quiero ser parte" (abre el Checkout) + la nota de renovación
//   free, sin Stripe   → el mismo botón, apagado y SIN texto debajo (así es local y
//                        cualquier entorno sin MINDFUL_STRIPE_SECRET_KEY: la pantalla
//                        se ve entera, sin prometer nada)

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { api } from "../lib/api";
import { useStore } from "../store";
import "./premium.css";

// WS25 · R4 · lo que abre el aporte. Cinco cosas, sin píldoras de "pronto":
// lo que está en esta lista es lo que se recibe al ser parte.
const INCLUYE: { nombre: string; texto: string }[] = [
  {
    nombre: "Cambiar la carta del día",
    texto:
      "Hasta tres veces. Si la de hoy no es la tuya, pides otra y sigues con tu Pausa.",
  },
  {
    nombre: "Reflexiones más largas",
    texto:
      "Hasta 500 caracteres, para esos momentos donde sientes que quieres compartir más.",
  },
  {
    nombre: "Tres fotos por Pausa",
    texto: "El lugar, la luz, lo que estaba pasando: hasta tres imágenes tuyas.",
  },
  {
    nombre: "Compartir más contenido",
    texto:
      "Recomendaciones en tu perfil de libros, videos y podcasts que te hicieron bien, para aportar a la comunidad.",
  },
  {
    nombre: "Escribir cartas para la comunidad",
    texto: "Tus palabras pueden ser la Pausa de alguien más, con tu apodo o en anónimo.",
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
          Dwellia no tiene anuncios y no hace uso económico de tus datos. Aquí se
          busca crear una comunidad de personas que aprecian el verdadero valor de
          una Pausa diaria.
        </p>
        <p>
          Esta comunidad la sostienen personas como tú, que quieren lograr una mayor
          conexión consigo mismas. Gracias.
        </p>
      </div>

      <div className="profile-section" style={{ marginTop: 22 }}>
        <h3>Lo que incluye</h3>
        <ul className="premium-lista">
          {INCLUYE.map((f) => (
            <li key={f.nombre} className="premium-item">
              <span className="premium-item-glifo" aria-hidden="true" />
              <div>
                <p className="premium-item-nombre">{f.nombre}</p>
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
                {abriendo ? "Abriendo…" : "Quiero dejar la comunidad"}
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
              {/* el precio ya se lee arriba: el botón solo invita */}
              {abriendo ? "Abriendo…" : "Quiero ser parte"}
            </Button>
          </div>
          {/* Sin Stripe (o mientras se pregunta) el botón queda apagado y no se
              promete nada debajo: nada de "muy pronto". */}
          {configurado === true && (
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

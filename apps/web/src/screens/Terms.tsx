// Términos y privacidad (WS20 · v3 en WS30/C3: comunidad, perfil público,
// cartas y recomendaciones de la comunidad). Ruta PÚBLICA: se llega desde el check del
// onboarding (target _blank, para no perder el wizard) y desde el Perfil.
// Texto corto y honesto, en cristiano — sin boilerplate legal vacío.

import { useNavigate } from "react-router-dom";

const ACTUALIZADO = "7 de septiembre de 2026";
const CONTACTO = "tomaszanchetti@gmail.com";

export function Terms() {
  const navigate = useNavigate();
  return (
    <div className="terms-doc">
      <button className="back-link" onClick={() => (history.length > 1 ? navigate(-1) : navigate("/"))}>
        ← Volver
      </button>

      <h2>Términos y privacidad</h2>
      <p className="meta">Última actualización: {ACTUALIZADO}</p>

      <section>
        <h3>Qué es Dwellia</h3>
        <p>
          Dwellia te trae una carta al día con una invitación a hacer una pausa fuera
          del teléfono y escribir en tu diario lo que sentiste. La app es la guía y el
          baúl de tus pausas. También puedes tener una comunidad: personas con las que
          decides compartir algunas de tus pausas. No es una red social: no hay feed,
          no hay likes ni contadores, y nadie ve lo tuyo salvo que tú lo compartas.
        </p>
      </section>

      <section>
        <h3>Qué datos guardamos</h3>
        <p>
          <b>Tu cuenta:</b> el correo con el que inicias sesión, tu nombre, tu apodo y,
          si la pones, tu foto de perfil. <b>Tus preferencias:</b> horario y zona
          horaria, si quieres el aviso diario y si tu perfil es público. <b>Tus
          pausas:</b> las reflexiones, valoraciones y fotos que decidas guardar en tu
          Baúl. <b>Tu comunidad:</b> a quién enviaste o aceptaste una solicitud, qué
          pausas reenviaste o guardaste, y las cartas y recomendaciones que escribas.
          <b>Si eres parte:</b> el estado de tu suscripción; el pago lo gestiona Stripe
          y nosotros no vemos ni guardamos los datos de tu tarjeta. No pedimos ni
          guardamos nada más.
        </p>
      </section>

      <section>
        <h3>Para qué los usamos</h3>
        <p>
          Solo para que la app funcione: elegir tu carta de cada día, guardar tu Baúl y
          — si lo activaste — enviarte el aviso diario como notificación en tu
          dispositivo. No vendemos ni
          compartimos tus datos con nadie, no hay publicidad y no usamos rastreadores
          de terceros. La base legal es tu consentimiento, que das al aceptar estos
          términos y puedes retirar cuando quieras.
        </p>
      </section>

      <section>
        <h3>Dónde viven tus datos</h3>
        <p>
          En servidores de Google Cloud en la Unión Europea (Bélgica). El acceso a tus
          datos está aislado por cuenta: solo tú ves lo tuyo. Tus fotos se guardan en
          un espacio privado que jamás es público.
        </p>
      </section>

      <section>
        <h3>Compartir es decisión tuya</h3>
        <p>
          Cada pausa nace privada. Si la marcas como compartida, la ven las personas de
          tu comunidad (y, si pusiste tu perfil en público, cualquier persona con cuenta
          en Dwellia): la carta, tu reflexión, tus fotos y tu apodo; nunca tu diario ni
          tus valoraciones. Puedes volverla privada cuando quieras y desaparece de la
          vista de todos, también de quien la había guardado. Tu perfil es privado por
          defecto: te pueden encontrar por tu apodo, nombre o correo, pero solo ven tus
          pausas quienes aceptaste. Si generas un enlace para regalar una pausa,
          cualquier persona que tenga ese enlace podrá verla; el enlace no aparece en
          buscadores y se apaga si borras la pausa.
        </p>
      </section>

      <section>
        <h3>Lo que escribes para la comunidad</h3>
        <p>
          Si eres parte y escribes una carta, nos das permiso para revisarla, pedirte
          un retoque y, si se aprueba, entregarla como carta del día a otras personas
          con tu apodo o de forma anónima, como elijas. Las cartas aprobadas quedan en
          Dwellia aunque más adelante borres tu cuenta, sin tu nombre. Las
          recomendaciones son opiniones personales de quien las escribe, no un consejo
          de Dwellia; si un enlace lleva fuera de la app, ese sitio tiene sus propias
          reglas. Podemos retirar cualquier carta, recomendación o pausa compartida que
          falte al respeto o no encaje con el espíritu de Dwellia, y te lo diremos.
        </p>
      </section>

      <section>
        <h3>Tus derechos (RGPD)</h3>
        <p>
          Puedes acceder, corregir y borrar tus datos. Tu nombre, apodo, foto, horario
          y preferencias se editan desde tu Perfil. Cada pausa del Baúl se puede
          eliminar para siempre — eso borra también sus fotos y su enlace compartido,
          sin copias. Puedes quitar a alguien de tu comunidad cuando quieras. Si
          eliminas tu cuenta, se borra todo lo tuyo, incluido lo que habías compartido
          y tus recomendaciones; solo permanecen, sin tu nombre, las cartas de la
          comunidad ya aprobadas. Para eliminar tu cuenta completa o ejercer cualquier
          otro derecho, escríbenos a <b>{CONTACTO}</b> y lo resolvemos.
        </p>
      </section>

      <section>
        <h3>Tu parte</h3>
        <p>
          Usa Dwellia para ti, con tu cuenta, y siendo mayor de 16 años. En la
          comunidad, trata a las personas como querrías que te traten: lo que compartes,
          escribes o recomiendas es tuyo y respondes por ello. Si algún día cambian
          estos términos de forma relevante, te lo contaremos dentro de la app antes de
          que apliquen.
        </p>
      </section>
    </div>
  );
}

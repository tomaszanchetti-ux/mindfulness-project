// Términos y privacidad (WS20). Ruta PÚBLICA: se llega desde el check del
// onboarding (target _blank, para no perder el wizard) y desde el Perfil.
// Texto corto y honesto, en cristiano — sin boilerplate legal vacío.

import { useNavigate } from "react-router-dom";

const ACTUALIZADO = "11 de junio de 2026";
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
          baúl de tus pausas — no es una red social: no hay feed, no hay likes y nadie
          ve lo tuyo.
        </p>
      </section>

      <section>
        <h3>Qué datos guardamos</h3>
        <p>
          <b>Tu cuenta:</b> el correo con el que inicias sesión, tu nombre y tu apodo.{" "}
          <b>Tus preferencias:</b> actividades elegidas, horario y zona horaria, y si
          quieres el aviso diario. <b>Tus pausas:</b> las reflexiones, valoraciones y
          fotos que decidas guardar en tu Baúl. No pedimos ni guardamos nada más.
        </p>
      </section>

      <section>
        <h3>Para qué los usamos</h3>
        <p>
          Solo para que la app funcione: elegir tu carta de cada día, guardar tu Baúl y
          — si lo activaste — enviarte el aviso diario por correo. No vendemos ni
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
          Si generas un enlace para regalar una carta, cualquier persona que tenga ese
          enlace podrá verla junto con tu nota y tu apodo. El enlace no aparece en
          buscadores, pero es público para quien lo reciba. Si borras la pausa, el
          enlace de esa pausa se apaga.
        </p>
      </section>

      <section>
        <h3>Tus derechos (RGPD)</h3>
        <p>
          Puedes acceder, corregir y borrar tus datos. Tu nombre, apodo, horario y
          preferencias se editan desde tu Perfil. Cada pausa del Baúl se puede eliminar
          para siempre — eso borra también sus fotos y su enlace compartido, sin copias.
          Para eliminar tu cuenta completa o ejercer cualquier otro derecho, escríbenos
          a <b>{CONTACTO}</b> y lo resolvemos.
        </p>
      </section>

      <section>
        <h3>Tu parte</h3>
        <p>
          Usa Dwellia para ti, con tu cuenta, y siendo mayor de 16 años. Si algún día
          cambian estos términos de forma relevante, te lo contaremos dentro de la app
          antes de que apliquen.
        </p>
      </section>
    </div>
  );
}

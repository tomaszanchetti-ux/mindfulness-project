// El método Dwellia (WS22) — la teoría del producto, en versión para usuarios.
// Derivada de M0_Motor_de_Contenido/fundamentos_pilares.md (el SoT teórico):
// la pausa de dos tiempos · la calma como camino · los seis pilares en anillos.
// Tono divulgativo y sereno; sin apellidos académicos; sin promesa terapéutica
// (canon S1: "se inspira en", jamás "trata/cura"). Se llega desde el Perfil y se
// menciona al cierre del onboarding — se lee cuando se quiere, nunca se obliga.

import { useNavigate } from "react-router-dom";
import { AnillosCirculo, PausaDosTiempos } from "../components/CirculosStory";
import { assetUrl } from "../lib/api";
import { useStore } from "../store";

// Los tres anillos, con la función de cada pilar contada en cristiano
// (la "pregunta-norte" de fundamentos_pilares.md, sin jerga).
const ANILLOS: { titulo: string; slugs: string[] }[] = [
  { titulo: "Hacia adentro", slugs: ["amor-propio", "sentido"] },
  { titulo: "Hacia tu experiencia", slugs: ["gratitud", "perspectiva"] },
  { titulo: "Hacia los demás y hacia adelante", slugs: ["vinculos", "resiliencia"] },
];

const FUNCION: Record<string, string> = {
  "amor-propio":
    "La base. Tratarte con el mismo cariño que repartes: desde ahí se crece, sin castigo.",
  sentido:
    "La dirección. Conectar lo de cada día con lo que de verdad te importa — la luna que orienta, reflejada en el agua quieta.",
  gratitud:
    "Volver a ver lo bueno que ya tienes y que la costumbre fue escondiendo.",
  perspectiva:
    "Mirar lo que pesa desde más lejos. Casi todo cambia de tamaño con la distancia.",
  resiliencia:
    "Tu relación con lo difícil: recordar lo que te sostuvo y sigue ahí.",
  vinculos:
    "Las personas que te hacen bien. Pocas cosas hacen crecer tanto como cuidar esos lazos.",
};

export function Metodo() {
  const navigate = useNavigate();
  const { categorias } = useStore();
  const porSlug = Object.fromEntries(categorias.map((c) => [c.slug, c]));

  return (
    <div className="metodo">
      <button className="back-link" onClick={() => navigate(-1)}>
        ← Volver
      </button>

      <div className="screen-head">
        <h1 className="screen-title">El método Dwellia</h1>
        <p className="meta">El porqué de tu pausa diaria, en tres ideas.</p>
      </div>

      <div className="profile-section">
        <h3>1 · La pausa de dos tiempos</h3>
        <div className="metodo-viz">
          <PausaDosTiempos />
        </div>
        <p className="metodo-text">
          Cada carta te propone una acción sencilla —contemplar, respirar, pasear,
          hacer— con una sola misión: llevarte a la calma. Y una vez allí, escribes
          en tu diario físico lo que sentiste.
        </p>
        <p className="metodo-text">
          La acción prepara; la escritura trabaja. Por eso toda carta, sea cual sea,
          termina en tu diario.
        </p>
      </div>

      <div className="profile-section">
        <h3>2 · La calma es el camino</h3>
        <p className="metodo-text">
          En Dwellia la calma no es un tema más: es el vehículo de todo el método.
          Como el agua — solo cuando se aquieta puedes ver el fondo. Las acciones de
          cada carta son, simplemente, maneras distintas de aquietar el agua.
        </p>
      </div>

      <div className="profile-section">
        <h3>3 · Seis pilares, tres círculos</h3>
        <div className="metodo-viz">
          <AnillosCirculo pilares={categorias} />
        </div>
        <p className="metodo-text">
          El crecimiento no es una lista: es un círculo que te rodea. Cada semana lo
          recorres entero — un pilar por día, más un día sorpresa. Tú no eliges cuál
          toca: dejar que te sorprenda es parte de la práctica.
        </p>

        {ANILLOS.map((an) => (
          <div key={an.titulo} className="metodo-anillo">
            <p className="metodo-anillo-titulo">{an.titulo}</p>
            {an.slugs.map((slug) => {
              const c = porSlug[slug];
              if (!c) return null;
              return (
                <div key={slug} className="metodo-pilar">
                  <img className="metodo-pilar-img" src={assetUrl(c.img)} alt="" />
                  <div>
                    <p className="metodo-pilar-nombre" style={{ color: c.color_text }}>
                      {c.nombre}
                    </p>
                    <p className="metodo-pilar-texto">{FUNCION[slug]}</p>
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>

      <div className="profile-section">
        <h3>De dónde viene</h3>
        <p className="metodo-text">
          Dwellia se inspira en tradiciones contemplativas milenarias y en la
          psicología del bienestar contemporánea: la gratitud que se escribe, la
          perspectiva que se toma, la amabilidad con uno mismo que se practica.
        </p>
        <p className="metodo-text">
          No es terapia ni la reemplaza. Es una práctica diaria, pequeña y tuya.
        </p>
      </div>
    </div>
  );
}

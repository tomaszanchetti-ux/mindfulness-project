// Perfil y configuración (§21). Ajustar la experiencia sin panel administrativo.
// Guardado automático cuando se puede (toggle de aviso, horario).

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { InstallIOSModal } from "../components/InstallIOSModal";
import { api, reiniciarDemo } from "../lib/api";
import { cerrarSesion } from "../lib/firebase";
import { useStore } from "../store";
import { canInstall, isIOS, isStandalone, promptInstall } from "../pwa";

export function Profile() {
  const navigate = useNavigate();
  const { perfil, categorias, acciones, refrescarPerfil } = useStore();
  const [hora, setHora] = useState("");
  const [aviso, setAviso] = useState(true);
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");
  const [apodo, setApodo] = useState("");
  const [installable, setInstallable] = useState(canInstall());
  const [verComoInstalar, setVerComoInstalar] = useState(false);

  useEffect(() => {
    const sync = () => setInstallable(canInstall());
    window.addEventListener("pwa:can-install", sync);
    window.addEventListener("pwa:installed", sync);
    return () => {
      window.removeEventListener("pwa:can-install", sync);
      window.removeEventListener("pwa:installed", sync);
    };
  }, []);

  useEffect(() => {
    if (perfil) {
      setHora(perfil.hora_aviso);
      setAviso(perfil.aviso_activo);
      setNombre(perfil.nombre ?? "");
      setApellido(perfil.apellido ?? "");
      setApodo(perfil.apodo ?? "");
    }
  }, [perfil]);

  if (!perfil) return <div className="center-note">…</div>;

  // WS10: actividades elegidas. Si no eligió ninguna todavía, valen todas.
  const misAcciones =
    perfil.acciones.length > 0
      ? acciones.filter((a) => perfil.acciones.includes(a.slug))
      : acciones;

  const guardarAviso = async (v: boolean) => {
    setAviso(v);
    await api.setPerfil({ aviso_activo: v });
    refrescarPerfil();
  };

  const guardarNombre = async () => {
    const v = nombre.trim();
    if (v && v !== perfil.nombre) {
      await api.setPerfil({ nombre: v });
      refrescarPerfil();
    }
  };

  const guardarApellido = async () => {
    const v = apellido.trim();
    if (v !== (perfil.apellido ?? "")) {
      await api.setPerfil({ apellido: v });
      refrescarPerfil();
    }
  };

  const guardarApodo = async () => {
    const v = apodo.trim();
    if (v && v !== perfil.apodo) {
      await api.setPerfil({ apodo: v });
      refrescarPerfil();
    }
  };

  const guardarHora = async (v: string) => {
    setHora(v);
    if (v) {
      await api.setPerfil({ hora_aviso: v });
      refrescarPerfil();
    }
  };

  return (
    <div className="profile">
      <div className="screen-head">
        <h1 className="screen-title">Perfil</h1>
      </div>

      <div className="profile-section">
        <h3>Cuenta</h3>
        <div className="profile-row">
          <span>Nombre</span>
          <input
            type="text"
            className="time-input"
            style={{ width: "auto", textAlign: "right" }}
            maxLength={80}
            placeholder="Tu nombre"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            onBlur={guardarNombre}
          />
        </div>
        <div className="profile-row">
          <span>Apellido</span>
          <input
            type="text"
            className="time-input"
            style={{ width: "auto", textAlign: "right" }}
            maxLength={80}
            placeholder="Opcional"
            value={apellido}
            onChange={(e) => setApellido(e.target.value)}
            onBlur={guardarApellido}
          />
        </div>
        <div className="profile-row">
          <span>Apodo</span>
          <input
            type="text"
            className="time-input"
            style={{ width: "auto", textAlign: "right" }}
            maxLength={40}
            placeholder="Cómo te llamamos"
            value={apodo}
            onChange={(e) => setApodo(e.target.value)}
            onBlur={guardarApodo}
          />
        </div>
        <div className="profile-row">
          <span>Email</span>
          <span className="val">{perfil.email}</span>
        </div>
        <div className="profile-row">
          <span>Zona horaria</span>
          <span className="val">{perfil.tz}</span>
        </div>
      </div>

      <div className="profile-section">
        <h3>Los pilares que recorres</h3>
        <div className="cat-pills">
          {categorias.map((c) => (
            <span key={c.slug} className="cat-pill">
              <span className="swatch" style={{ background: c.color_accent }} />
              {c.nombre}
            </span>
          ))}
        </div>
        <p className="meta" style={{ marginTop: 8 }}>
          Cada semana, Dwellia te lleva por los seis pilares del crecimiento — uno
          distinto cada día, más un día sorpresa.
        </p>
      </div>

      <div className="profile-section">
        <h3>Cómo complementas tu pausa</h3>
        <div className="cat-pills">
          {misAcciones.filter((a) => a.slug !== "escribir").length === 0 ? (
            <span className="cat-pill">Solo escritura, por ahora</span>
          ) : (
            misAcciones
              .filter((a) => a.slug !== "escribir")
              .map((a) => (
                <span key={a.slug} className="cat-pill">
                  {a.nombre}
                </span>
              ))
          )}
        </div>
        <p className="meta" style={{ marginTop: 8 }}>
          La escritura es la pausa misma: siempre presente. Estas actividades la
          disparan.
        </p>
      </div>

      <div className="profile-section">
        <h3>Tu pausa diaria</h3>
        <div className="profile-row">
          <span>Avisarme cada día</span>
          <span className="switch">
            <input
              type="checkbox"
              checked={aviso}
              onChange={(e) => guardarAviso(e.target.checked)}
            />
            <span className="slider" />
          </span>
        </div>
        <div className="profile-row">
          <span>Horario</span>
          <input
            type="time"
            className="time-input"
            style={{ width: "auto" }}
            value={hora}
            onChange={(e) => guardarHora(e.target.value)}
          />
        </div>
      </div>

      <div className="profile-section">
        <h3>Privacidad</h3>
        <p className="meta">Lo que escribes y tus fotos quedan solo para ti.</p>
        <button className="link" style={{ marginTop: 8 }} onClick={() => navigate("/terminos")}>
          Términos y política de privacidad
        </button>
      </div>

      {!isStandalone() && (
        <div className="profile-section">
          <h3>Instalar Dwellia</h3>
          {installable ? (
            <>
              <p className="meta">
                Tenla como app en tu teléfono, sin pasar por el navegador.
              </p>
              <div className="actions-stack" style={{ marginTop: 10 }}>
                <Button variant="secondary" full onClick={() => promptInstall()}>
                  Instalar app
                </Button>
              </div>
            </>
          ) : isIOS() ? (
            <>
              <p className="meta">
                Tenla como app en tu teléfono, sin pasar por el navegador.
              </p>
              <div className="actions-stack" style={{ marginTop: 10 }}>
                <Button variant="secondary" full onClick={() => setVerComoInstalar(true)}>
                  Cómo instalar
                </Button>
              </div>
            </>
          ) : (
            <p className="meta">
              Desde el menú del navegador (⋮) elige <b>Instalar app</b> o{" "}
              <b>Agregar a pantalla de inicio</b>.
            </p>
          )}
        </div>
      )}

      {verComoInstalar && <InstallIOSModal onClose={() => setVerComoInstalar(false)} />}

      {import.meta.env.DEV && (
        <div className="profile-section">
          <h3>Demo (solo dev)</h3>
          <p className="meta">
            Esto reinicia la demo desde cero: nueva cuenta vacía y el funnel completo
            otra vez, ideal para mostrársela a alguien de nuevo.
          </p>
          <div className="actions-stack" style={{ marginTop: 10 }}>
            <Button variant="secondary" full onClick={reiniciarDemo}>
              Reiniciar demo desde cero
            </Button>
          </div>
        </div>
      )}

      <div className="actions-stack" style={{ marginTop: 2 }}>
        <Button
          variant="tertiary"
          onClick={async () => {
            await cerrarSesion().catch(() => {});
            navigate("/login");
          }}
        >
          Cerrar sesión
        </Button>
      </div>
    </div>
  );
}

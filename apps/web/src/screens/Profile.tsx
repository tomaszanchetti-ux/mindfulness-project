// Perfil y configuración (§21). Ajustar la experiencia sin panel administrativo.
// Guardado automático cuando se puede (toggle de aviso, horario).

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { api, reiniciarDemo } from "../lib/api";
import { useStore } from "../store";

export function Profile() {
  const navigate = useNavigate();
  const { perfil, categorias, acciones, refrescarPerfil } = useStore();
  const [hora, setHora] = useState("");
  const [aviso, setAviso] = useState(true);
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");
  const [apodo, setApodo] = useState("");

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

  const misCategorias = categorias.filter((c) => perfil.categorias.includes(c.slug));
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
        <h3>Lo que cultivas</h3>
        <div className="cat-pills">
          {misCategorias.map((c) => (
            <span key={c.slug} className="cat-pill">
              <span className="swatch" style={{ background: c.color_accent }} />
              {c.nombre}
            </span>
          ))}
        </div>
      </div>

      <div className="profile-section">
        <h3>Cómo haces tu pausa</h3>
        <div className="cat-pills">
          {misAcciones.map((a) => (
            <span key={a.slug} className="cat-pill">
              {a.nombre}
            </span>
          ))}
        </div>
        <p className="meta" style={{ marginTop: 8 }}>
          Cada pausa es una excusa para sentir y escribirlo en tu diario.
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
      </div>

      <div className="profile-section">
        <h3>Demo</h3>
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

      <div className="actions-stack" style={{ marginTop: 2 }}>
        <Button variant="tertiary" onClick={() => navigate("/login")}>
          Cerrar sesión
        </Button>
      </div>
    </div>
  );
}

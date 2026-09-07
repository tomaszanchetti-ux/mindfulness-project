// Perfil (§21 · rehecho en WS25 · R6). Es la ficha de quien eres dentro de
// Dwellia, no un panel de ajustes: arriba el apodo con el que te conocen, y
// debajo, en este orden, tu Pausa diaria · instalar · tu plan · el método ·
// privacidad · cerrar sesión.
//
// Lo que cambia el ritual (toggle de aviso, horario) se guarda solo, en el acto.
// Lo que es tu identidad (apodo, nombre, apellido) se edita a propósito, en un
// panel que se abre con "Editar" y se confirma con "Guardar": nadie cambia su
// nombre sin querer.
//
// Fuera desde WS25: la zona horaria (la detecta el navegador y nadie la toca) y
// la vitrina de pilares (vive en "El método Dwellia").
//
// WS30 · C2.2 · arriba del todo suma tu FOTO (la que ve tu comunidad en las
// búsquedas y en tus fichas) y, junto al apodo, el toggle "Perfil público": la
// decisión de quién puede llegar a tus Pausas compartidas. Todo lo demás queda
// en el mismo orden de siempre.

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Avatar } from "../components/Avatar";
import { Button } from "../components/Button";
import { InstallIOSModal } from "../components/InstallIOSModal";
import { api, reiniciarDemo } from "../lib/api";
import { cerrarSesion } from "../lib/firebase";
import { useStore } from "../store";
import { canInstall, isIOS, isStandalone, promptInstall } from "../pwa";
import { activarPush, permisoPush, soportaPush, suscripcionActual } from "../lib/push";
import { fechaLarga } from "./Premium";
import "./premium.css";
import "./profile.css";
import "./baul.css";

// Lo que acepta la foto de perfil (el backend aplica lo mismo: FORMATOS_AVATAR
// y 8 MB). Se valida acá para no hacer subir 9 MB y recién entonces avisar.
const FORMATOS_FOTO = ["image/jpeg", "image/png", "image/webp"];
const FOTO_MAX_MB = 8;

export function Profile() {
  const navigate = useNavigate();
  const { perfil, refrescarPerfil } = useStore();
  const [hora, setHora] = useState("");
  const [aviso, setAviso] = useState(true);
  // Datos de identidad: se editan en el panel y solo viajan al confirmar.
  const [editando, setEditando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");
  const [apodo, setApodo] = useState("");
  const [installable, setInstallable] = useState(canInstall());
  // WS24 · "Tu plan": abrir el portal de Stripe puede fallar (503 sin Stripe,
  // 409 si nunca compró). Se avisa suave, en la misma sección.
  const [abriendoPortal, setAbriendoPortal] = useState(false);
  const [avisoPlan, setAvisoPlan] = useState<string | null>(null);
  const [verComoInstalar, setVerComoInstalar] = useState(false);
  // Estado del push EN ESTE dispositivo (WS21): el aviso diario llega por acá.
  const [push, setPush] = useState<"cargando" | "activas" | "pedir" | "bloqueadas" | "instalar" | "nosoporta">("cargando");
  const [activando, setActivando] = useState(false);
  // WS30 · C2.2 · la foto de perfil y el perfil público.
  const fotoRef = useRef<HTMLInputElement>(null);
  const [subiendoFoto, setSubiendoFoto] = useState(false);
  const [avisoFoto, setAvisoFoto] = useState<string | null>(null);
  const [publico, setPublico] = useState(false);
  const [guardandoPublico, setGuardandoPublico] = useState(false);

  useEffect(() => {
    if (!soportaPush()) {
      setPush(isIOS() && !isStandalone() ? "instalar" : "nosoporta");
      return;
    }
    if (permisoPush() === "denied") {
      setPush("bloqueadas");
      return;
    }
    suscripcionActual().then((sub) =>
      setPush(sub && permisoPush() === "granted" ? "activas" : "pedir"),
    );
  }, []);

  const activarNotificaciones = async () => {
    setActivando(true);
    try {
      const ok = await activarPush();
      setPush(ok ? "activas" : permisoPush() === "denied" ? "bloqueadas" : "pedir");
    } catch {
      setPush("pedir");
    } finally {
      setActivando(false);
    }
  };

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
      // Si nunca eligió apodo, el nombre hace de apodo (igual que el onboarding).
      setApodo(perfil.apodo ?? perfil.nombre ?? "");
      setPublico(perfil.perfil_publico);
    }
  }, [perfil]);

  if (!perfil) return <div className="center-note">…</div>;

  // El nombre grande de la cabecera: el apodo manda; si no hay, el nombre.
  const comoTeLlaman = perfil.apodo || perfil.nombre || "Tu perfil";
  const esPremium = perfil.plan === "premium";

  const guardarAviso = async (v: boolean) => {
    setAviso(v);
    await api.setPerfil({ aviso_activo: v });
    refrescarPerfil();
  };

  // —— WS30 · C2.2 · la foto: la cara con la que te encuentran ——
  // El <input type="file"> vive escondido; el botón es quien lo abre.
  const elegirFoto = async (file: File | undefined) => {
    if (!file) return;
    setAvisoFoto(null);
    if (!FORMATOS_FOTO.includes(file.type)) {
      setAvisoFoto("La foto tiene que ser JPG, PNG o WebP.");
      return;
    }
    if (file.size > FOTO_MAX_MB * 1024 * 1024) {
      setAvisoFoto(`La foto no puede pesar más de ${FOTO_MAX_MB} MB.`);
      return;
    }
    setSubiendoFoto(true);
    try {
      await api.subirFotoPerfil(file);
      await refrescarPerfil();
    } catch (e) {
      setAvisoFoto((e as Error).message || "No pudimos guardar tu foto. Inténtalo en un rato.");
    } finally {
      setSubiendoFoto(false);
      // Que elegir el MISMO archivo otra vez vuelva a disparar el cambio.
      if (fotoRef.current) fotoRef.current.value = "";
    }
  };

  const quitarFoto = async () => {
    setAvisoFoto(null);
    setSubiendoFoto(true);
    try {
      await api.quitarFotoPerfil();
      await refrescarPerfil();
    } catch (e) {
      setAvisoFoto((e as Error).message || "No pudimos quitar tu foto. Inténtalo en un rato.");
    } finally {
      setSubiendoFoto(false);
    }
  };

  // —— WS30 · C2.2 · perfil público ——
  // `perfil_publico` viaja en el mismo PUT /api/perfil (contrato C0 §4.3). El
  // tipo del cliente todavía no lo declara y `lib/api.ts` no se toca en esta
  // card: por eso el paso está acotado a esta línea.
  const guardarPublico = async (v: boolean) => {
    setPublico(v);
    setGuardandoPublico(true);
    try {
      await (api.setPerfil as (b: Record<string, unknown>) => Promise<unknown>)({
        perfil_publico: v,
      });
      await refrescarPerfil();
    } catch {
      setPublico(!v); // no se guardó: el switch vuelve a donde estaba
    } finally {
      setGuardandoPublico(false);
    }
  };

  const abrirEditor = () => {
    // Siempre se abre con lo que hay guardado: cancelar no deja rastros.
    setNombre(perfil.nombre ?? "");
    setApellido(perfil.apellido ?? "");
    setApodo(perfil.apodo ?? perfil.nombre ?? "");
    setEditando(true);
  };

  const guardarIdentidad = async () => {
    setGuardando(true);
    try {
      await api.setPerfil({
        apodo: apodo.trim(),
        nombre: nombre.trim(),
        apellido: apellido.trim(),
      });
      await refrescarPerfil();
      setEditando(false);
    } finally {
      setGuardando(false);
    }
  };

  const abrirPortal = async () => {
    setAbriendoPortal(true);
    setAvisoPlan(null);
    try {
      const { url } = await api.pagosPortal();
      window.location.href = url;
    } catch (e) {
      // El `detail` de la API es de sistema; el aviso al usuario lo ponemos acá.
      const status = (e as Error & { status?: number }).status;
      setAvisoPlan(
        status === 409
          ? "Todavía no hay una suscripción que gestionar."
          : "No pudimos abrir la gestión de tu suscripción. Inténtalo en un rato.",
      );
      setAbriendoPortal(false);
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
      {/* —— 1 · Quién eres aquí: tu cara y tu nombre —— */}
      <div className="perfil-cabecera">
        <div className="perfil-quien">
          <Avatar apodo={comoTeLlaman} fotoUrl={perfil.foto_url} size={64} />
          <div className="perfil-identidad">
            <h1 className="perfil-apodo">{comoTeLlaman}</h1>
            <p className="perfil-email">{perfil.email}</p>
          </div>
        </div>
        {!editando && (
          <button className="perfil-editar" onClick={abrirEditor}>
            Editar
          </button>
        )}
      </div>

      {/* La foto es la cara con la que te encuentran y con la que firman tus
          fichas: se cambia en un gesto y se quita en otro. */}
      <div className="perfil-foto-acciones">
        <input
          ref={fotoRef}
          className="perfil-foto-input"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={(e) => elegirFoto(e.target.files?.[0])}
        />
        <button
          className="link"
          disabled={subiendoFoto}
          onClick={() => fotoRef.current?.click()}
        >
          {subiendoFoto ? "Un momento…" : perfil.foto_url ? "Cambiar foto" : "Poner una foto"}
        </button>
        {perfil.foto_url && (
          <button className="link" disabled={subiendoFoto} onClick={quitarFoto}>
            Quitar
          </button>
        )}
      </div>
      {avisoFoto && <p className="perfil-foto-aviso">{avisoFoto}</p>}

      {editando && (
        <div className="perfil-editor">
          <div className="perfil-campo">
            <label className="perfil-campo-label" htmlFor="perfil-apodo">
              Apodo · cómo te llamamos
            </label>
            <input
              id="perfil-apodo"
              className="time-input"
              type="text"
              maxLength={40}
              placeholder="Cómo quieres que te llamemos"
              value={apodo}
              onChange={(e) => setApodo(e.target.value)}
            />
          </div>
          <div className="perfil-campo">
            <label className="perfil-campo-label" htmlFor="perfil-nombre">
              Nombre
            </label>
            <input
              id="perfil-nombre"
              className="time-input"
              type="text"
              maxLength={80}
              placeholder="Tu nombre"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
          </div>
          <div className="perfil-campo">
            <label className="perfil-campo-label" htmlFor="perfil-apellido">
              Apellido (opcional)
            </label>
            <input
              id="perfil-apellido"
              className="time-input"
              type="text"
              maxLength={80}
              placeholder="Tu apellido"
              value={apellido}
              onChange={(e) => setApellido(e.target.value)}
            />
          </div>
          <div className="perfil-campo">
            <span className="perfil-campo-label">Email</span>
            {/* El email es la llave de la cuenta: se muestra, no se toca. */}
            <p className="perfil-campo-fijo">{perfil.email}</p>
          </div>
          <p className="perfil-editor-nota">
            Te encuentran por tu email, apodo, nombre y apellido.
          </p>
          <div className="perfil-editor-acciones">
            <Button full disabled={guardando || !apodo.trim()} onClick={guardarIdentidad}>
              {guardando ? "Guardando…" : "Guardar"}
            </Button>
            <Button
              variant="tertiary"
              full
              disabled={guardando}
              onClick={() => setEditando(false)}
            >
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {/* —— Perfil público: quién puede llegar a tus Pausas compartidas.
              Va junto a quién eres, porque es parte de eso. —— */}
      <div className="perfil-publico">
        <label className="toggle-row">
          <span className="visibilidad-label">Perfil público</span>
          <span className="switch">
            <input
              type="checkbox"
              checked={publico}
              disabled={guardandoPublico}
              onChange={(e) => guardarPublico(e.target.checked)}
            />
            <span className="slider" />
          </span>
        </label>
        <p className="perfil-publico-nota">
          <b>Privado:</b> te encuentran, pero ven tus Pausas solo quienes aceptaste.
          <br />
          <b>Público:</b> cualquier persona de Dwellia ve tus Pausas compartidas.
        </p>
      </div>

      {/* —— 2 · Tu Pausa diaria —— */}
      <div className="profile-section">
        <h3>Tu Pausa diaria</h3>
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

        {aviso && push === "activas" && (
          <p className="meta" style={{ marginTop: 10 }}>
            ✓ Notificaciones activas en este dispositivo.
          </p>
        )}
        {aviso && push === "pedir" && (
          <>
            <p className="meta" style={{ marginTop: 10 }}>
              Para que el aviso llegue a este dispositivo, activa las notificaciones.
            </p>
            <div className="actions-stack" style={{ marginTop: 10 }}>
              <Button variant="secondary" full disabled={activando} onClick={activarNotificaciones}>
                {activando ? "Activando…" : "Activar notificaciones"}
              </Button>
            </div>
          </>
        )}
        {aviso && push === "instalar" && (
          <p className="meta" style={{ marginTop: 10 }}>
            En iPhone, el aviso llega solo con Dwellia instalada: instálala (más abajo
            te mostramos cómo), ábrela desde tu pantalla de inicio y vuelve aquí.
          </p>
        )}
        {aviso && push === "bloqueadas" && (
          <p className="meta" style={{ marginTop: 10 }}>
            Las notificaciones están bloqueadas para Dwellia en este dispositivo.
            Actívalas en los ajustes del navegador o del sistema.
          </p>
        )}
        {aviso && push === "nosoporta" && (
          <p className="meta" style={{ marginTop: 10 }}>
            Este navegador no admite notificaciones; abre Dwellia en tu teléfono para
            recibir el aviso.
          </p>
        )}
      </div>

      {/* —— 3 · Instalar Dwellia (solo si todavía no lo está) —— */}
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

      {/* —— 4 · Tu plan. Free: se cuenta que ya tiene todo el método y se invita,
              sin presión. Premium: se agradece y se deja gestionar el cobro. —— */}
      <div className="profile-section">
        <h3>Tu plan</h3>
        <div className="profile-row">
          <span>{esPremium ? "Dwellia premium" : "Plan gratuito"}</span>
          {/* La píldora se mantiene corta a propósito: la fecha va debajo, o en
              móvil parte el renglón en dos. */}
          <span className={`plan-pill ${esPremium ? "es-premium" : ""}`}>
            {esPremium ? "activo" : "Gratis"}
          </span>
        </div>
        {esPremium ? (
          <>
            <p className="meta" style={{ marginTop: 8 }}>
              {perfil.plan_hasta
                ? `Hasta el ${fechaLarga(perfil.plan_hasta)}. Gracias por sostener este lugar sin anuncios.`
                : "Gracias por sostener este lugar sin anuncios."}
            </p>
            {avisoPlan && <p className="premium-aviso" style={{ marginTop: 10 }}>{avisoPlan}</p>}
            <div className="actions-stack" style={{ marginTop: 12 }}>
              <Button variant="secondary" full disabled={abriendoPortal} onClick={abrirPortal}>
                {abriendoPortal ? "Abriendo…" : "Quiero dejar la comunidad"}
              </Button>
            </div>
          </>
        ) : (
          <>
            <p className="meta" style={{ marginTop: 8 }}>
              Tienes el método Dwellia completo, sin anuncios.
            </p>
            <div className="actions-stack" style={{ marginTop: 12 }}>
              <Button variant="primary" full onClick={() => navigate("/premium")}>
                Quiero ser parte
              </Button>
            </div>
          </>
        )}
      </div>

      {/* —— 5 · El método —— */}
      <div className="profile-section">
        <h3>El método Dwellia</h3>
        <p className="meta">
          La Pausa de dos tiempos, la calma como camino y los seis pilares: el
          porqué de cada carta.
        </p>
        <button className="link" style={{ marginTop: 8 }} onClick={() => navigate("/metodo")}>
          Leer el método
        </button>
      </div>

      {/* —— 6 · Privacidad —— */}
      <div className="profile-section">
        <h3>Privacidad</h3>
        <p className="meta">Lo que escribes y tus fotos quedan solo para ti.</p>
        <button className="link" style={{ marginTop: 8 }} onClick={() => navigate("/terminos")}>
          Términos y política de privacidad
        </button>
      </div>

      {verComoInstalar && <InstallIOSModal onClose={() => setVerComoInstalar(false)} />}

      {/* —— 8 · Demo (solo dev) y cerrar sesión —— */}
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

      {/* —— Adminland (WS28 · Tomás): abajo de todo, solo si esta cuenta es admin.
              No es una pestaña: la puerta está acá, y quien no es admin ni la ve. —— */}
      {perfil.es_admin && (
        <div className="actions-stack" style={{ marginTop: 18 }}>
          <Button variant="secondary" full onClick={() => navigate("/admin")}>
            Adminland
          </Button>
        </div>
      )}
    </div>
  );
}

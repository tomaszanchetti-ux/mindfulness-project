// WS28 · B2.2a · Avisos — lo que hay detrás de la campana.
//
// Una lista, más nuevo primero, y nada más. Los avisos de Dwellia no piden nada:
// cuentan que una carta cambió de estado. Por eso tocar uno lo marca leído y, si
// habla de una carta, lleva a Crear, que es donde se ve el recorrido completo.
//
// El marcado es OPTIMISTA: el punto se apaga en el acto y la llamada viaja
// después. Si falla, el aviso ya cumplió su función (se leyó) y volver a entrar
// lo vuelve a mostrar sin leer: nadie pierde nada.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { api } from "../lib/api";
import { fechaCorta } from "../lib/format";
import type { Aviso } from "../lib/types";
import "./crear.css";

export function Avisos() {
  const navigate = useNavigate();
  const [avisos, setAvisos] = useState<Aviso[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [marcando, setMarcando] = useState(false);

  useEffect(() => {
    let vivo = true;
    api
      .avisos()
      .then((b) => {
        if (!vivo) return;
        // El backend ya los manda ordenados; lo reafirmamos acá para que el
        // orden de la pantalla no dependa de eso.
        setAvisos(
          [...b.avisos].sort(
            (a, z) => new Date(z.created_at).getTime() - new Date(a.created_at).getTime(),
          ),
        );
      })
      .catch((e) => {
        if (!vivo) return;
        setAvisos([]);
        setError((e as Error).message);
      });
    return () => {
      vivo = false;
    };
  }, []);

  const abrir = (aviso: Aviso) => {
    if (!aviso.leido) {
      setAvisos((prev) =>
        (prev || []).map((a) => (a.id === aviso.id ? { ...a, leido: true } : a)),
      );
      api.avisoLeido(aviso.id).catch(() => {});
    }
    if (aviso.tipo === "carta_estado") navigate("/crear");
  };

  const marcarTodos = async () => {
    setMarcando(true);
    try {
      await api.avisosLeidos();
      setAvisos((prev) => (prev || []).map((a) => ({ ...a, leido: true })));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setMarcando(false);
    }
  };

  if (avisos === null) return <div className="center-note">…</div>;

  const noLeidos = avisos.filter((a) => !a.leido).length;

  return (
    <div className="avisos">
      <div className="screen-head">
        <h1 className="screen-title">Avisos</h1>
        <p className="screen-sub">Lo que pasó con tus cartas</p>
      </div>

      {error && <p className="crear-aviso">{error}</p>}

      {avisos.length === 0 ? (
        <div className="empty">
          <p className="empty-title">Todavía no tienes avisos.</p>
          <p className="empty-body">
            Cuando una de tus cartas avance en su recorrido, te lo contamos aquí.
          </p>
        </div>
      ) : (
        <>
          {noLeidos > 0 && (
            <div className="avisos-marcar">
              <button className="link" disabled={marcando} onClick={marcarTodos}>
                {marcando ? "Marcando…" : "Marcar todos como leídos"}
              </button>
            </div>
          )}

          <div className="avisos-lista">
            {avisos.map((a) => (
              <button
                key={a.id}
                type="button"
                className={`aviso ${a.leido ? "" : "es-no-leido"}`}
                onClick={() => abrir(a)}
              >
                {/* spans y no <p>: un botón solo admite contenido de frase */}
                <span className="aviso-texto">{a.texto}</span>
                <span className="aviso-fecha">{fechaCorta(a.created_at)}</span>
              </button>
            ))}
          </div>
        </>
      )}

      <div className="actions-stack avisos-volver">
        <Button
          variant="tertiary"
          onClick={() => (history.length > 1 ? navigate(-1) : navigate("/hoy"))}
        >
          Volver
        </Button>
      </div>
    </div>
  );
}

// Push web (WS21): el canal del aviso diario. Sin FCM — Web Push estándar + VAPID.
//
// Realidad por plataforma:
//   · Android / desktop: funciona en el navegador (mejor aún instalada).
//   · iPhone: SOLO funciona con Dwellia instalada en la pantalla de inicio
//     (iOS 16.4+). En Safari "suelto" la API ni existe → soportaPush() = false.

import { api } from "./api";

// Llave VAPID pública (par de la privada del backend). Es pública por diseño.
const VAPID_PUBLIC_KEY =
  "BNZZl9_Sx-ljUK9HvugWNjsUAe6bNx5ie7tLiM6_f8OFkhnn5mv81wu-9lNytf-aLaJBdk-4oRX0RLJPNV0GgyU";

export function soportaPush(): boolean {
  return (
    "serviceWorker" in navigator && "PushManager" in window && "Notification" in window
  );
}

export function permisoPush(): NotificationPermission | "unsupported" {
  return soportaPush() ? Notification.permission : "unsupported";
}

function vapidBytes(): Uint8Array<ArrayBuffer> {
  const pad = "=".repeat((4 - (VAPID_PUBLIC_KEY.length % 4)) % 4);
  const raw = atob((VAPID_PUBLIC_KEY + pad).replace(/-/g, "+").replace(/_/g, "/"));
  const bytes = new Uint8Array(new ArrayBuffer(raw.length));
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  return bytes;
}

export async function suscripcionActual(): Promise<PushSubscription | null> {
  if (!soportaPush()) return null;
  const reg = await navigator.serviceWorker.ready;
  return reg.pushManager.getSubscription();
}

/** Pide permiso (si hace falta), suscribe este dispositivo y lo registra en la API. */
export async function activarPush(): Promise<boolean> {
  if (!soportaPush()) return false;
  const permiso = await Notification.requestPermission();
  if (permiso !== "granted") return false;
  const reg = await navigator.serviceWorker.ready;
  const sub =
    (await reg.pushManager.getSubscription()) ||
    (await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: vapidBytes(),
    }));
  const json = sub.toJSON();
  if (!json.endpoint || !json.keys?.p256dh || !json.keys?.auth) return false;
  await api.pushSuscribir({
    endpoint: json.endpoint,
    p256dh: json.keys.p256dh,
    auth: json.keys.auth,
  });
  return true;
}

/** Da de baja este dispositivo (navegador + API). */
export async function desactivarPush(): Promise<void> {
  const sub = await suscripcionActual();
  if (!sub) return;
  const endpoint = sub.endpoint;
  await sub.unsubscribe().catch(() => {});
  await api.pushBaja(endpoint).catch(() => {});
}

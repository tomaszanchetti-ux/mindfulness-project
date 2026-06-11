// Service worker mínimo: hace que Dwellia sea instalable como PWA y funcione
// offline. Estrategia network-first: SIEMPRE intenta la red (así un deploy nuevo
// se ve al instante) y solo cae al cache si no hay conexión.
const CACHE = "dwellia-shell-v1";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  e.respondWith(
    fetch(req)
      .then((res) => {
        if (res && res.status === 200 && res.type === "basic") {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() => caches.match(req)),
  );
});

// ── Push (WS21) ──────────────────────────────────────────────────────────────
// El backend manda {titulo, cuerpo, url}; acá se muestra la notificación.
self.addEventListener("push", (e) => {
  let data = {};
  try {
    data = e.data ? e.data.json() : {};
  } catch {
    /* payload no-JSON: usamos defaults */
  }
  const titulo = data.titulo || "Dwellia";
  e.waitUntil(
    self.registration.showNotification(titulo, {
      body: data.cuerpo || "Tu carta de hoy te espera.",
      icon: "/icon-192.png",
      badge: "/icon-192.png",
      data: { url: data.url || "/hoy" },
    }),
  );
});

// Tocar la notificación abre (o enfoca) la app en la carta del día.
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || "/hoy";
  e.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((wins) => {
      for (const w of wins) {
        if ("focus" in w) {
          w.navigate(url);
          return w.focus();
        }
      }
      return self.clients.openWindow(url);
    }),
  );
});

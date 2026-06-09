// Instalación de la PWA. El navegador a veces NO ofrece instalar (en Android el
// prompt automático queda suprimido tras desinstalar; en iOS nunca hay prompt).
// Capturamos el evento `beforeinstallprompt` para poder ofrecer un botón propio.

type BIPEvent = Event & {
  prompt: () => void;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

let deferred: BIPEvent | null = null;

// Llamar lo antes posible (el evento puede dispararse apenas carga la página).
export function initInstallPrompt(): void {
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferred = e as BIPEvent;
    window.dispatchEvent(new Event("pwa:can-install"));
  });
  window.addEventListener("appinstalled", () => {
    deferred = null;
    window.dispatchEvent(new Event("pwa:installed"));
  });
}

export function canInstall(): boolean {
  return !!deferred;
}

export async function promptInstall(): Promise<boolean> {
  if (!deferred) return false;
  deferred.prompt();
  const { outcome } = await deferred.userChoice;
  if (outcome === "accepted") deferred = null;
  return outcome === "accepted";
}

export function isIOS(): boolean {
  return /iphone|ipad|ipod/i.test(navigator.userAgent);
}

// ¿Ya está corriendo como app instalada? (entonces no ofrecemos instalar)
export function isStandalone(): boolean {
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    // iOS Safari
    (navigator as unknown as { standalone?: boolean }).standalone === true
  );
}

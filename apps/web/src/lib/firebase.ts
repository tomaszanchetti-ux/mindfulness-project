// Firebase Auth (solo producción; en dev la API resuelve identidad por X-Debug-*).
//
// authDomain apunta al dominio de Hosting (no a *.firebaseapp.com): así el handler
// /__/auth/ queda same-origin y signInWithRedirect funciona con el storage
// partitioning de Safari/Chrome.

import { initializeApp } from "firebase/app";
import {
  GoogleAuthProvider,
  getAuth,
  getRedirectResult,
  isSignInWithEmailLink,
  sendSignInLinkToEmail,
  signInWithEmailLink,
  signInWithPopup,
  signInWithRedirect,
  signOut,
} from "firebase/auth";
import { isStandalone } from "../pwa";

const app = initializeApp({
  projectId: "dwellia-app",
  appId: "1:173534681346:web:da32f9719e20930d714a1b",
  storageBucket: "dwellia-app.firebasestorage.app",
  apiKey: "AIzaSyDrhoXnH4h5sNU7dk0JKBWzlcPVp2INNIE",
  authDomain: "dwellia-app.web.app",
  messagingSenderId: "173534681346",
});

export const auth = getAuth(app);

// Email del magic link: se guarda al enviarlo para completar el sign-in cuando
// la persona vuelve desde su correo (mismo dispositivo).
const EMAIL_KEY = "dwellia-email-enlace";

export async function loginConGoogle(): Promise<void> {
  const provider = new GoogleAuthProvider();
  // PWA instalada (iOS sobre todo): el popup no es confiable → redirect directo.
  if (isStandalone()) {
    await signInWithRedirect(auth, provider);
    return;
  }
  try {
    await signInWithPopup(auth, provider);
  } catch (e) {
    const code = (e as { code?: string }).code;
    if (
      code === "auth/popup-blocked" ||
      code === "auth/operation-not-supported-in-this-environment" ||
      code === "auth/cancelled-popup-request"
    ) {
      await signInWithRedirect(auth, provider);
      return;
    }
    throw e;
  }
}

// Completa el retorno de signInWithRedirect (no-op si no venimos de uno).
export async function completarRedirect(): Promise<void> {
  try {
    await getRedirectResult(auth);
  } catch {
    // Sin resultado pendiente o error transitorio: el Login queda disponible.
  }
}

export async function enviarMagicLink(email: string): Promise<void> {
  await sendSignInLinkToEmail(auth, email, {
    url: `${window.location.origin}/login/email`,
    handleCodeInApp: true,
  });
  try {
    localStorage.setItem(EMAIL_KEY, email);
  } catch {
    /* sin localStorage: pedirá el email al volver */
  }
}

export function esMagicLink(): boolean {
  return isSignInWithEmailLink(auth, window.location.href);
}

export function emailGuardado(): string | null {
  try {
    return localStorage.getItem(EMAIL_KEY);
  } catch {
    return null;
  }
}

export async function completarMagicLink(email: string): Promise<void> {
  await signInWithEmailLink(auth, email, window.location.href);
  try {
    localStorage.removeItem(EMAIL_KEY);
  } catch {
    /* ignorar */
  }
}

export async function cerrarSesion(): Promise<void> {
  await signOut(auth);
}

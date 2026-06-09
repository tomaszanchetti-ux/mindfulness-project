import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El prototipo corre en :8081 (puerto ya contemplado en el CORS de la API).
// Igual usamos proxy: el navegador habla con Vite (mismo origen) y Vite reenvía
// /api y /c-públicos a la API en :8000 → cero fricción de CORS en local.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8081,
    host: "127.0.0.1",
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
    },
  },
});

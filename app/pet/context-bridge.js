// app/pet/context-bridge.js — Disparo automático del contexto de la mascota (Fase 9.2/9.4).
// Se incluye en las páginas de módulo (gym, dieta, finanzas, apuntes, levelup). Al cargar
// dentro de Tauri, emite `elfie:context` según la página → la mascota toma la pose del
// módulo activo. NO-OP en web (sin __TAURI__). El dashboard (index.html) repone "neutral".
(function () {
  "use strict";
  const T = window.__TAURI__;
  if (!T) return; // navegador web: la mascota es de escritorio

  const p = (location.pathname || "").toLowerCase();
  let ctx = null;
  if (p.includes("gym")) ctx = "gym";
  else if (p.includes("dieta")) ctx = "diet";
  else if (p.includes("finanzas")) ctx = "finance";
  else if (p.includes("apuntes")) ctx = "study";
  else if (p.includes("levelup")) ctx = "levelup";

  if (ctx) {
    try { T.event.emit("elfie:context", ctx); } catch (_) {}
  }
})();

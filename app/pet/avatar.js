// app/pet/avatar.js — Máquina de estados de la mascota flotante de Elfie (Fase 9.0).
// Vive en la ventana `pet` (pet.html). Web-safe: si no hay Tauri, funciona igual
// como demo/preview (sin comandos de ventana). El "cerebro" corre en la ventana
// principal y conduce a la mascota emitiendo eventos app-wide (elfie:state, etc.).
(function () {
  "use strict";

  const T = window.__TAURI__ || null;
  const invoke = T ? T.core.invoke : async () => {};
  const listen = T ? T.event.listen : null;
  const emit = T ? T.event.emit : async () => {};

  const $ = (id) => document.getElementById(id);

  // Estados con su archivo de avatar (MVP: 5 en PNG/SVG; se amplía en 9.2).
  const ASSETS = {
    neutral:   "pet/assets/neutral.svg",
    listening: "pet/assets/listening.svg",
    thinking:  "pet/assets/thinking.svg",
    speaking:  "pet/assets/speaking.svg",
    executing: "pet/assets/thinking.svg",   // alias hasta tener arte propio
    confirming:"pet/assets/listening.svg",  // alias
    error:     "pet/assets/error.svg",
    alert:     "pet/assets/error.svg",       // alias
  };
  const STATUS = {
    neutral: "", listening: "Escuchando…", thinking: "Pensando…",
    speaking: "", executing: "Ejecutando…", confirming: "¿Confirmas?",
    error: "No entendí", alert: "Atención",
  };

  let state = "neutral";
  let idleTimer = null, blinkTimer = null, bubbleTimer = null;

  function preload() {
    Object.values(ASSETS).forEach((src) => { const i = new Image(); i.src = src; });
  }

  // --- Cambio de estado: alterna el archivo del avatar ---
  function setState(next, opts) {
    opts = opts || {};
    if (!ASSETS[next]) next = "neutral";
    state = next;
    const img = $("pet-avatar");
    if (img) img.src = ASSETS[next];
    document.body.dataset.state = next;
    const st = $("pet-status");
    if (st) st.textContent = opts.status != null ? opts.status : (STATUS[next] || "");
    if (opts.text) bubble(opts.text, opts.kind || "info");
    // El parpadeo solo en reposo (en otros estados el arte ya expresa).
    if (next === "neutral") scheduleBlink(); else stopBlink();
  }

  // --- Parpadeo / idle (ilusión de vida sin GPU): un micro scaleY en el avatar ---
  function scheduleBlink() {
    stopBlink();
    const next = 3500 + Math.floor(2500 * ((Date.now() % 997) / 997)); // 3.5–6 s, sin Math.random global
    blinkTimer = setTimeout(() => {
      const img = $("pet-avatar");
      if (img && state === "neutral") {
        img.classList.add("blink");
        setTimeout(() => img.classList.remove("blink"), 130);
      }
      scheduleBlink();
    }, next);
  }
  function stopBlink() { if (blinkTimer) { clearTimeout(blinkTimer); blinkTimer = null; } }

  // --- Burbuja de diálogo ---
  function bubble(text, kind, sticky) {
    const b = $("pet-bubble");
    if (!b) return;
    b.textContent = text;
    b.dataset.kind = kind || "info";
    b.hidden = false;
    pushHistory(text, kind);
    if (bubbleTimer) clearTimeout(bubbleTimer);
    if (!sticky) bubbleTimer = setTimeout(() => { b.hidden = true; }, 6000);
  }
  function clearBubble() { const b = $("pet-bubble"); if (b) b.hidden = true; }

  function pushHistory(text, kind) {
    const h = $("pet-history");
    if (!h) return;
    const row = document.createElement("div");
    row.className = "ph-row" + (kind ? " " + kind : "");
    row.textContent = text;
    h.appendChild(row);
    while (h.childElementCount > 30) h.removeChild(h.firstChild);
    h.scrollTop = h.scrollHeight;
  }

  // --- Tarjeta de confirmación (la cara visual de "la IA propone, el humano dispone") ---
  let pendingConfirm = null;
  function confirmCard(text, opts) {
    opts = opts || {};
    setState("confirming");
    bubble(text, opts.irreversible ? "warn" : "info", true);
    const card = $("pet-confirm");
    if (!card) return;
    $("pet-confirm-text").textContent = text;
    card.dataset.irreversible = opts.irreversible ? "1" : "0";
    card.hidden = false;
    pendingConfirm = opts;
  }
  function resolveConfirm(ok) {
    const card = $("pet-confirm");
    if (card) card.hidden = true;
    const p = pendingConfirm; pendingConfirm = null;
    clearBubble();
    setState("neutral");
    if (!p) return;
    try { ok ? p.onYes && p.onYes() : p.onNo && p.onNo(); } catch (_) {}
    // Avisa a la ventana principal el resultado (por si encadena algo).
    emit("pet:confirm-result", { ok });
  }
  // Confirmación por voz: la ventana principal reenvía el texto crudo aquí.
  const YES = /\b(s[ií]|confirma|h[aá]zlo|dale|ok|correcto)\b/i;
  const NO = /\b(no|cancela|ignora|olv[ií]dalo|det[eé]n)\b/i;
  function voiceConfirm(textRaw) {
    if (!pendingConfirm) return false;
    if (YES.test(textRaw)) { resolveConfirm(true); return true; }
    if (NO.test(textRaw)) { resolveConfirm(false); return true; }
    return false;
  }

  // --- Tamaños: mini (solo avatar) · normal (avatar+texto) · panel (+historial+acciones) ---
  const SIZES = ["mini", "normal", "panel"];
  function applySize(size) {
    document.body.className = size;
    const h = $("pet-history");
    if (h) h.hidden = size !== "panel"; // el historial solo existe en panel
  }
  function setSize(size) {
    if (!SIZES.includes(size)) size = "normal";
    applySize(size);
    try { localStorage.setItem("prts_pet_size", size); } catch (_) {}
    invoke("pet_set_size", { size }).catch(() => {});
  }
  function cycleSize() {
    const i = SIZES.indexOf(document.body.className || "normal");
    setSize(SIZES[(i + 1) % SIZES.length]);
  }

  // --- Miniacciones: la mascota pide a la ventana principal que actúe ---
  function action(act) { emit("pet:action", { act }); }

  // --- Cableado de eventos venidos del cerebro (ventana principal) ---
  if (listen) {
    listen("elfie:state", (e) => { const p = e.payload || {}; setState(p.state || "neutral", p); });
    listen("elfie:say", (e) => { const p = e.payload || {}; setState("speaking"); if (p.text) bubble(p.text, "say"); });
    listen("elfie:listening", (e) => {
      if (e.payload) setState("listening");
      else if (state !== "speaking") setState("neutral");
    });
    listen("elfie:speaking", (e) => { if (e.payload) setState("speaking"); else if (state === "speaking") setState("neutral"); });
    listen("elfie:bubble", (e) => { const p = e.payload || {}; bubble(p.text || "", p.kind || "info", p.sticky); });
    listen("elfie:thinking", () => setState("thinking"));
    listen("elfie:confirm", (e) => { const p = e.payload || {}; confirmCard(p.text || "¿Confirmas?", p); });
    listen("elfie:voice-confirm", (e) => voiceConfirm((e.payload && e.payload.text) || ""));
    listen("pet:size", (e) => { const s = e.payload; if (SIZES.includes(s)) applySize(s); });
  }

  // --- Init ---
  function init() {
    preload();
    let size = "normal";
    try { size = localStorage.getItem("prts_pet_size") || "normal"; } catch (_) {}
    applySize(SIZES.includes(size) ? size : "normal");

    document.querySelectorAll("[data-act]").forEach((b) => {
      b.addEventListener("click", () => {
        const a = b.dataset.act;
        if (a === "size") cycleSize();
        else action(a);
      });
    });
    const yes = $("pet-yes"), no = $("pet-no");
    if (yes) yes.addEventListener("click", () => resolveConfirm(true));
    if (no) no.addEventListener("click", () => resolveConfirm(false));

    setState("neutral");

    // Demo en web/preview (sin Tauri): cicla estados para ver el sistema vivo.
    if (!T || /[?&]demo=1/.test(location.search)) {
      const seq = ["neutral", "listening", "thinking", "speaking", "confirming", "error"];
      let i = 0;
      idleTimer = setInterval(() => {
        const s = seq[i++ % seq.length];
        if (s === "speaking") setState(s, { text: "Registré tu peso de hoy: 72.4 kg." });
        else if (s === "confirming") setState(s, { text: "¿Agrego esto a Semana?" });
        else setState(s);
      }, 2200);
    }
  }

  window.Avatar = { setState, bubble, clearBubble, confirmCard, voiceConfirm, setSize, cycleSize, action, get state() { return state; } };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

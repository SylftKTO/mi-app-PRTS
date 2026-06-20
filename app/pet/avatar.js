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

  // Estado → nombre base del archivo. La URL la arma assetUrl() con la extensión
  // activa (svg hoy; webp cuando haya arte animado — Fase 9.2). Alternar el archivo
  // por estado es la base del sistema visual.
  const ASSETS = {
    neutral: "neutral", listening: "listening", thinking: "thinking",
    speaking: "speaking", "speaking-closed": "speaking-closed",
    executing: "thinking", confirming: "listening", error: "error", alert: "error",
    // Estados contextuales por módulo (9.2): pose de reposo según lo que se hace.
    study: "study", gym: "gym", finance: "finance", diet: "diet", levelup: "levelup", music: "music",
  };
  const CONTEXTS = ["study", "gym", "finance", "diet", "levelup", "music"];
  const REST = new Set(["neutral"].concat(CONTEXTS)); // estados de "reposo" (parpadean)
  const STATUS = {
    neutral: "", listening: "Escuchando…", thinking: "Pensando…",
    speaking: "", executing: "Ejecutando…", confirming: "¿Confirmas?",
    error: "No entendí", alert: "Atención",
    study: "Estudio", gym: "Gym", finance: "Finanzas", diet: "Dieta", levelup: "LevelUp", music: "Música",
  };
  // Tono visual por estado: color de la burbuja según lo que comunica el avatar.
  const KIND = { error: "error", alert: "warn", confirming: "info", speaking: "say", executing: "info" };

  const EXT_KEY = "prts_pet_ext";
  let EXT = "svg";
  try { EXT = localStorage.getItem(EXT_KEY) || "svg"; } catch (_) {}
  function assetUrl(base) { return "pet/assets/" + base + "." + EXT; }

  let state = "neutral";
  let restState = "neutral"; // pose por defecto al volver a reposo (neutral o contexto)
  let idleTimer = null, blinkTimer = null, bubbleTimer = null, talkTimer = null;

  function preload() {
    Object.values(ASSETS).forEach((b) => { const i = new Image(); i.src = assetUrl(b); });
  }

  // --- Cambio de estado: alterna el archivo del avatar ---
  function setState(next, opts) {
    opts = opts || {};
    if (next === "neutral") next = restState; // "neutral" muestra la pose de reposo activa
    if (!ASSETS[next]) next = "neutral";
    state = next;
    const img = $("pet-avatar");
    if (img) img.src = assetUrl(ASSETS[next]);
    document.body.dataset.state = next;
    const st = $("pet-status");
    if (st) st.textContent = opts.status != null ? opts.status : (STATUS[next] || "");
    if (opts.text) bubble(opts.text, opts.kind || KIND[next] || "info");
    // Boca animada solo al hablar; parpadeo solo en reposo.
    if (next === "speaking") startTalk(); else stopTalk();
    // En reposo: parpadeo + temporizador de auto-ocultar. En actividad: reaparece.
    if (REST.has(next)) { scheduleBlink(); scheduleHide(); }
    else { stopBlink(); clearHide(); revealIfNeeded(); }
  }

  // --- Pose por módulo: fija la "pose de reposo" (9.2) ---
  function setContext(ctx) {
    restState = ctx && ASSETS[ctx] && CONTEXTS.includes(ctx) ? ctx : "neutral";
    if (REST.has(state)) setState(restState); // si está en reposo, refléjalo ya
  }

  // --- Boca animada (lip-sync simple): alterna 2 sprites mientras habla ---
  function startTalk() {
    stopTalk();
    let open = true;
    talkTimer = setInterval(() => {
      const img = $("pet-avatar");
      if (!img || state !== "speaking") { stopTalk(); return; }
      open = !open;
      img.src = assetUrl(open ? "speaking" : "speaking-closed");
    }, 150);
  }
  function stopTalk() { if (talkTimer) { clearInterval(talkTimer); talkTimer = null; } }

  // --- Parpadeo / idle (ilusión de vida sin GPU): un micro scaleY en el avatar ---
  function scheduleBlink() {
    stopBlink();
    const next = 3500 + Math.floor(2500 * ((Date.now() % 997) / 997)); // 3.5–6 s, sin Math.random global
    blinkTimer = setTimeout(() => {
      const img = $("pet-avatar");
      if (img && REST.has(state)) {
        img.classList.add("blink");
        setTimeout(() => img.classList.remove("blink"), 130);
      }
      scheduleBlink();
    }, next);
  }
  function stopBlink() { if (blinkTimer) { clearTimeout(blinkTimer); blinkTimer = null; } }

  // Cambia la extensión de assets (svg → webp cuando haya arte animado).
  function setExt(ext) {
    EXT = ext === "webp" ? "webp" : "svg";
    try { localStorage.setItem(EXT_KEY, EXT); } catch (_) {}
    preload();
    setState(state);
  }

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
    SIZES.forEach((s) => document.body.classList.toggle(s, s === size)); // preserva "solo"
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
    const cur = SIZES.find((s) => document.body.classList.contains(s)) || "normal";
    setSize(SIZES[(SIZES.indexOf(cur) + 1) % SIZES.length]);
  }

  // --- Preferencias de la mascota (9.4): opacidad, ancla, auto-ocultar, solo-avatar ---
  const PCFG_KEY = "prts_pet_cfg";
  let petCfg = { opacity: 1, anchor: "tr", autoHide: false, solo: false };
  try { petCfg = Object.assign(petCfg, JSON.parse(localStorage.getItem(PCFG_KEY) || "{}")); } catch (_) {}
  function savePetCfg() { try { localStorage.setItem(PCFG_KEY, JSON.stringify(petCfg)); } catch (_) {} }

  // Opacidad (transparencia ajustable): se aplica al contenido (la ventana es transparent).
  const OPAC = [1, 0.85, 0.7, 0.55];
  function setOpacity(v) { petCfg.opacity = v; savePetCfg(); document.body.style.opacity = String(v); }
  function cycleOpacity() {
    const i = OPAC.indexOf(petCfg.opacity);
    setOpacity(OPAC[(i + 1) % OPAC.length]);
    bubble("Opacidad " + Math.round(petCfg.opacity * 100) + "%", "info");
  }

  // Ancla a esquina del monitor (lo posiciona Rust).
  const CORNERS = ["tr", "br", "bl", "tl"];
  const CORNER_LBL = { tr: "arriba dcha.", br: "abajo dcha.", bl: "abajo izq.", tl: "arriba izq." };
  function anchor(c) { petCfg.anchor = c; savePetCfg(); invoke("pet_anchor", { corner: c }).catch(() => {}); }
  function cycleAnchor() {
    const i = CORNERS.indexOf(petCfg.anchor);
    const c = CORNERS[(i + 1) % CORNERS.length];
    anchor(c);
    bubble("Anclada: " + CORNER_LBL[c], "info");
  }

  // Solo-avatar (click-through): deja pasar el ratón y oculta el chrome. Se SALE desde
  // Elfie Core (ventana principal) o el atajo/tray → emite pet:config {solo:false}.
  function setSolo(on) {
    petCfg.solo = on; savePetCfg();
    document.body.classList.toggle("solo", on);
    invoke("pet_click_through", { on }).catch(() => {});
  }

  // Auto-ocultar: tras inactividad en reposo, esconde la ventana; reaparece con actividad.
  let hideTimer = null;
  function scheduleHide() {
    clearHide();
    if (!petCfg.autoHide) return;
    hideTimer = setTimeout(() => { if (REST.has(state)) invoke("pet_hide").catch(() => {}); }, 20000);
  }
  function clearHide() { if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; } }
  function revealIfNeeded() { if (petCfg.autoHide) invoke("pet_show").catch(() => {}); }

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
    listen("elfie:context", (e) => setContext(e.payload));
    // La ventana principal (Elfie Core) controla solo-avatar y auto-ocultar.
    listen("pet:config", (e) => {
      const p = e.payload || {};
      if ("solo" in p) setSolo(!!p.solo);
      if ("autoHide" in p) {
        petCfg.autoHide = !!p.autoHide; savePetCfg();
        if (!petCfg.autoHide) invoke("pet_show").catch(() => {});
        else scheduleHide();
      }
    });
    listen("pet:size", (e) => { const s = e.payload; if (SIZES.includes(s)) applySize(s); });
  }

  // --- Init ---
  function init() {
    preload();
    let size = "normal";
    try { size = localStorage.getItem("prts_pet_size") || "normal"; } catch (_) {}
    applySize(SIZES.includes(size) ? size : "normal");

    // Acciones locales de la mascota (no van al cerebro); el resto → pet:action.
    const LOCAL_ACTS = { size: cycleSize, anchor: cycleAnchor, opacity: cycleOpacity, solo: () => setSolo(true) };
    document.querySelectorAll("[data-act]").forEach((b) => {
      b.addEventListener("click", () => {
        const a = b.dataset.act;
        if (LOCAL_ACTS[a]) LOCAL_ACTS[a]();
        else action(a);
      });
    });

    // Aplica preferencias guardadas (opacidad + ancla). Solo-avatar NO se auto-aplica
    // al iniciar (evita dejar la ventana atrapada sin clics).
    setOpacity(petCfg.opacity || 1);
    if (petCfg.anchor) anchor(petCfg.anchor);

    // Menú contextual (clic derecho sobre la mascota).
    const menu = $("pet-menu");
    function showMenu(x, y) {
      if (!menu) return;
      menu.hidden = false;
      const mw = menu.offsetWidth || 172, mh = menu.offsetHeight || 260;
      menu.style.left = Math.max(4, Math.min(x, window.innerWidth - mw - 4)) + "px";
      menu.style.top = Math.max(4, Math.min(y, window.innerHeight - mh - 4)) + "px";
    }
    function hideMenu() { if (menu) menu.hidden = true; }
    document.addEventListener("contextmenu", (e) => { e.preventDefault(); showMenu(e.clientX, e.clientY); });
    document.addEventListener("click", (e) => { if (menu && !menu.hidden && !menu.contains(e.target)) hideMenu(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") hideMenu(); });
    if (menu) menu.addEventListener("click", () => hideMenu()); // cierra tras elegir
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

  window.Avatar = {
    setState, setContext, setExt, bubble, clearBubble, confirmCard, voiceConfirm,
    setSize, cycleSize, setOpacity, cycleOpacity, anchor, cycleAnchor, setSolo,
    action, get state() { return state; }, get rest() { return restState; }, get cfg() { return petCfg; },
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

// app/elfie/desktop.js — Puente Elfie Desktop (Tauri) ↔ frontend PRTS compartido.
// Todo lo de aquí es NO-OP en el navegador web: solo corre dentro del WebView de Tauri,
// detectado por window.__TAURI__ (habilitado con withGlobalTauri en tauri.conf.json).
//
// Fase 1 (Core Desktop):
//  - Atajos globales: Ctrl+Space → captura, Alt+E → voz, Ctrl+Shift+R → rutina.
//  - Notificaciones nativas de Windows (comando Rust elfie_notify).
//  - Supabase Realtime: avisa con notificación nativa cuando llegan tareas/recordatorios/
//    capturas creadas desde otro cliente (web u otro dispositivo).
(function () {
  "use strict";
  const T = window.__TAURI__;
  if (!T) return; // navegador web: no hacer nada.

  const invoke = T.core.invoke;
  const listen = T.event.listen;

  // --- Configuración de Elfie (single source of truth en elfie/elfie-config.js) ---
  // El módulo Elfie (elfie.html) la edita; aquí el dashboard la APLICA.
  const ELFIE_CFG = window.ElfieConfig.data;
  const saveCfg = () => window.ElfieConfig.save();
  window.elfieCfg = ELFIE_CFG;

  // Notificación nativa de Windows. Degradación: si falla, no rompe nada.
  async function notify(title, body) {
    try {
      await invoke("elfie_notify", { title, body: body || "" });
    } catch (e) {
      console.warn("[elfie] notify falló:", e);
    }
  }
  window.elfieNotify = notify;

  // --- Atajos globales emitidos desde Rust ---
  function enfocarCaptura() {
    const panel = document.getElementById("panel-captura");
    if (panel) panel.scrollIntoView({ behavior: "smooth", block: "center" });
    const input = document.getElementById("cap-text");
    if (input) {
      input.focus();
      input.select?.();
    }
  }

  listen("elfie:open-capture", enfocarCaptura);

  // --- Voz local vía sidecar (Fase 3): faster-whisper STT + Kokoro TTS ---
  const VOICE_URL = "http://127.0.0.1:7331";
  let recording = false;

  async function voicePost(path, body) {
    const r = await fetch(VOICE_URL + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    return r.json();
  }

  // Push-to-talk: mantener Alt+E graba; soltar transcribe y enruta.
  listen("elfie:start-voice", async () => {
    if (ELFIE_CFG.features && ELFIE_CFG.features.voice === false) return; // voz desactivada
    if (recording) return;
    recording = true;
    if (window.PRTS_AI) window.PRTS_AI.attention = true; // enciende las auras de escucha de la runa
    try {
      await voicePost("/stt/start");
    } catch (e) {
      recording = false;
      console.warn("[elfie] sidecar de voz no responde:", e);
    }
  });

  listen("elfie:stop-voice", async () => {
    if (!recording) return;
    recording = false;
    if (window.PRTS_AI) window.PRTS_AI.attention = false;
    try {
      const res = await voicePost("/stt/stop");
      const text = (res && res.text) ? res.text.trim() : "";
      if (text && typeof window.ejecutarComando === "function") {
        console.log("[elfie] dijiste:", text);
        window.ejecutarComando(text, true); // spoken=true → sin modales, responde hablando
      }
    } catch (e) {
      console.warn("[elfie] STT falló:", e);
    }
  });

  // TTS por sidecar: Kokoro o XTTS (voz clonada). Si falla, usa el say original (speechSynthesis).
  if (window.PRTS_AI) {
    const originalSay = window.PRTS_AI.say ? window.PRTS_AI.say.bind(window.PRTS_AI) : null;
    window.PRTS_AI.say = async function (text) {
      if (!text || !ELFIE_CFG.ttsEnabled) return; // personalidad silenciosa → sin voz
      if (ELFIE_CFG.voiceEngine === "navegador") {
        if (originalSay) originalSay(text);
        return;
      }
      window.PRTS_AI.speaking = true; // ondas de voz (auras rosa de la runa)
      try {
        const body = { text, speed: ELFIE_CFG.voiceSpeed };
        // Voz clonada: solo si hay perfil XTTS con audio de referencia (si no, Kokoro).
        if (ELFIE_CFG.voiceEngine === "xtts" && ELFIE_CFG.xttsSpeakerWav) {
          body.engine = "xtts";
          body.speaker_wav = ELFIE_CFG.xttsSpeakerWav;
        }
        const res = await voicePost("/tts", body);
        if (!res || res.ok !== true) throw new Error(res && res.error);
      } catch (e) {
        console.warn("[elfie] TTS del sidecar falló, uso voz del navegador:", e);
        if (originalSay) originalSay(text);
      } finally {
        window.PRTS_AI.speaking = false;
      }
    };
  }

  listen("elfie:run-routine", () => {
    // Ctrl+Shift+R → abre el gestor de rutinas (Routine Engine Visual, Fase 5).
    if (window.elfieRoutines) window.elfieRoutines.openManager();
  });

  // --- Supabase Realtime: notificar inserciones desde otros clientes ---
  // Espera a que el cliente sb y la sesión existan (los crea el script inline de la página).
  function initRealtime() {
    const sb = window.sb;
    if (!sb || !sb.channel) {
      return setTimeout(initRealtime, 800);
    }
    sb.auth.getUser().then(({ data }) => {
      if (!data || !data.user) return; // sin sesión: no suscribir.

      sb.channel("elfie-desktop")
        .on(
          "postgres_changes",
          { event: "INSERT", schema: "public", table: "tasks" },
          (p) => {
            const t = p.new || {};
            notify("Nueva tarea", t.title || t.titulo || "Tarea creada");
          }
        )
        .on(
          "postgres_changes",
          { event: "INSERT", schema: "public", table: "reminders" },
          (p) => {
            const r = p.new || {};
            notify("Nuevo recordatorio", r.title || "Recordatorio creado");
          }
        )
        .on(
          "postgres_changes",
          { event: "INSERT", schema: "public", table: "inbox_entries" },
          (p) => {
            const e = p.new || {};
            notify("Captura nueva", (e.raw_text || e.content || "").slice(0, 80));
          }
        )
        .subscribe((status) => {
          if (status === "SUBSCRIBED") console.log("[elfie] Realtime activo");
        });
    });
  }
  initRealtime();

  // --- Control del sistema (Fase 2): helpers expuestos para voz/UI ---
  window.elfieSys = {
    openApp: (name) => invoke("open_app", { name }),
    killProcess: (name) => invoke("kill_process", { name }),
    openFolder: (path) => invoke("open_folder", { path }),
    powerAction: (action) => invoke("power_action", { action }),
    clipboardRead: () => invoke("clipboard_read"),
    clipboardWrite: (text) => invoke("clipboard_write", { text }),
    getMetrics: () => invoke("get_metrics"),
    setVolume: (level) => invoke("set_volume", { level }),
    getVolume: () => invoke("get_volume"),
    muteToggle: () => invoke("mute_toggle"),
    screenshot: (toClipboard = false) => invoke("screenshot", { toClipboard }),
    toggleFullscreen: () => invoke("toggle_fullscreen"),
    foregroundApp: () => invoke("foreground_app"),
  };

  // --- Pantalla completa: F11 alterna; Escape sale (solo cuando está activa) ---
  let fsOn = false;
  async function setFullscreen() {
    try { fsOn = await invoke("toggle_fullscreen"); } catch (e) { console.warn("[elfie] fullscreen falló:", e); }
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "F11") {
      e.preventDefault();
      setFullscreen();
    } else if (e.key === "Escape" && fsOn) {
      e.preventDefault();
      setFullscreen(); // sale de pantalla completa
    }
  });

  // --- Router híbrido: interpretación local con Ollama (fallback Anthropic) ---
  window.elfieInterpret = async function (text) {
    if (ELFIE_CFG.interpreter === "anthropic") return null; // usar Claude API (libera GPU local)
    try {
      const fecha = new Date().toLocaleDateString("en-CA", {
        timeZone: "America/Mexico_City",
      });
      const intent = await voicePost("/interpret", { text, fecha, tone: ELFIE_CFG.tone });
      if (intent && intent.intent && intent.intent !== "unknown") return intent;
      return null; // unknown → que lo intente Anthropic
    } catch (e) {
      console.warn("[elfie] interpret local falló:", e);
      return null;
    }
  };

  // --- Widget de métricas (CPU/RAM/GPU RTX 5060) ---
  function buildMetricsWidget() {
    if (document.getElementById("elfie-metrics")) return;
    const w = document.createElement("div");
    w.id = "elfie-metrics";
    w.style.cssText = [
      "position:fixed",
      "right:14px",
      "bottom:14px",
      "z-index:9999",
      "min-width:190px",
      "padding:10px 12px",
      "background:rgba(22,20,22,.94)",
      "border:1px solid rgba(185,150,168,.25)",
      "border-radius:10px",
      "font:11px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace",
      "color:#ECE8EA",
      "letter-spacing:.03em",
      "backdrop-filter:blur(4px)",
      "user-select:none",
      "box-shadow:0 6px 20px rgba(0,0,0,.35)",
    ].join(";");
    w.innerHTML =
      '<div style="font-size:9px;text-transform:uppercase;letter-spacing:.12em;opacity:.6;margin-bottom:6px">Sistema · Elfie</div>' +
      '<div id="em-rows"></div>';
    w.title = "Doble clic para ocultar";
    w.addEventListener("dblclick", () => (w.style.display = "none"));
    document.body.appendChild(w);
  }

  function bar(pct) {
    const p = Math.max(0, Math.min(100, Math.round(pct || 0)));
    const hue = p < 60 ? 335 : p < 85 ? 20 : 0; // rosa→coral→rojo
    return (
      `<span style="display:inline-block;width:54px;height:6px;border-radius:3px;` +
      `background:rgba(185,150,168,.18);vertical-align:middle;overflow:hidden">` +
      `<span style="display:block;height:100%;width:${p}%;background:hsl(${hue} 70% 55%)"></span></span>`
    );
  }

  function renderMetrics(m) {
    const rows = document.getElementById("em-rows");
    if (!rows) return;
    const line = (label, pct, txt) =>
      `<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;margin:3px 0">` +
      `<span style="opacity:.7">${label}</span>${bar(pct)}<span style="min-width:62px;text-align:right">${txt}</span></div>`;
    let html = "";
    html += line("CPU", m.cpu_percent, `${(m.cpu_percent || 0).toFixed(0)}%`);
    const ramPct = m.ram_total_gb ? (m.ram_used_gb / m.ram_total_gb) * 100 : 0;
    html += line("RAM", ramPct, `${(m.ram_used_gb || 0).toFixed(1)}/${(m.ram_total_gb || 0).toFixed(0)}G`);
    if (m.gpu_percent != null) {
      html += line("GPU", m.gpu_percent, `${m.gpu_percent}%`);
      if (m.gpu_vram_used_gb != null) {
        const vp = m.gpu_vram_total_gb ? (m.gpu_vram_used_gb / m.gpu_vram_total_gb) * 100 : 0;
        html += line("VRAM", vp, `${m.gpu_vram_used_gb.toFixed(1)}/${(m.gpu_vram_total_gb || 0).toFixed(0)}G`);
      }
      const extra = [];
      if (m.gpu_temp_c != null) extra.push(`${m.gpu_temp_c}°C`);
      if (m.gpu_power_w != null) extra.push(`${m.gpu_power_w.toFixed(0)}W`);
      if (extra.length)
        html += `<div style="text-align:right;opacity:.55;margin-top:2px">${extra.join(" · ")}</div>`;
    } else {
      html += `<div style="opacity:.45;margin-top:2px">GPU: NVML no disponible</div>`;
    }
    rows.innerHTML = html;
  }

  function applyMetricsWidget() {
    const on = !ELFIE_CFG.features || ELFIE_CFG.features.metricsWidget !== false;
    const ex = document.getElementById("elfie-metrics");
    if (on && !ex && document.body) buildMetricsWidget();
    else if (!on && ex) ex.remove();
  }
  // --- Orquestador de recursos (Fase 8.2): auto-baja a "bajos" bajo presión ---
  // Política en el cliente (ya recibe métricas). El mecanismo de GPU vive en el sidecar.
  const HEAVY_APPS = ["code", "idea64", "pycharm", "rider64", "clion", "devenv",
    "studio64", "unity", "unrealeditor", "godot", "blender"]; // IDEs/editores; los juegos los caza la métrica GPU
  let _autoDown = false, _prevMode = null, _hiStreak = 0, _loStreak = 0, _fgTick = 0, _fgHeavy = false;

  async function resourceGuard(m) {
    const f = ELFIE_CFG.features || {};
    if (!f.autoResources) return;
    // chequeo de primer plano: throttle ~cada 5 ticks (~15 s) porque refresca procesos
    if ((_fgTick++ % 5) === 0) {
      try {
        const fg = String(await invoke("foreground_app") || "").toLowerCase();
        _fgHeavy = !!fg && HEAVY_APPS.some((a) => fg.includes(a));
      } catch (_) { _fgHeavy = false; }
    }
    const vramPct = m.gpu_vram_total_gb ? (m.gpu_vram_used_gb / m.gpu_vram_total_gb) * 100 : 0;
    const pressure = vramPct >= 90 || (m.cpu_percent || 0) >= 90 || _fgHeavy;
    if (pressure) { _hiStreak++; _loStreak = 0; } else { _loStreak++; _hiStreak = 0; }

    if (!_autoDown && _hiStreak >= 2 && ELFIE_CFG.mode !== "bajos") {
      _prevMode = ELFIE_CFG.mode; _autoDown = true;
      window.ElfieConfig.applyMode("bajos");
      setWake(false);
      notify("Elfie · recursos", _fgHeavy ? "App pesada en primer plano → modo bajos recursos." : "Carga alta → modo bajos recursos.");
    } else if (_autoDown && _loStreak >= 4) {
      _autoDown = false;
      const back = _prevMode || "normal"; _prevMode = null;
      window.ElfieConfig.applyMode(back);
      setWake(!!(ELFIE_CFG.features && ELFIE_CFG.features.wake));
      try { await voicePost("/config", { model: ELFIE_CFG.localModel }); } catch (_) {}
      notify("Elfie · recursos", "Recursos liberados → modo " + back + ".");
    }
  }

  listen("elfie:metrics", (e) => { renderMetrics(e.payload); resourceGuard(e.payload); });

  // --- Wake word "Elfie" (opt-in, on-device vía Vosk en el sidecar) ---
  let wakeOn = false;
  let wakeLooping = false;

  async function wakeLoop() {
    if (wakeLooping) return;
    wakeLooping = true;
    while (wakeOn) {
      try {
        const r = await fetch(VOICE_URL + "/wake/next");
        const j = await r.json();
        if (j && j.text && typeof window.ejecutarComando === "function") {
          console.log("[elfie] (Elfie) dijiste:", j.text);
          if (window.PRTS_AI) window.PRTS_AI.attention = true;
          window.ejecutarComando(j.text, true);
          setTimeout(() => { if (window.PRTS_AI) window.PRTS_AI.attention = false; }, 2000);
        }
      } catch (e) {
        await new Promise((res) => setTimeout(res, 1500)); // sidecar ocupado/caído
      }
    }
    wakeLooping = false;
  }

  async function setWake(on) {
    wakeOn = on;
    if (ELFIE_CFG.features) ELFIE_CFG.features.wake = on;
    window.ElfieConfig.save();
    try {
      await voicePost(on ? "/wake/enable" : "/wake/disable");
    } catch (_) {}
    if (on) wakeLoop();
    window.dispatchEvent(new CustomEvent("elfie:wake-changed", { detail: on }));
  }

  window.elfieWake = {
    enable: () => setWake(true),
    disable: () => setWake(false),
    get enabled() { return wakeOn; },
  };

  // --- Aplicar configuración al cargar el dashboard ---
  async function applyElfie() {
    applyMetricsWidget();
    try { await voicePost("/config", { model: ELFIE_CFG.localModel }); } catch (_) {} // modelo LLM local
    const wantWake =
      (ELFIE_CFG.features && ELFIE_CFG.features.wake) || localStorage.getItem("prts_wake") === "1";
    if (wantWake && !wakeOn) setWake(true);
    // Abrir herramienta solicitada desde el módulo Elfie (?elfie=rutinas|monitor).
    const open = new URLSearchParams(location.search).get("elfie");
    if (open === "rutinas") setTimeout(() => window.elfieRoutines && window.elfieRoutines.openManager(), 400);
    else if (open === "monitor") setTimeout(() => window.elfieMonitor && window.elfieMonitor.open(), 400);
  }
  window.addEventListener("elfie:cfg-changed", applyMetricsWidget);

  if (document.readyState !== "loading") applyElfie();
  else document.addEventListener("DOMContentLoaded", applyElfie);

  console.log("[elfie] Puente desktop inicializado");
})();

// app/elfie/routines.js — Routine Engine Visual (Fase 5).
// Rutinas configurables (datos, no código): secuencia de pasos con delays.
// Almacenamiento en Supabase (tabla routines) con fallback a localStorage.
// Ejecución: las acciones nativas usan window.elfieSys (solo Tauri); navigate/
// spotify/say usan PRTS_AI. En web sin elfieSys, esos pasos se omiten sin romper.
(function () {
  "use strict";
  const LS_KEY = "prts_routines";
  let routines = [];

  const fromLS = () => {
    try { return JSON.parse(localStorage.getItem(LS_KEY) || "[]"); } catch (_) { return []; }
  };
  const toLS = () => localStorage.setItem(LS_KEY, JSON.stringify(routines));

  async function load() {
    const sb = window.sb;
    if (sb) {
      try {
        const { data, error } = await sb.from("routines").select("*").order("created_at");
        if (!error && data) { routines = data; toLS(); return routines; }
      } catch (_) {}
    }
    routines = fromLS();
    return routines;
  }

  async function save(r) {
    const sb = window.sb;
    const row = {
      name: r.name,
      trigger_phrase: r.trigger_phrase || null,
      shortcut: r.shortcut || null,
      steps: r.steps || [],
      is_active: r.is_active !== false,
    };
    if (sb) {
      try {
        if (r.id) {
          await sb.from("routines").update(row).eq("id", r.id);
        } else {
          const { data } = await sb.from("routines").insert(row).select().single();
          if (data) r.id = data.id;
        }
      } catch (_) {}
    }
    const i = routines.findIndex((x) => r.id && x.id === r.id);
    if (i >= 0) routines[i] = r; else routines.push(r);
    toLS();
  }

  async function remove(r) {
    const sb = window.sb;
    if (sb && r.id) { try { await sb.from("routines").delete().eq("id", r.id); } catch (_) {} }
    routines = routines.filter((x) => x !== r && (!r.id || x.id !== r.id));
    toLS();
  }

  // ---- Parser de pasos: texto simple ↔ steps[] ----
  const ALIASES = {
    app: "open_app", abrir: "open_app", abre: "open_app", open_app: "open_app",
    volumen: "set_volume", volume: "set_volume", set_volume: "set_volume",
    navegar: "navigate", ir: "navigate", navigate: "navigate",
    spotify: "spotify_preset", musica: "spotify_preset", música: "spotify_preset", spotify_preset: "spotify_preset",
    captura: "screenshot", screenshot: "screenshot",
    silenciar: "mute_toggle", mute: "mute_toggle", mute_toggle: "mute_toggle",
    decir: "say", say: "say",
    esperar: "wait", espera: "wait", wait: "wait",
  };

  function parseSteps(text) {
    const steps = [];
    for (const raw of (text || "").split("\n")) {
      const line = raw.trim();
      if (!line) continue;
      const m = line.match(/^([\wáéíóú]+)\s*[:=]?\s*(.*)$/i);
      if (!m) continue;
      const act = ALIASES[m[1].toLowerCase()];
      const val = m[2].trim();
      if (!act) continue;
      const step = { action: act, params: {}, delay_ms: 0 };
      if (act === "open_app") step.params.name = val;
      else if (act === "set_volume") step.params.level = parseInt(val) || 0;
      else if (act === "navigate") step.params.view = val.toLowerCase();
      else if (act === "spotify_preset") step.params.preset = val || "foco";
      else if (act === "say") step.params.text = val;
      else if (act === "wait") step.delay_ms = parseInt(val) || 500;
      steps.push(step);
    }
    return steps;
  }

  function stepsToText(steps) {
    return (steps || []).map((s) => {
      switch (s.action) {
        case "open_app": return "abrir: " + (s.params.name || "");
        case "set_volume": return "volumen: " + (s.params.level || 0);
        case "navigate": return "ir: " + (s.params.view || "");
        case "spotify_preset": return "spotify: " + (s.params.preset || "foco");
        case "say": return "decir: " + (s.params.text || "");
        case "wait": return "esperar: " + (s.delay_ms || 0);
        case "mute_toggle": return "silenciar";
        case "screenshot": return "captura";
        default: return s.action;
      }
    }).join("\n");
  }

  // ---- Ejecutor ----
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  async function execStep(s) {
    const sys = window.elfieSys, ai = window.PRTS_AI;
    try {
      switch (s.action) {
        case "open_app": if (sys) await sys.openApp(s.params.name); break;
        case "set_volume": if (sys) await sys.setVolume(s.params.level); break;
        case "mute_toggle": if (sys) await sys.muteToggle(); break;
        case "screenshot": if (sys) await sys.screenshot(false); break;
        case "navigate":
          if (ai && ai.executeIntent)
            await ai.executeIntent({ intent: "navigate", params: { view: s.params.view } }, { spoken: true });
          break;
        case "spotify_preset":
          if (ai && ai.executeIntent)
            await ai.executeIntent({ intent: "open", params: { deep_link: "spotify:preset:" + s.params.preset } }, { spoken: true });
          break;
        case "say": if (ai && ai.say) ai.say(s.params.text); break;
        case "wait": break;
      }
    } catch (e) {
      console.warn("[rutina] paso falló", s, e);
    }
  }

  async function run(r) {
    if (!r || !r.steps) return;
    for (const s of r.steps) {
      await execStep(s);
      if (s.delay_ms) await sleep(s.delay_ms);
    }
  }

  // Dispara por frase (voz/texto). Devuelve true si ejecutó una rutina.
  async function tryRun(text) {
    const t = (text || "").toLowerCase().trim();
    if (!t) return false;
    const hit = routines.find(
      (r) => r.is_active !== false && r.trigger_phrase && t.includes(r.trigger_phrase.toLowerCase())
    );
    if (!hit) return false;
    if (window.PRTS_AI && window.PRTS_AI.say) window.PRTS_AI.say("Ejecutando " + hit.name);
    await run(hit);
    return true;
  }

  window.elfieRoutines = {
    load, save, remove, run, tryRun, parseSteps, stepsToText,
    list: () => routines,
    openManager: () => openManager(),
  };

  // ---- Gestor visual (modal) ----
  let editing = null;
  function openManager() {
    load().then(render);
    let modal = document.getElementById("rutinas-modal");
    if (modal) { modal.style.display = "flex"; return; }
    modal = document.createElement("div");
    modal.id = "rutinas-modal";
    modal.style.cssText =
      "position:fixed;inset:0;z-index:10000;display:flex;align-items:center;justify-content:center;" +
      "background:rgba(6,10,18,.6);backdrop-filter:blur(3px)";
    modal.addEventListener("click", (e) => { if (e.target === modal) modal.style.display = "none"; });
    const card = document.createElement("div");
    card.id = "rutinas-card";
    card.style.cssText =
      "width:min(560px,92vw);max-height:86vh;overflow:auto;background:#161416;color:#ECE8EA;" +
      "border:1px solid rgba(185,150,168,.25);border-radius:14px;padding:18px 20px;" +
      "font:13px/1.5 system-ui,sans-serif;box-shadow:0 20px 60px rgba(0,0,0,.5)";
    modal.appendChild(card);
    document.body.appendChild(modal);
    render();
  }

  function h(tag, css, props) {
    const e = document.createElement(tag);
    if (css) e.style.cssText = css;
    Object.assign(e, props || {});
    return e;
  }

  function render() {
    const card = document.getElementById("rutinas-card");
    if (!card) return;
    card.innerHTML = "";
    const head = h("div", "display:flex;justify-content:space-between;align-items:center;margin-bottom:14px");
    head.append(
      h("div", "font-family:Georgia,serif;font-size:18px", { textContent: "Mis Rutinas" }),
      h("button", "background:transparent;color:#ADA3AA;border:none;font-size:20px;cursor:pointer",
        { textContent: "×", onclick: () => (document.getElementById("rutinas-modal").style.display = "none") })
    );
    card.appendChild(head);

    // Lista
    const list = h("div", "display:flex;flex-direction:column;gap:8px;margin-bottom:16px");
    if (!routines.length) list.appendChild(h("div", "opacity:.5;font-size:12px", { textContent: "Sin rutinas aún. Crea una abajo." }));
    routines.forEach((r) => {
      const row = h("div", "display:flex;align-items:center;gap:8px;padding:8px 10px;border:1px solid rgba(185,150,168,.18);border-radius:9px");
      const info = h("div", "flex:1;min-width:0");
      info.append(
        h("div", "font-weight:600", { textContent: r.name }),
        h("div", "font-size:11px;opacity:.6;font-family:ui-monospace,monospace",
          { textContent: [r.trigger_phrase ? '"' + r.trigger_phrase + '"' : null, (r.steps || []).length + " pasos"].filter(Boolean).join(" · ") })
      );
      const btn = (t, on) => h("button", "background:transparent;color:#ECE8EA;border:1px solid rgba(185,150,168,.3);border-radius:6px;padding:4px 8px;cursor:pointer;font-size:11px", { textContent: t, onclick: on });
      row.append(
        info,
        btn("▶", () => run(r)),
        btn("Editar", () => { editing = r; renderForm(); }),
        btn("✕", async () => { await remove(r); render(); })
      );
      list.appendChild(row);
    });
    card.appendChild(list);

    const add = h("button", "background:#B04A62;color:#fff;border:none;border-radius:8px;padding:8px 14px;cursor:pointer", { textContent: "+ Nueva rutina", onclick: () => { editing = { name: "", trigger_phrase: "", steps: [] }; renderForm(); } });
    card.appendChild(add);
    if (editing) renderForm();
  }

  function renderForm() {
    const card = document.getElementById("rutinas-card");
    if (!card) return;
    let form = document.getElementById("rutina-form");
    if (form) form.remove();
    form = h("div", "margin-top:16px;border-top:1px solid rgba(185,150,168,.18);padding-top:14px;display:flex;flex-direction:column;gap:8px");
    form.id = "rutina-form";
    const lbl = (t) => h("div", "font-size:11px;text-transform:uppercase;letter-spacing:.08em;opacity:.6", { textContent: t });
    const inputCss = "background:#0a1120;color:#ECE8EA;border:1px solid rgba(185,150,168,.3);border-radius:7px;padding:7px 9px;font:inherit;width:100%;box-sizing:border-box";
    const name = h("input", inputCss, { value: editing.name || "", placeholder: "Modo estudio" });
    const phrase = h("input", inputCss, { value: editing.trigger_phrase || "", placeholder: "modo estudio (frase de voz)" });
    const steps = h("textarea", inputCss + ";min-height:120px;font-family:ui-monospace,monospace;font-size:12px",
      { value: stepsToText(editing.steps), placeholder: "abrir: vscode\nesperar: 500\nspotify: foco\nvolumen: 40\nir: tareas" });
    form.append(lbl("Nombre"), name, lbl("Frase de voz (opcional)"), phrase,
      lbl("Pasos (uno por línea: abrir/volumen/ir/spotify/silenciar/captura/decir/esperar)"), steps);
    const hint = h("div", "font-size:11px;opacity:.5", { textContent: "Ej: «abrir: discord» · «volumen: 40» · «ir: tareas» · «esperar: 800»" });
    form.appendChild(hint);
    const bar = h("div", "display:flex;gap:8px;margin-top:6px");
    bar.append(
      h("button", "background:#B04A62;color:#fff;border:none;border-radius:8px;padding:8px 14px;cursor:pointer",
        { textContent: "Guardar", onclick: async () => {
          editing.name = name.value.trim() || "Rutina";
          editing.trigger_phrase = phrase.value.trim();
          editing.steps = parseSteps(steps.value);
          await save(editing);
          editing = null;
          render();
        } }),
      h("button", "background:transparent;color:#ADA3AA;border:1px solid rgba(185,150,168,.3);border-radius:8px;padding:8px 14px;cursor:pointer",
        { textContent: "Cancelar", onclick: () => { editing = null; render(); } })
    );
    form.appendChild(bar);
    card.appendChild(form);
  }

  // Carga inicial silenciosa (para que tryRun tenga datos sin abrir el gestor).
  if (window.sb || true) load();
})();

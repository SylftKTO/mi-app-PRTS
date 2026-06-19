// app/elfie/elfie-config.js — Config compartida de Elfie (single source of truth).
// La usan el dashboard (desktop.js la aplica) y el módulo Elfie (elfie.html la edita).
// Persiste en localStorage 'prts_elfie_cfg' + best-effort a Supabase elfie_config.
(function () {
  "use strict";
  const KEY = "prts_elfie_cfg";

  const TONOS = {
    profesional: "directa, eficiente, sin rodeos",
    casual: "informal y cálida, con comentarios breves",
    silenciosa: "mínima, de 1 a 2 palabras",
    tecnica: "datos concretos, sin suavizar",
    nocturna: "suave y tranquila",
  };

  const DEFAULTS = {
    personality: "profesional",
    voiceEngine: "kokoro", // kokoro | navegador | xtts (voz clonada)
    voiceSpeed: 1.0,
    ttsEnabled: true,
    xttsVoiceName: "",   // nombre del perfil de voz activo (XTTS)
    xttsSpeakerWav: "",  // ruta LOCAL del audio de referencia (solo este equipo → localStorage)
    interpreter: "local", // local (Ollama) | anthropic (Claude API)
    localModel: "qwen2.5:7b", // phi3.5 | qwen2.5:7b | llama3.1:8b
    features: { wake: false, voice: true, monitor: true, metricsWidget: true },
    customPersonalities: {}, // { nombre: "descripción del tono" }
  };

  function deepMerge(base, over) {
    const out = Array.isArray(base) ? base.slice() : Object.assign({}, base);
    for (const k in over) {
      if (over[k] && typeof over[k] === "object" && !Array.isArray(over[k])) {
        out[k] = deepMerge(base[k] || {}, over[k]);
      } else {
        out[k] = over[k];
      }
    }
    return out;
  }

  let data = deepMerge(DEFAULTS, (() => {
    try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (_) { return {}; }
  })());

  function personalities() {
    return Object.assign({}, TONOS, data.customPersonalities || {});
  }
  function tone() {
    return personalities()[data.personality] || TONOS.profesional;
  }
  data.tone = tone();

  function save() {
    data.tone = tone();
    localStorage.setItem(KEY, JSON.stringify(data));
    if (window.sb) {
      window.sb
        .from("elfie_config")
        .upsert({
          personality: data.personality,
          voice_engine: data.voiceEngine,
          voice_speed: data.voiceSpeed,
          tts_enabled: data.ttsEnabled,
          local_llm_model: data.localModel,
          updated_at: new Date().toISOString(),
        })
        .then(() => {}, () => {});
    }
    window.dispatchEvent(new CustomEvent("elfie:cfg-changed"));
  }

  window.ElfieConfig = { TONOS, DEFAULTS, data, save, tone, personalities };
})();

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
    // Perfil de personalidad (Fase 8.3b): ejes que componen el tono efectivo.
    iniciativa: "media",        // baja | media | alta — cuánto propone por su cuenta
    detalle: "normal",          // breve | normal | extenso — longitud de respuesta
    confirmaciones: "normales", // estrictas | normales | mínimas — cuánto pregunta antes de actuar
    personaDesc: "",            // arquetipo en texto libre (vacío = preset/identidad base)
    voiceEngine: "kokoro", // kokoro | navegador | xtts (voz clonada) | piper (ligera, Fase 9.1)
    voiceSpeed: 1.0,
    ttsEnabled: true,
    xttsVoiceName: "",   // nombre del perfil de voz activo (XTTS)
    xttsSpeakerWav: "",  // ruta LOCAL del audio de referencia (solo este equipo → localStorage)
    interpreter: "local", // local (Ollama) | anthropic (Claude API)
    localModel: "qwen2.5:7b", // phi3.5 | qwen2.5:7b | llama3.1:8b
    features: { wake: false, voice: true, monitor: true, metricsWidget: true, autoResources: true },
    customPersonalities: {}, // { nombre: "descripción del tono" }
    // Elfie Core (Fase 8.1): modo de operación. applyMode() ajusta varios knobs a la vez.
    mode: "normal",         // bajos | normal | conversacion | mascota
    sttContinuous: false,   // escucha semi-continua (modo conversación)
    memoryActive: true,     // memoria de largo plazo del chat
  };

  // Presets de modo: un cambio reconfigura wake/voz/intérprete/modelo/memoria de golpe.
  const MODES = {
    bajos:        { wake: false, voiceEngine: "navegador", interpreter: "anthropic", localModel: "phi3.5",    sttContinuous: false, memoryActive: false },
    normal:       { wake: true,  voiceEngine: "kokoro",    interpreter: "local",     localModel: "qwen2.5:7b", sttContinuous: false, memoryActive: true  },
    conversacion: { wake: true,  voiceEngine: "xtts",      interpreter: "local",     localModel: "qwen2.5:7b", sttContinuous: true,  memoryActive: true  },
    // Mascota (Fase 9.1): cerebro en la nube (Anthropic) + voz ligera Piper → GPU casi libre.
    mascota:      { wake: true,  voiceEngine: "piper",     interpreter: "anthropic", localModel: "phi3.5",    sttContinuous: false, memoryActive: true  },
  };

  // Ejes → frases que se inyectan al system prompt (chat.py / router) vía tone().
  const EJE_INICIATIVA = {
    baja: "Iniciativa baja: responde lo pedido, sin proponer de más.",
    media: "Iniciativa media: sugiere algo útil solo cuando aporte.",
    alta: "Iniciativa alta: anticipa necesidades y propón el siguiente paso.",
  };
  const EJE_DETALLE = {
    breve: "Sé muy breve, 1-2 frases.",
    normal: "",
    extenso: "Puedes extenderte cuando ayude a entender.",
  };
  const EJE_CONFIRM = {
    estrictas: "Confirma antes de cualquier acción que escriba o cambie datos.",
    normales: "",
    "mínimas": "Evita confirmaciones salvo en acciones irreversibles.",
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
  // Tono efectivo = arquetipo (texto libre o preset) + ejes de personalidad.
  function tone() {
    const base = (data.personaDesc && data.personaDesc.trim())
      || personalities()[data.personality] || TONOS.profesional;
    return [
      base,
      EJE_INICIATIVA[data.iniciativa] || "",
      EJE_DETALLE[data.detalle] || "",
      EJE_CONFIRM[data.confirmaciones] || "",
    ].filter(Boolean).join(" ");
  }
  data.tone = tone();

  // Aplica un modo (Elfie Core): ajusta wake/voz/intérprete/modelo/memoria y persiste.
  // Los efectos en el sidecar (wake enable/disable, /config) los aplica el consumidor
  // que escuche 'elfie:cfg-changed' o el propio selector en elfie.html.
  function applyMode(name) {
    const m = MODES[name];
    if (!m) return false;
    data.mode = name;
    data.features = data.features || {};
    data.features.wake = m.wake;
    data.voiceEngine = m.voiceEngine;
    data.interpreter = m.interpreter;
    data.localModel = m.localModel;
    data.sttContinuous = m.sttContinuous;
    data.memoryActive = m.memoryActive;
    save();
    return true;
  }

  function save() {
    data.tone = tone();
    localStorage.setItem(KEY, JSON.stringify(data));
    if (window.sb) {
      window.sb
        .from("elfie_config")
        .upsert({
          personality: data.personality,
          persona: {
            iniciativa: data.iniciativa,
            detalle: data.detalle,
            confirmaciones: data.confirmaciones,
            desc: data.personaDesc,
          },
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

  window.ElfieConfig = { TONOS, DEFAULTS, MODES, data, save, tone, personalities, applyMode };
})();

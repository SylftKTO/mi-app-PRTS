// app/elfie/chat.js — Puente del Chat de Elfie (Fase 7.1).
// Habla con el sidecar de voz (:7331): /chat/send, /chat/remember, /chat/recall,
// /chat/forget, /chat/memories, /chat/status. NO-OP en navegador web (sin Tauri no
// hay sidecar → available()=false; la página avisa que el chat es de escritorio).
//
// También centraliza el TTS del chat (Kokoro/XTTS) leyendo ElfieConfig, para no
// depender de desktop.js: PRTS_AI.say lo define el dashboard, pero esta página es
// autónoma. speak() divide la respuesta en frases y las locuta en orden.
(function () {
  "use strict";
  const VOICE_URL = "http://127.0.0.1:7331";
  const isDesktop = () => !!window.__TAURI__;

  async function post(path, body) {
    const r = await fetch(VOICE_URL + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    return r.json();
  }

  // --- TTS: frase a frase, en serie, vía el sidecar (Kokoro o XTTS) ---
  let speakChain = Promise.resolve();
  let speakOn = false;

  function ttsBody(text) {
    const cfg = (window.ElfieConfig && window.ElfieConfig.data) || {};
    const body = { text, speed: cfg.voiceSpeed || 1.0 };
    if (cfg.voiceEngine === "xtts" && cfg.xttsSpeakerWav) {
      body.engine = "xtts";
      body.speaker_wav = cfg.xttsSpeakerWav;
    }
    return body;
  }

  function partirFrases(text) {
    // Trozos hablables: corta por puntuación fuerte sin dejar frases minúsculas.
    return String(text || "")
      .replace(/\s+/g, " ")
      .match(/[^.!?…\n]+[.!?…]?/g) || [];
  }

  window.elfieChat = {
    available: isDesktop,

    async status() {
      if (!isDesktop()) return null;
      try {
        return await (await fetch(VOICE_URL + "/chat/status")).json();
      } catch (_) {
        return null;
      }
    },

    // Genera la respuesta de Elfie. history = [{role, content}, …] (cronológico).
    async send(history, tone) {
      if (!isDesktop()) return null;
      try {
        return await post("/chat/send", { history, tone: tone || "" });
      } catch (_) {
        return null;
      }
    },

    // Memoria de largo plazo.
    async remember(text, kind) {
      if (!isDesktop() || !text) return null;
      try { return await post("/chat/remember", { text, kind: kind || "hecho" }); }
      catch (_) { return null; }
    },
    async memories() {
      if (!isDesktop()) return null;
      try { return await (await fetch(VOICE_URL + "/chat/memories")).json(); }
      catch (_) { return null; }
    },
    async forget(id) {
      if (!isDesktop() || !id) return null;
      try { return await post("/chat/forget", { id }); }
      catch (_) { return null; }
    },

    // Extracción automática de hechos durables (segundo plano, no bloquea el chat).
    // Devuelve {ok, stored:[...]} o null. Pensada para fire-and-forget.
    async extract(history) {
      if (!isDesktop() || !history || !history.length) return null;
      try { return await post("/chat/extract", { history }); }
      catch (_) { return null; }
    },

    // Locuta una respuesta completa, frase a frase. Devuelve cuando termina.
    async speak(text) {
      if (!isDesktop()) return;
      const cfg = (window.ElfieConfig && window.ElfieConfig.data) || {};
      if (cfg.ttsEnabled === false) return;
      if (cfg.voiceEngine === "navegador") {
        if (window.PRTS_AI && window.PRTS_AI.say) window.PRTS_AI.say(text);
        return;
      }
      speakOn = true;
      const frases = partirFrases(text);
      speakChain = speakChain.then(async () => {
        for (const f of frases) {
          if (!speakOn) break;
          const t = f.trim();
          if (!t) continue;
          try { await post("/tts", ttsBody(t)); } catch (_) { /* sigue con la próxima */ }
        }
      });
      return speakChain;
    },

    stopSpeak() {
      speakOn = false;
    },
  };
})();

// app/elfie/rag.js — Puente RAG de Apuntes (Fase 6).
// Habla con el sidecar de voz de Elfie (proceso Python local) en :7331,
// que tiene embeddings (nomic/bge) + LanceDB. NO-OP en el navegador web:
// sin Tauri no hay sidecar → todos los métodos degradan a null sin romper nada.
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

  window.elfieRag = {
    available: isDesktop,

    // Estado del índice {ok, ready, count}. null si no hay desktop/sidecar.
    async status() {
      if (!isDesktop()) return null;
      try {
        const r = await fetch(VOICE_URL + "/rag/status");
        return await r.json();
      } catch (_) {
        return null;
      }
    },

    // Indexa/actualiza una nota (fire-and-forget; jamás rompe el guardado).
    async index(note) {
      if (!isDesktop() || !note || !note.id) return null;
      try {
        return await post("/rag/index", { note });
      } catch (_) {
        return null;
      }
    },

    // Quita una nota del índice al borrarla.
    async del(id) {
      if (!isDesktop() || !id) return null;
      try {
        return await post("/rag/delete", { id });
      } catch (_) {
        return null;
      }
    },

    // Reindexa todas las notas (backfill desde el frontend).
    async reindex(notes) {
      if (!isDesktop()) return null;
      try {
        return await post("/rag/index_batch", { notes: notes || [] });
      } catch (_) {
        return null;
      }
    },

    // Top-k apuntes más cercanos a la consulta.
    async query(q, k = 3) {
      if (!isDesktop()) return null;
      try {
        return await post("/rag/query", { q, k });
      } catch (_) {
        return null;
      }
    },

    // Respuesta hablada fundamentada SOLO en los apuntes (recupera + LLM local).
    async answer(q, k = 3) {
      if (!isDesktop()) return null;
      try {
        return await post("/rag/answer", { q, k });
      } catch (_) {
        return null;
      }
    },
  };
})();

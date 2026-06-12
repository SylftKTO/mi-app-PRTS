// PRTS · Fase 4.2 — Voz push-to-talk (solo escritorio Chromium).
// Gate de capacidad: webkitSpeechRecognition + dispositivo de escritorio.
// Mantener presionado el mic = escuchar; soltar = transcripción final.
// Degradación: sin soporte → el botón conserva su comportamiento de nota
// y la captura sigue siendo por texto. Nada se rompe.

(function () {
  "use strict";

  const PRTS_AI = (window.PRTS_AI = window.PRTS_AI || {});

  PRTS_AI.voiceAvailable = function () {
    const esEscritorio = window.matchMedia("(pointer: fine)").matches &&
      !/Android|iPhone|iPad|Mobile/i.test(navigator.userAgent);
    return "webkitSpeechRecognition" in window && esEscritorio;
  };

  /**
   * Habilita push-to-talk sobre un botón existente.
   * opts: { button, input, onFinal(transcript), onState('idle'|'listening'|'error', msg?) }
   * Devuelve true si la voz quedó habilitada; false si no hay soporte.
   */
  PRTS_AI.initVoice = function (opts) {
    if (!PRTS_AI.voiceAvailable()) return false;

    const { button, input, onFinal, onState } = opts;
    let rec = null;
    let escuchando = false;

    function start() {
      if (escuchando) return;
      rec = new window.webkitSpeechRecognition();
      rec.lang = "es-MX";
      rec.interimResults = true;   // transcripción en vivo en el input
      rec.continuous = false;
      escuchando = true;
      onState && onState("listening");
      button.classList.add("listening");

      rec.onresult = (ev) => {
        let interim = "", final = "";
        for (const r of ev.results) (r.isFinal ? (final += r[0].transcript) : (interim += r[0].transcript));
        if (input) input.value = (final + interim).trim();
        if (final && onFinal) { onFinal(final.trim()); if (input) input.value = ""; }
      };
      rec.onerror = (ev) => {
        onState && onState("error", ev.error === "not-allowed" ? "Permiso de micrófono denegado." : "Error de voz: " + ev.error);
        stop();
      };
      rec.onend = () => {
        escuchando = false;
        button.classList.remove("listening");
        onState && onState("idle");
      };
      try { rec.start(); } catch { /* start doble: ignorar */ }
    }

    function stop() {
      if (rec && escuchando) { try { rec.stop(); } catch { /* ya detenido */ } }
    }

    // Push-to-talk: presionar = escuchar, soltar = transcribir
    button.addEventListener("pointerdown", (e) => { e.preventDefault(); start(); });
    button.addEventListener("pointerup", stop);
    button.addEventListener("pointerleave", stop);
    button.addEventListener("contextmenu", (e) => e.preventDefault());
    return true;
  };
})();

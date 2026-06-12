// PRTS · Fase 5 — Wake word ("escucha continua").
//
// Enfoque sin dependencias: webkitSpeechRecognition en modo continuo como
// detector "suave" de palabra clave. Cuando una frase final contiene «PRTS»,
// el resto de la frase se enruta como comando (Fase 4.2). Si solo se dijo
// «PRTS», entra una ventana de escucha y la SIGUIENTE frase es el comando.
//
// Limitaciones honestas (documentadas):
//  - Solo escritorio Chromium (igual que push-to-talk).
//  - webkitSpeechRecognition ENVÍA el audio a Google para transcribir; en modo
//    continuo eso es audio ambiental constante mientras está activa. Por eso:
//    opt-in, apagada por defecto, con indicador visible. Para un detector
//    100% en el dispositivo, ver el adaptador Porcupine documentado en el README.
//  - Palabra clave HABLADA: «Priestess» (pronunciación inglesa "príst-es").
//    Se eligió sobre el acrónimo «PRTS» porque el reconocedor es-MX transcribe
//    mucho mejor una palabra pronunciable. WAKE acepta sus mis-hears comunes.
//    (Internamente el comando se normaliza con prefijo "PRTS, " para el router.)

(function () {
  "use strict";

  const PRTS_AI = (window.PRTS_AI = window.PRTS_AI || {});
  const KEY = "prts_wake_on";

  // «Priestess» (inglés) y sus transcripciones aproximadas en es-MX, con
  // muletilla opcional (hey/oye). Cubre: priestess, priestes, priesta, priest,
  // pristes, prist, preste(s), prís, pris…
  const WAKE = /\b(?:hey |oye )?(priest\w*|prist\w*|prest\w*|pr[ií]s\w*)\b/i;

  let rec = null, on = false, paused = false, restartT = null;
  let lastFire = 0, awaiting = false, awaitT = null;
  let onCommand = null, onState = null;

  const supported = () =>
    "webkitSpeechRecognition" in window &&
    window.matchMedia("(pointer: fine)").matches &&
    !/Android|iPhone|iPad|Mobile/i.test(navigator.userAgent);

  PRTS_AI.wakeSupported = supported;

  function emit(st) { onState && onState(st); }

  function start() {
    if (!on || paused || rec) return;
    rec = new window.webkitSpeechRecognition();
    rec.lang = "es-MX";
    rec.continuous = true;
    rec.interimResults = false;

    rec.onresult = (ev) => {
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        const r = ev.results[i];
        if (!r.isFinal) continue;
        const txt = r[0].transcript.trim();
        if (!txt) continue;

        // Ventana de escucha abierta tras un «PRTS» solo: esta frase es el comando.
        if (awaiting) {
          awaiting = false; clearTimeout(awaitT);
          dispara("PRTS, " + txt);
          continue;
        }
        const m = txt.match(WAKE);
        if (m && Date.now() - lastFire > 1500) {
          lastFire = Date.now();
          const resto = txt.slice(m.index + m[0].length).replace(/^[\s,.:]+/, "").trim();
          if (resto.length >= 2) {
            dispara("PRTS, " + resto);                     // frase única: «PRTS, pon música»
          } else {
            awaiting = true;                               // solo dijo «PRTS» → escucho lo siguiente
            emit("awaiting");
            clearTimeout(awaitT);
            awaitT = setTimeout(() => { awaiting = false; emit("listening"); }, 6000);
          }
        }
      }
    };
    rec.onerror = (e) => {
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        PRTS_AI.wakeSet(false); emit("denied");
      }
    };
    rec.onend = () => {
      rec = null;
      if (on && !paused) { clearTimeout(restartT); restartT = setTimeout(start, 300); }
    };

    try { rec.start(); emit("listening"); }
    catch { rec = null; }
  }

  function stop() {
    clearTimeout(restartT); clearTimeout(awaitT);
    awaiting = false;
    if (rec) { try { rec.onend = null; rec.stop(); } catch { /* ya detenido */ } rec = null; }
  }

  function dispara(cmd) { emit("trigger"); onCommand && onCommand(cmd); }

  // --- API pública ---
  PRTS_AI.initWake = function (opts) {
    onCommand = opts.onCommand; onState = opts.onState;
    on = supported() && localStorage.getItem(KEY) === "1";
    if (on) start();
    return on;
  };
  PRTS_AI.wakeOn = () => on;
  PRTS_AI.wakeSet = function (v) {
    on = !!v && supported();
    localStorage.setItem(KEY, on ? "1" : "0");
    if (on) start(); else { stop(); emit("off"); }
    return on;
  };
  // Coordinación: un solo reconocedor a la vez (push-to-talk y TTS la pausan).
  PRTS_AI.wakePause = () => { if (on) { paused = true; stop(); } };
  PRTS_AI.wakeResume = () => { if (on && paused) { paused = false; start(); } };
})();

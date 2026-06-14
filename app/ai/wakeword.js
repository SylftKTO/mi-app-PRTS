// PRTS · Fase 5 — Wake word ("escucha continua").
//
// Enfoque sin dependencias: webkitSpeechRecognition en modo continuo como
// detector "suave" de palabra clave. Cuando una frase final contiene «Dalia»,
// el resto de la frase se enruta como comando (Fase 4.2). Si solo se dijo
// «Dalia», entra una ventana de escucha y la SIGUIENTE frase es el comando.
//
// Segundo plano (Fase 5.0.1): para que siga escuchando con la pestaña detrás
// de otra ventana/pestaña se mantiene un stream de micrófono activo
// (getUserMedia). Un tab que captura audio queda EXENTO del throttling y del
// congelamiento de pestañas en segundo plano de Chromium, así los reinicios
// del reconocedor siguen disparándose. Un watchdog y el re-armado en
// visibilitychange/resume cubren los huecos.
//
// Limitaciones honestas (documentadas):
//  - Solo escritorio Chromium (igual que push-to-talk).
//  - "Segundo plano" = la pestaña sigue ABIERTA detrás de otra. Si cierras el
//    navegador o la laptop se suspende, no hay forma desde la web: eso requiere
//    el companion nativo (Nivel C, fuera de alcance — ver README/Fase5 doc).
//  - webkitSpeechRecognition ENVÍA el audio a Google para transcribir; en modo
//    continuo eso es audio ambiental constante mientras está activa. Por eso:
//    opt-in, apagada por defecto, con indicador visible (y el de micrófono del
//    navegador permanece encendido).
//  - Palabra clave HABLADA: «Dalia». Se eligió sobre el acrónimo «PRTS»
//    porque el reconocedor es-MX transcribe mucho mejor una palabra
//    pronunciable. WAKE acepta sus mis-hears comunes (dalía, dalia…).
//    (Internamente el comando se normaliza con prefijo "PRTS, " para el router.)

(function () {
  "use strict";

  const PRTS_AI = (window.PRTS_AI = window.PRTS_AI || {});
  const KEY = "prts_wake_on";

  // «Dalia» y sus transcripciones aproximadas en es-MX, con muletilla
  // opcional (hey/oye). Cubre: dalia, dalía, dalias…
  const WAKE = /\b(?:hey |oye )?Dal[ií]a\w*\b/i;

  let rec = null, on = false, paused = false, restartT = null, watchdog = null;
  let micStream = null;
  let lastFire = 0, awaiting = false, awaitT = null;
  let onCommand = null, onState = null;

  const supported = () =>
    "webkitSpeechRecognition" in window &&
    window.matchMedia("(pointer: fine)").matches &&
    !/Android|iPhone|iPad|Mobile/i.test(navigator.userAgent);

  PRTS_AI.wakeSupported = supported;

  function emit(st) { onState && onState(st); }

  // Retiene un micrófono activo mientras la escucha está encendida: mantiene la
  // pestaña "capturando audio" → exenta del throttling/congelamiento de
  // segundo plano, y deja visible el indicador de micrófono (privacidad).
  async function holdMic() {
    if (micStream || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      micStream = null;
      if (e && (e.name === "NotAllowedError" || e.name === "SecurityError")) {
        PRTS_AI.wakeSet(false); emit("denied");
      }
    }
  }
  function releaseMic() {
    if (micStream) { micStream.getTracks().forEach((t) => t.stop()); micStream = null; }
  }

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

        // Ventana de escucha abierta tras un «Dalia» solo: esta frase es el comando.
        if (awaiting) {
          awaiting = false; clearTimeout(awaitT);
          dispara("PRTS, " + txt);
          continue;
        }
        const m = txt.match(WAKE);
        if (m && Date.now() - lastFire > 1500) {
          lastFire = Date.now();
          const resto = txt.slice(m.index + m[0].length).replace(/^[\s,.:]+/, "").trim();
          const antes = txt.slice(0, m.index).replace(/[\s,.:]+$/, "").trim();
          if (resto.length >= 2) {
            dispara("PRTS, " + resto);                     // wake al inicio: «Dalia, pon música»
          } else if (antes.length >= 2) {
            dispara("PRTS, " + antes);                     // wake al final: «Pon música, Dalia» · «Buen día Dalia»
          } else {
            awaiting = true;                               // solo dijo «Dalia» → escucho lo siguiente
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

  // Watchdog: en segundo plano un onend puede no reprogramar a tiempo (o el
  // reconocedor muere en silencio). Este intervalo re-arma si quedó caído.
  // Con el micrófono retenido la pestaña no se congela, así que sigue corriendo.
  function startWatchdog() {
    if (watchdog) return;
    watchdog = setInterval(() => { if (on && !paused && !rec) start(); }, 3000);
  }
  function stopWatchdog() { clearInterval(watchdog); watchdog = null; }

  // Re-armar al cambiar de visibilidad o al reanudar la pestaña (Page Lifecycle).
  const rearm = () => { if (on && !paused && !rec) start(); };
  document.addEventListener("visibilitychange", rearm);
  document.addEventListener("resume", rearm);

  // --- API pública ---
  PRTS_AI.initWake = function (opts) {
    onCommand = opts.onCommand; onState = opts.onState;
    on = supported() && localStorage.getItem(KEY) === "1";
    if (on) { holdMic(); start(); startWatchdog(); }
    return on;
  };
  PRTS_AI.wakeOn = () => on;
  PRTS_AI.wakeSet = function (v) {
    on = !!v && supported();
    localStorage.setItem(KEY, on ? "1" : "0");
    if (on) { holdMic(); start(); startWatchdog(); }
    else { stopWatchdog(); stop(); releaseMic(); emit("off"); }
    return on;
  };
  // Coordinación: un solo reconocedor a la vez (push-to-talk y TTS la pausan).
  // El micrófono retenido NO se libera al pausar: así la pestaña sigue exenta
  // de throttling y la escucha vuelve al instante.
  PRTS_AI.wakePause = () => { if (on) { paused = true; stop(); } };
  PRTS_AI.wakeResume = () => { if (on && paused) { paused = false; start(); } };
})();

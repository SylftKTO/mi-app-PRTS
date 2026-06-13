// PRTS · Fase 4.2 — Ejecutor de intenciones (whitelist) + router local.
// La IA devuelve intenciones JSON; AQUÍ se ejecutan contra un vocabulario
// cerrado. Cualquier intención o deep link fuera de la lista se ignora.
// Nunca eval, nunca strings arbitrarios.

(function () {
  "use strict";

  const PRTS_AI = (window.PRTS_AI = window.PRTS_AI || {});

  // --- Whitelists ---
  const DEEP_LINK_PREFIXES = ["spotify:", "https://open.spotify.com/"];

  // Playlists preset (decisión §15.5: presets fijos, no API de Spotify).
  // ⚠️ COMPLETAR POR EL USUARIO: pega aquí los links de TUS playlists.
  //    En Spotify: playlist → ⋯ → Compartir → "Copiar enlace de playlist"
  //    (sirve el formato https://open.spotify.com/playlist/<id> o spotify:playlist:<id>).
  const PLAYLISTS = {
    estudio: "spotify:",   // TODO: playlist de estudio
    foco: "spotify:",      // TODO: playlist de foco/concentración
    entreno: "https://open.spotify.com/playlist/6zG8SofSyv5H9I3fWAfgJx",
  };
  // El LLM puede devolver "spotify:preset:estudio" → se resuelve aquí
  function resolverDeepLink(link) {
    const m = String(link).match(/^spotify:preset:(\w+)/);
    return m ? (PLAYLISTS[m[1]] || "spotify:") : link;
  }

  // Convierte un link web de Spotify a su URI de app (spotify:tipo:id) y viceversa,
  // para abrir la app de ESCRITORIO en lugar del navegador.
  function aSpotifyApp(url) {
    const m = String(url).match(/open\.spotify\.com\/(playlist|album|track|artist)\/([A-Za-z0-9]+)/);
    return m ? `spotify:${m[1]}:${m[2]}` : url;
  }
  function aSpotifyWeb(url) {
    if (/^https:\/\/open\.spotify\.com\//.test(url)) return url;
    const m = String(url).match(/^spotify:(playlist|album|track|artist):([A-Za-z0-9]+)/);
    return m ? `https://open.spotify.com/${m[1]}/${m[2]}` : null;
  }

  // Abre Spotify priorizando la app de escritorio (handler de protocolo spotify:).
  // Si la app no toma el foco en ~1.4 s (no instalada), cae al reproductor web.
  function abrirSpotify(link) {
    const uri = aSpotifyApp(link);
    const web = aSpotifyWeb(link);
    if (uri.startsWith("spotify:")) {
      // Lanza el handler del SO sin navegar fuera de PRTS.
      const ifr = document.createElement("iframe");
      ifr.style.display = "none";
      ifr.src = uri;
      document.body.appendChild(ifr);
      setTimeout(() => ifr.remove(), 1500);
      if (web) {
        const visibleAntes = !document.hidden;
        setTimeout(() => {
          // Si seguimos visibles, la app no abrió → fallback al web player.
          if (visibleAntes && !document.hidden) window.open(web, "_blank", "noopener");
        }, 1400);
      }
    } else {
      window.open(uri || link, "_blank", "noopener");
    }
  }
  const VIEWS_INTERNAS = { dashboard: null, tareas: null, semana: null, proyectos: null }; // vistas SPA (switchView)
  const PAGINAS = { gym: "gym.html", dieta: "dieta.html", apuntes: "apuntes.html" };       // páginas propias
  const ORIGENES = ["escuela", "wolves", "levelup", "personal"];
  const PRIORIDADES = ["alta", "media", "baja"];

  let deps = null; // { sb, switchView, notify, refresh }

  PRTS_AI.initActions = function (d) { deps = d; };

  const hoyMX = () => new Date().toLocaleDateString("en-CA", { timeZone: "America/Mexico_City" });

  // --- Respuesta hablada (TTS): PRTS lee sus respuestas en escritorio ---
  // speechSynthesis viene en el navegador: sin costo, sin backend, degrada solo.
  const puedeHablar = () =>
    "speechSynthesis" in window && window.matchMedia("(pointer: fine)").matches;
  PRTS_AI.ttsAvailable = puedeHablar;

  // Voz configurable (persistida): el usuario elige entre las voces del sistema.
  const VOICE_KEY = "prts_voice";
  let vozPreferida = (() => { try { return localStorage.getItem(VOICE_KEY) || ""; } catch { return ""; } })();
  PRTS_AI.getVoices = () => {
    if (!("speechSynthesis" in window)) return [];
    const todas = speechSynthesis.getVoices();
    const es = todas.filter((v) => /^es/i.test(v.lang));
    return es.length ? es : todas;   // si no hay voces es-*, mostrar todas
  };
  PRTS_AI.getVoice = () => vozPreferida;
  PRTS_AI.setVoice = (name) => {
    vozPreferida = name || "";
    try { localStorage.setItem(VOICE_KEY, vozPreferida); } catch { /* sin storage */ }
  };

  // Estado observable para la UI (animación del nodo PRTS en el mapa).
  PRTS_AI.speaking = false;
  PRTS_AI.attention = false;

  PRTS_AI.say = function (texto) {
    if (!puedeHablar() || !texto) return;
    try {
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(texto);
      u.lang = "es-MX";
      u.rate = 1.05;
      const voz = speechSynthesis.getVoices().find((v) => v.name === vozPreferida);
      if (voz) { u.voice = voz; u.lang = voz.lang; }
      // Pausa la escucha continua mientras PRTS habla, para no oírse a sí misma.
      if (PRTS_AI.wakePause) PRTS_AI.wakePause();
      u.onstart = () => { PRTS_AI.speaking = true; };
      u.onend = u.onerror = () => {
        PRTS_AI.speaking = false;
        if (PRTS_AI.wakeResume) PRTS_AI.wakeResume();
      };
      speechSynthesis.speak(u);
    } catch { /* sin voz: el texto ya se muestra */ }
  };

  // Toda respuesta del ejecutor se muestra Y se lee en voz alta
  const notify = (msg) => {
    if (deps && deps.notify) deps.notify(msg);
    PRTS_AI.say(msg);
  };

  // Abre Spotify intentando primero la APP DE ESCRITORIO (protocolo spotify:).
  // Si la app no captura el foco en ~1.5s, cae al reproductor web.
  function abrirSpotify(link) {
    let uri = link, web = link;
    const m = link.match(/^https:\/\/open\.spotify\.com\/(playlist|album|track|artist)\/([A-Za-z0-9]+)/);
    if (m) uri = `spotify:${m[1]}:${m[2]}`;
    else if (link.startsWith("spotify:")) {
      const p = link.split(":");
      web = p[1] && p[2] ? `https://open.spotify.com/${p[1]}/${p[2]}` : "https://open.spotify.com/";
    }
    const fallback = setTimeout(() => window.open(web, "_blank", "noopener"), 1500);
    const cancelar = () => { clearTimeout(fallback); window.removeEventListener("blur", cancelar); };
    window.addEventListener("blur", cancelar);   // la app tomó el foco → no abrir la web
    location.href = uri;
  }

  // --- Router local: intenciones simples SIN LLM (costo/latencia cero) ---
  // Devuelve una intención si el texto matchea un patrón conocido; null si es freeform.
  PRTS_AI.routeLocal = function (texto) {
    // Quita la muletilla de mando inicial: «PRTS» (normalizado) o la wake word
    // hablada («Dalia») y sus mis-hears.
    const t = texto.toLowerCase()
      .replace(/^(?:hola\s+|hey\s+|oye\s+)?(?:dal[ií]a\w*|prts)[,.]?\s*/i, "").trim();

    let m = t.match(/^(?:abre|abrir|ve a|vamos a|muestra|muéstrame)\s+(?:el |la |los |las |mis? )?(\w+)/);
    if (m) {
      const destino = m[1].replace(/s$/, ""); // tarea(s), proyecto(s)…
      const mapa = { dashboard: "dashboard", inicio: "dashboard", tarea: "tareas", semana: "semana",
                     proyecto: "proyectos", gym: "gym", gimnasio: "gym", dieta: "dieta", apunte: "apuntes" };
      if (mapa[destino]) return { intent: "navigate", params: { view: mapa[destino] }, speak: "Abriendo " + mapa[destino] + ".", confidence: 1 };
    }
    if (/resume|resumen|qué (hay|tengo|toca) hoy|cómo va (el|mi) día/.test(t)) {
      const scope = /tarea/.test(t) ? "tareas" : /gym|gimnasio|entrena/.test(t) ? "gym" : "dia";
      return { intent: "summary", params: { scope }, speak: "", confidence: 1 };
    }
    if (/clima|temperatura|va a llover|pronóstico/.test(t)) {
      return { intent: "weather", params: { location: null }, speak: "", confidence: 1 };
    }
    m = t.match(/^pon (?:la )?música(?:\s+(?:de|para)\s+(estudio|estudiar|foco|concentra\w*|entrenar|entreno|gym))?/);
    if (m) {
      const ctx = /estudi/.test(m[1] || "") ? "estudio" : /foco|concentra/.test(m[1] || "") ? "foco"
                : /entren|gym/.test(m[1] || "") ? "entreno" : "estudio";
      return { intent: "open", params: { target: "spotify", deep_link: "spotify:preset:" + ctx },
               speak: "Abriendo tu playlist de " + ctx + ".", confidence: 1 };
    }
    // "registra press banca 80 por 8" / "press banca 80 kg x 8" → serie de gym sin LLM
    m = t.match(/^(?:registra(?:r)?|anota(?:r)?|apunta(?:r)?)?\s*([a-záéíóúüñ][a-záéíóúüñ\s]*?)\s+(\d+(?:[.,]\d+)?)\s*(?:kg|kilos)?\s*(?:por|x|×)\s*(\d+)\b/);
    if (m) {
      return { intent: "log_set",
               params: { exercise: m[1].trim(), weight_kg: Number(m[2].replace(",", ".")), reps: Number(m[3]) },
               speak: "", confidence: 1 };
    }

    // --- Protocolos de respuesta simple (sin LLM, sin datos): hora, fecha, saludo… ---
    const di = (texto) => ({ intent: "say", params: {}, speak: texto, confidence: 1 });
    const ahora = new Date();
    const tz = { timeZone: "America/Mexico_City" };
    if (/(qué|que) hora|qué horas|dame la hora|hora es/.test(t))
      return di(`Son las ${ahora.toLocaleTimeString("es-MX", { ...tz, hour: "numeric", minute: "2-digit" })}.`);
    if (/(qué|que) (día|dia)( es)?|(qué|que) fecha|fecha de hoy|(día|dia) es hoy/.test(t))
      return di(`Hoy es ${ahora.toLocaleDateString("es-MX", { ...tz, weekday: "long", day: "numeric", month: "long" })}.`);
    if (/^(hola|qué onda|que onda|qué tal|que tal|hey|buen[oa]s)\b/.test(t)) {
      const h = Number(ahora.toLocaleString("en-US", { ...tz, hour: "numeric", hour12: false }));
      const saludo = h < 12 ? "Buenos días" : h < 19 ? "Buenas tardes" : "Buenas noches";
      return di(`${saludo}. ¿En qué te ayudo?`);
    }
    if (/^(gracias|muchas gracias|thank)/.test(t)) return di("De nada.");
    if (/cómo estás|como estas|cómo te sientes/.test(t)) return di("Operativa y a tus órdenes.");
    if (/ayuda|qué puedes hacer|que puedes hacer|qué sabes hacer|tus comandos|qué comandos/.test(t))
      return di("Puedo abrir módulos, resumir tu día, registrar tareas, peso y series de gym, poner música, darte el clima, la hora y responder preguntas rápidas.");

    return null;
  };

  // --- Ejecutor (switch cerrado sobre intent) ---
  // opts.spoken = el comando vino por voz (push-to-talk o escucha continua):
  // las escrituras se aplican sin modal y se confirman EN VOZ ALTA (manos libres).
  // Por teclado se mantiene confirm() como guardia.
  PRTS_AI.executeIntent = async function (it, opts) {
    if (!deps || !it || typeof it !== "object") return;
    const spoken = !!(opts && opts.spoken);
    switch (it.intent) {
      case "open": {
        const link = resolverDeepLink(it.params?.deep_link || "");
        if (!DEEP_LINK_PREFIXES.some((p) => link.startsWith(p))) { notify("Deep link no permitido."); return; }
        notify(it.speak || "Abriendo…");
        abrirSpotify(link);
        return;
      }
      case "weather": {
        await consultarClima(it.params?.location || null, it.speak);
        return;
      }
      case "say":      // protocolo de respuesta simple (local, sin LLM)
      case "ask": {    // pregunta cotidiana respondida por el LLM (en it.speak)
        notify(it.speak || "No tengo una respuesta para eso.");
        return;
      }
      case "navigate": {
        const v = String(it.params?.view || "");
        if (v in VIEWS_INTERNAS) { notify(it.speak || ""); deps.switchView(v); }
        else if (v in PAGINAS) { notify(it.speak || ""); location.href = PAGINAS[v]; }
        else notify("Vista no permitida.");
        return;
      }
      case "summary": {
        const { data: d, error } = await deps.sb.rpc("dashboard_brief");
        if (error || !d) { notify("No pude calcular el resumen."); return; }
        notify(resumenLocal(String(it.params?.scope || "dia"), d));
        return;
      }
      case "create_task": {
        const p = it.params || {};
        const title = String(p.title || "").trim();
        if (!title) return;
        const origin = ORIGENES.includes(p.origin) ? p.origin : "personal";
        const priority = PRIORIDADES.includes(p.priority) ? p.priority : "media";
        const deadline = /^\d{4}-\d{2}-\d{2}$/.test(p.deadline || "") ? p.deadline : null;
        // Por voz el comando dictado ES la disposición → aplica y confirma hablando.
        if (!spoken && !confirm(`Crear tarea: "${title}" · ${origin} · ${priority}${deadline ? " · " + deadline : ""}?`)) return;
        const { error } = await deps.sb.from("tasks").insert({ title, origin, priority, deadline });
        notify(error ? "No pude crear la tarea: " + error.message
                     : `Tarea creada: ${title}${deadline ? ", para el " + deadline : ""}.`);
        if (!error && deps.refresh) deps.refresh();
        return;
      }
      case "log_set": {
        const p = it.params || {};
        const kg = Number(p.weight_kg), reps = Math.round(Number(p.reps));
        const nombre = String(p.exercise || "").trim().toLowerCase();
        if (!nombre || !(kg > 0 && kg < 500) || !(reps > 0 && reps < 100)) return;
        // Resolver ejercicio del catálogo (todas las palabras dichas deben aparecer en el nombre)
        const { data: ejs } = await deps.sb.from("exercises").select("id, name").limit(200);
        const palabras = nombre.split(/\s+/);
        const ej = (ejs || []).find((e) => palabras.every((w) => e.name.toLowerCase().includes(w)));
        if (!ej) { notify(`No encontré "${nombre}" en tu catálogo de ejercicios.`); return; }
        if (!spoken && !confirm(`Registrar: ${ej.name} · ${kg} kg × ${reps}?`)) return;
        // Sesión de hoy (se crea si aún no existe; unique user+fecha)
        const hoy = hoyMX();
        let { data: ses } = await deps.sb.from("workout_sessions").select("id").eq("session_date", hoy).maybeSingle();
        if (!ses) {
          const r = await deps.sb.from("workout_sessions").insert({ session_date: hoy }).select("id").single();
          if (r.error) { notify("Error: " + r.error.message); return; }
          ses = r.data;
        }
        const { count } = await deps.sb.from("workout_sets")
          .select("id", { count: "exact", head: true }).eq("session_id", ses.id).eq("exercise_id", ej.id);
        const serie = (count || 0) + 1;
        const { error } = await deps.sb.from("workout_sets")
          .insert({ session_id: ses.id, exercise_id: ej.id, set_number: serie, weight_kg: kg, reps });
        notify(error ? "Error: " + error.message : `${ej.name}: ${kg} kg por ${reps}, serie ${serie}.`);
        if (!error && deps.refresh) deps.refresh();
        return;
      }
      case "log_weight": {
        const kg = Number(it.params?.weight_kg);
        if (!(kg > 0 && kg < 400)) return;
        const fecha = /^\d{4}-\d{2}-\d{2}$/.test(it.params?.date || "") ? it.params.date : hoyMX();
        if (!spoken && !confirm(`Registrar peso corporal: ${kg} kg (${fecha})?`)) return;
        const { error } = await deps.sb.from("body_weights")
          .upsert({ weight_kg: kg, measured_on: fecha }, { onConflict: "user_id,measured_on" });
        notify(error ? "Error: " + error.message : (it.speak || `Peso registrado: ${kg} kg.`));
        return;
      }
      default:
        // unknown o fuera de vocabulario → el llamador vuelca el texto a captura
        notify(it.speak || "No entendí el comando; lo guardo como captura.");
        return;
    }
  };

  // Clima vía Open-Meteo (gratuito, sin API key → no necesita Edge Function).
  // Ubicación: geolocalización del navegador (con permiso) o nombre de lugar.
  async function consultarClima(lugar, speak) {
    notify(speak || "Consultando el clima…");
    try {
      let lat, lon, etiqueta;
      if (lugar) {
        const g = await (await fetch("https://geocoding-api.open-meteo.com/v1/search?count=1&language=es&name=" + encodeURIComponent(lugar))).json();
        if (!g.results?.length) { notify(`No encontré "${lugar}".`); return; }
        ({ latitude: lat, longitude: lon, name: etiqueta } = g.results[0]);
      } else {
        const pos = await new Promise((res, rej) =>
          navigator.geolocation.getCurrentPosition(res, rej, { timeout: 8000, maximumAge: 600000 }));
        lat = pos.coords.latitude; lon = pos.coords.longitude; etiqueta = "tu ubicación";
      }
      const w = await (await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
        `&current=temperature_2m,precipitation,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max` +
        `&timezone=America%2FMexico_City&forecast_days=1`)).json();
      const c = w.current, d = w.daily;
      const desc = descClima(c.weather_code);
      notify(`${etiqueta[0].toUpperCase() + etiqueta.slice(1)}: ${Math.round(c.temperature_2m)}°C, ${desc}. ` +
        `Hoy ${Math.round(d.temperature_2m_min[0])}–${Math.round(d.temperature_2m_max[0])}°C, ` +
        `${d.precipitation_probability_max[0]}% prob. de lluvia.`);
    } catch (err) {
      notify(err?.code === 1 ? "Sin permiso de ubicación; di un lugar: \"PRTS, clima en Celaya\"."
                             : "No pude consultar el clima.");
    }
  }

  function descClima(code) {
    if (code === 0) return "despejado";
    if (code <= 2) return "parcialmente nublado";
    if (code === 3) return "nublado";
    if (code <= 48) return "neblina";
    if (code <= 67) return "lluvia";
    if (code <= 77) return "nieve";
    if (code <= 82) return "chubascos";
    return "tormenta";
  }

  function resumenLocal(scope, d) {
    if (scope === "tareas") {
      const u = d.tasks.urgent.length;
      return d.tasks.pending
        ? `${d.tasks.pending} pendientes${u ? `, ${u} urgentes: ` + d.tasks.urgent.slice(0, 3).map((t) => t.title).join("; ") : "."}`
        : "Sin tareas pendientes.";
    }
    if (scope === "gym") {
      return d.gym.has_routine_today
        ? `Hoy toca ${d.gym.routine}${d.gym.logged_today ? ` — ya llevas ${d.gym.sets_today} series.` : ", aún sin registrar."}`
        : "Hoy es día de descanso.";
    }
    const partes = [];
    partes.push(d.gym.has_routine_today ? `Gym: ${d.gym.routine}.` : "Gym: descanso.");
    partes.push(d.tasks.pending ? `Tareas: ${d.tasks.pending} pendientes.` : "Sin tareas pendientes.");
    if (d.week_today.length) partes.push(`${d.week_today.length} bloques en agenda.`);
    return partes.join(" ");
  }
})();

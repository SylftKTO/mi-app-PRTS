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
  const VIEWS_INTERNAS = { dashboard: null, tareas: null, semana: null, proyectos: null }; // vistas SPA (switchView)
  const PAGINAS = { gym: "gym.html", dieta: "dieta.html", apuntes: "apuntes.html" };       // páginas propias
  const ORIGENES = ["escuela", "wolves", "levelup", "personal"];
  const PRIORIDADES = ["alta", "media", "baja"];

  let deps = null; // { sb, switchView, notify, refresh }

  PRTS_AI.initActions = function (d) { deps = d; };

  const hoyMX = () => new Date().toLocaleDateString("en-CA", { timeZone: "America/Mexico_City" });
  const notify = (msg) => deps && deps.notify && deps.notify(msg);

  // --- Router local: intenciones simples SIN LLM (costo/latencia cero) ---
  // Devuelve una intención si el texto matchea un patrón conocido; null si es freeform.
  PRTS_AI.routeLocal = function (texto) {
    const t = texto.toLowerCase().replace(/^(hola\s+)?prts[,.]?\s*/i, "").trim();

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
    return null;
  };

  // --- Ejecutor (switch cerrado sobre intent) ---
  PRTS_AI.executeIntent = async function (it) {
    if (!deps || !it || typeof it !== "object") return;
    switch (it.intent) {
      case "open": {
        const link = resolverDeepLink(it.params?.deep_link || "");
        if (!DEEP_LINK_PREFIXES.some((p) => link.startsWith(p))) { notify("Deep link no permitido."); return; }
        notify(it.speak || "Abriendo…");
        window.open(link, "_blank", "noopener");
        return;
      }
      case "weather": {
        await consultarClima(it.params?.location || null, it.speak);
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
        // La IA propone, el humano dispone (Fase 4: siempre confirmar)
        if (!confirm(`Crear tarea: "${title}" · ${origin} · ${priority}${deadline ? " · " + deadline : ""}?`)) return;
        const { error } = await deps.sb.from("tasks").insert({ title, origin, priority, deadline });
        notify(error ? "Error: " + error.message : (it.speak || "Tarea creada."));
        if (!error && deps.refresh) deps.refresh();
        return;
      }
      case "log_weight": {
        const kg = Number(it.params?.weight_kg);
        if (!(kg > 0 && kg < 400)) return;
        const fecha = /^\d{4}-\d{2}-\d{2}$/.test(it.params?.date || "") ? it.params.date : hoyMX();
        if (!confirm(`Registrar peso corporal: ${kg} kg (${fecha})?`)) return;
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

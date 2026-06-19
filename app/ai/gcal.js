// PRTS · Fase 5 — Integración con Google Calendar (cliente puro).
//
// Por qué Calendar y no Web Push: el celular ya tiene la app de Google Calendar,
// que entrega la notificación a la hora con PRTS cerrado. PRTS solo crea el
// evento (con recordatorio "popup"); Google hace el resto. Cero backend de push.
//
// Auth: Google Identity Services (GIS), flujo de token. El access token (~1h)
// vive en memoria; se re-pide en silencio al expirar. Sin refresh token, sin
// secretos en el cliente → no hace falta Edge Function. El Client ID es público
// (va en config.js). Scope mínimo: calendar.events.
//
// Degradación: si no hay Client ID, o el usuario no conectó, o la API falla,
// las funciones devuelven null y el llamador guarda el recordatorio igual en
// Supabase (sin notificación al celular). Nada se rompe.

(function () {
  "use strict";

  const PRTS_AI = (window.PRTS_AI = window.PRTS_AI || {});
  const KEY = "prts_gcal_on";
  const SCOPE = "https://www.googleapis.com/auth/calendar.events";
  const GIS_SRC = "https://accounts.google.com/gsi/client";
  const API = "https://www.googleapis.com/calendar/v3/calendars/primary/events";
  const TZ = "America/Mexico_City";

  const clientId = () => (window.PRTS_CONFIG && PRTS_CONFIG.GOOGLE_CLIENT_ID) || "";

  let tokenClient = null;
  let accessToken = null;
  let tokenExp = 0;            // epoch ms de expiración
  let gisReady = null;         // promesa de carga del script GIS

  // Carga el script de Google Identity Services una sola vez.
  function loadGIS() {
    if (gisReady) return gisReady;
    gisReady = new Promise((resolve, reject) => {
      if (window.google && google.accounts && google.accounts.oauth2) return resolve();
      const s = document.createElement("script");
      s.src = GIS_SRC; s.async = true; s.defer = true;
      s.onload = () => resolve();
      s.onerror = () => reject(new Error("No se pudo cargar Google Identity Services."));
      document.head.appendChild(s);
    });
    return gisReady;
  }

  async function ensureTokenClient() {
    if (tokenClient) return tokenClient;
    if (!clientId()) throw new Error("Falta GOOGLE_CLIENT_ID en config.js.");
    await loadGIS();
    tokenClient = google.accounts.oauth2.initTokenClient({
      client_id: clientId(),
      scope: SCOPE,
      callback: () => {},   // se reemplaza por llamada en cada requestAccessToken
    });
    return tokenClient;
  }

  // Pide un token. interactive=true muestra el consentimiento; false intenta silencioso.
  function requestToken(interactive) {
    return new Promise((resolve, reject) => {
      tokenClient.callback = (resp) => {
        if (resp && resp.access_token) {
          accessToken = resp.access_token;
          tokenExp = Date.now() + (Number(resp.expires_in || 3600) - 60) * 1000;
          resolve(accessToken);
        } else {
          reject(new Error(resp && resp.error ? resp.error : "Sin token de Google."));
        }
      };
      try { tokenClient.requestAccessToken({ prompt: interactive ? "consent" : "" }); }
      catch (e) { reject(e); }
    });
  }

  async function getToken() {
    if (accessToken && Date.now() < tokenExp) return accessToken;
    await ensureTokenClient();
    return requestToken(false);   // silencioso (ya consentido en sesiones previas)
  }

  // Próxima fecha (local) de un weekday a una hora; si es hoy pero ya pasó → la próxima semana.
  function proximaOcurrencia(weekday, h, m) {
    const d = new Date(); d.setHours(h, m, 0, 0);
    let diff = (weekday - d.getDay() + 7) % 7;
    if (diff === 0 && d < new Date()) diff = 7;
    d.setDate(d.getDate() + diff);
    return d;
  }

  // --- API pública ---
  PRTS_AI.gcal = {
    available: () => !!clientId(),
    connected: () => { try { return localStorage.getItem(KEY) === "1"; } catch { return false; } },

    // Conexión interactiva (botón "Conectar Google Calendar"). Devuelve true/false.
    async connect() {
      try {
        await ensureTokenClient();
        await requestToken(true);
        localStorage.setItem(KEY, "1");
        return true;
      } catch { return false; }
    },

    disconnect() {
      try {
        if (accessToken && window.google && google.accounts && google.accounts.oauth2) {
          google.accounts.oauth2.revoke(accessToken, () => {});
        }
      } catch { /* ignorar */ }
      accessToken = null; tokenExp = 0;
      try { localStorage.setItem(KEY, "0"); } catch { /* sin storage */ }
    },

    // Construye el cuerpo del evento desde un recordatorio {title, notes, remind_at, lead_minutes}.
    // remind_at = ISO; el evento dura 30 min y el popup avisa lead_minutes antes.
    _evento(rem) {
      const start = new Date(rem.remind_at);
      const end = new Date(start.getTime() + 30 * 60000);
      const lead = Math.max(0, Math.round(Number(rem.lead_minutes) || 0));
      return {
        summary: "⏰ " + (rem.title || "Recordatorio"),
        description: (rem.notes ? rem.notes + "\n\n" : "") + "Creado por PRTS.",
        start: { dateTime: start.toISOString(), timeZone: TZ },
        end: { dateTime: end.toISOString(), timeZone: TZ },
        reminders: { useDefault: false, overrides: [{ method: "popup", minutes: lead }] },
      };
    },

    // Crea el evento. Devuelve el id de Google, o null si no se pudo (degradación).
    async createEvent(rem) {
      if (!this.connected() || !this.available()) return null;
      try {
        const token = await getToken();
        const r = await fetch(API, {
          method: "POST",
          headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
          body: JSON.stringify(this._evento(rem)),
        });
        if (!r.ok) return null;
        return (await r.json()).id || null;
      } catch { return null; }
    },

    async updateEvent(eventId, rem) {
      if (!eventId || !this.connected() || !this.available()) return null;
      try {
        const token = await getToken();
        const r = await fetch(`${API}/${encodeURIComponent(eventId)}`, {
          method: "PATCH",
          headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
          body: JSON.stringify(this._evento(rem)),
        });
        return r.ok ? eventId : null;
      } catch { return null; }
    },

    async deleteEvent(eventId) {
      if (!eventId || !this.connected() || !this.available()) return false;
      try {
        const token = await getToken();
        const r = await fetch(`${API}/${encodeURIComponent(eventId)}`, {
          method: "DELETE",
          headers: { Authorization: "Bearer " + token },
        });
        return r.ok || r.status === 410;   // 410 = ya borrado
      } catch { return false; }
    },

    // --- Clases LevelUp: evento con duración real y, si es recurrente, RRULE semanal ---
    // cls = { title, language, level, format, kind, weekday, class_date, start_time, duration_min }
    _eventoClase(cls) {
      const [h, m] = String(cls.start_time).slice(0, 5).split(":").map(Number);
      let start;
      if (cls.kind === "recurrente") start = proximaOcurrencia(cls.weekday, h, m);
      else { start = new Date(cls.class_date + "T00:00:00"); start.setHours(h, m, 0, 0); }
      const end = new Date(start.getTime() + (Number(cls.duration_min) || 60) * 60000);
      const ev = {
        summary: "📘 " + (cls.title || "Clase LevelUp"),
        description: [cls.language && ("Idioma: " + cls.language), cls.level && ("Nivel/tema: " + cls.level),
          cls.format && ("Formato: " + cls.format)].filter(Boolean).join("\n") + "\n\nLevelUp · PRTS",
        start: { dateTime: start.toISOString(), timeZone: TZ },
        end: { dateTime: end.toISOString(), timeZone: TZ },
        reminders: { useDefault: false, overrides: [{ method: "popup", minutes: 30 }] },
      };
      if (cls.kind === "recurrente") ev.recurrence = ["RRULE:FREQ=WEEKLY"];
      return ev;
    },
    async createClass(cls) {
      if (!this.connected() || !this.available()) return null;
      try {
        const token = await getToken();
        const r = await fetch(API, {
          method: "POST",
          headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
          body: JSON.stringify(this._eventoClase(cls)),
        });
        return r.ok ? ((await r.json()).id || null) : null;
      } catch { return null; }
    },
    async updateClass(eventId, cls) {
      if (!eventId || !this.connected() || !this.available()) return null;
      try {
        const token = await getToken();
        const r = await fetch(`${API}/${encodeURIComponent(eventId)}`, {
          method: "PATCH",
          headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
          body: JSON.stringify(this._eventoClase(cls)),
        });
        return r.ok ? eventId : null;
      } catch { return null; }
    },
  };
})();

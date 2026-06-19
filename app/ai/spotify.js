// app/ai/spotify.js — Control real de Spotify vía Web API (PRTS).
// OAuth Authorization Code + PKCE (sin secreto → seguro en cliente). El refresh
// token vive en localStorage; el access token (~1h) en memoria y se renueva solo.
// Funciona en web y escritorio. Degradación: si no hay CLIENT_ID o no está
// conectado, los métodos devuelven {ok:false} y el llamador cae a deep links.
//
// La reproducción (play/pause/next/volumen) requiere Spotify Premium y un
// dispositivo activo. Sin dispositivo activo devuelve {ok:false, reason:"no_device"}
// para que el llamador abra la app de Spotify y reintente.
(function () {
  "use strict";
  const PRTS_AI = (window.PRTS_AI = window.PRTS_AI || {});
  const KEY_RT = "prts_spotify_rt";       // refresh token
  const KEY_PKCE = "prts_spotify_pkce";   // {verifier, state} durante el flujo
  const API = "https://api.spotify.com/v1";
  const SCOPES = [
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "playlist-read-private",
    "streaming",
  ].join(" ");

  const clientId = () => (window.PRTS_CONFIG && PRTS_CONFIG.SPOTIFY_CLIENT_ID) || "";
  const redirectUri = () => location.origin + "/spotify-callback.html";

  let accessToken = "";
  let tokenExp = 0;

  // ---- PKCE helpers ----
  function rand(n) {
    const a = new Uint8Array(n);
    crypto.getRandomValues(a);
    return Array.from(a, (b) => ("0" + (b & 0xff).toString(16)).slice(-2)).join("");
  }
  function b64url(buf) {
    return btoa(String.fromCharCode(...new Uint8Array(buf)))
      .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  async function challenge(verifier) {
    const data = new TextEncoder().encode(verifier);
    return b64url(await crypto.subtle.digest("SHA-256", data));
  }

  async function tokenRequest(body) {
    const r = await fetch("https://accounts.spotify.com/api/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams(body),
    });
    if (!r.ok) throw new Error("token " + r.status);
    return r.json();
  }

  function setTokens(j) {
    if (j.access_token) {
      accessToken = j.access_token;
      tokenExp = Date.now() + (Number(j.expires_in || 3600) - 60) * 1000;
    }
    if (j.refresh_token) {
      try { localStorage.setItem(KEY_RT, j.refresh_token); } catch (_) {}
    }
  }

  async function getToken() {
    if (accessToken && Date.now() < tokenExp) return accessToken;
    const rt = (() => { try { return localStorage.getItem(KEY_RT); } catch { return null; } })();
    if (!rt) throw new Error("no conectado");
    const j = await tokenRequest({
      grant_type: "refresh_token", refresh_token: rt, client_id: clientId(),
    });
    setTokens(j);
    return accessToken;
  }

  // ---- Llamada REST autenticada. Devuelve {ok, status, data} sin lanzar. ----
  async function api(method, path, body) {
    let token;
    try { token = await getToken(); } catch (e) { return { ok: false, reason: "auth", error: String(e) }; }
    const opts = { method, headers: { Authorization: "Bearer " + token } };
    if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
    let r;
    try { r = await fetch(API + path, opts); } catch (e) { return { ok: false, reason: "net", error: String(e) }; }
    if (r.status === 204) return { ok: true, data: null };
    if (r.status === 404) return { ok: false, reason: "no_device" }; // sin dispositivo activo
    if (r.status === 403) return { ok: false, reason: "premium" };   // requiere Premium
    let data = null;
    try { data = await r.json(); } catch (_) {}
    return { ok: r.ok, status: r.status, data };
  }

  // ---- Conexión (popup PKCE) ----
  function connect() {
    return new Promise(async (resolve, reject) => {
      const cid = clientId();
      if (!cid) return reject(new Error("Falta SPOTIFY_CLIENT_ID en config.js"));
      const verifier = rand(48);
      const state = rand(8);
      try { localStorage.setItem(KEY_PKCE, JSON.stringify({ verifier, state })); } catch (_) {}
      const url = "https://accounts.spotify.com/authorize?" + new URLSearchParams({
        client_id: cid, response_type: "code", redirect_uri: redirectUri(),
        code_challenge_method: "S256", code_challenge: await challenge(verifier),
        scope: SCOPES, state,
      });
      const pop = window.open(url, "spotify-auth", "width=480,height=720");
      if (!pop) return reject(new Error("Permite las ventanas emergentes para conectar Spotify."));
      const onMsg = async (ev) => {
        if (ev.origin !== location.origin || !ev.data || ev.data.type !== "spotify-auth") return;
        window.removeEventListener("message", onMsg);
        try {
          const { code, state: st } = ev.data;
          const saved = JSON.parse(localStorage.getItem(KEY_PKCE) || "{}");
          if (!code || st !== saved.state) throw new Error("estado inválido");
          const j = await tokenRequest({
            grant_type: "authorization_code", code, redirect_uri: redirectUri(),
            client_id: cid, code_verifier: saved.verifier,
          });
          setTokens(j);
          localStorage.removeItem(KEY_PKCE);
          resolve(true);
        } catch (e) { reject(e); }
      };
      window.addEventListener("message", onMsg);
    });
  }

  function disconnect() {
    accessToken = ""; tokenExp = 0;
    try { localStorage.removeItem(KEY_RT); } catch (_) {}
  }

  // ---- API pública de control ----
  PRTS_AI.spotify = {
    available: () => !!clientId(),
    connected() { try { return !!localStorage.getItem(KEY_RT); } catch { return false; } },
    connect, disconnect,

    play: (opts) => api("PUT", "/me/player/play", opts || {}),       // {context_uri} o {uris:[...]}
    pause: () => api("PUT", "/me/player/pause"),
    resume: () => api("PUT", "/me/player/play", {}),
    next: () => api("POST", "/me/player/next"),
    previous: () => api("POST", "/me/player/previous"),
    volume: (pct) => api("PUT", `/me/player/volume?volume_percent=${Math.max(0, Math.min(100, Math.round(pct)))}`),
    current: () => api("GET", "/me/player/currently-playing"),
    state: () => api("GET", "/me/player"),  // dispositivo activo + volumen

    // Sube/baja el volumen de forma relativa (lee el estado actual). delta en %.
    async nudgeVolume(delta) {
      const s = await this.state();
      if (!s.ok || !s.data || !s.data.device) return s.ok ? { ok: false, reason: "no_device" } : s;
      const cur = Number(s.data.device.volume_percent || 50);
      const r = await this.volume(cur + delta);
      return r.ok ? { ok: true, volume: Math.max(0, Math.min(100, cur + delta)) } : r;
    },

    // Busca y reproduce. type: track|playlist|album|artist.
    async searchAndPlay(query, type = "track") {
      const q = encodeURIComponent(query);
      const res = await api("GET", `/search?q=${q}&type=${type}&limit=1`);
      if (!res.ok) return res;
      const key = type + "s";
      const item = res.data && res.data[key] && res.data[key].items && res.data[key].items[0];
      if (!item) return { ok: false, reason: "not_found" };
      const body = type === "track" ? { uris: [item.uri] } : { context_uri: item.uri };
      const pr = await this.play(body);
      return pr.ok ? { ok: true, name: item.name, uri: item.uri } : pr;
    },

    // Reproduce un URI/­link de Spotify (playlist/album/track).
    async playUri(uri) {
      const m = String(uri).match(/(?:spotify:|open\.spotify\.com\/)(playlist|album|artist|track)[:/]([A-Za-z0-9]+)/);
      if (!m) return { ok: false, reason: "bad_uri" };
      const u = `spotify:${m[1]}:${m[2]}`;
      return this.play(m[1] === "track" ? { uris: [u] } : { context_uri: u });
    },
  };

  // Completa el flujo si esta misma pestaña volvió con ?code (fallback sin popup).
  (function maybeHandleRedirect() {
    const p = new URLSearchParams(location.search);
    if (!p.get("code") || !location.pathname.includes("spotify-callback")) return;
  })();
})();

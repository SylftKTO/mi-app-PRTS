// Configuración de Supabase
// Copia estos valores desde: Supabase Dashboard → Project Settings → API
// La anon key es pública por diseño (la seguridad real la da RLS).
window.PRTS_CONFIG = {
  SUPABASE_URL: "https://mzefckjimfilhmdvmjom.supabase.co",
  SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16ZWZja2ppbWZpbGhtZHZtam9tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODExMzU5MTAsImV4cCI6MjA5NjcxMTkxMH0.OX9Y_O_H6zHyXqz-UVqSZdnCVvlLOoLdB5WT2cy85Yg",

  // Google Calendar (recordatorios → notificación al celular). Público por diseño.
  // Obténlo en Google Cloud Console → APIs y servicios → Credenciales →
  // "ID de cliente de OAuth" (tipo Aplicación web). Habilita "Google Calendar API"
  // y agrega tus orígenes JS autorizados (tu URL de Vercel y http://localhost:3210).
  // Mientras esté vacío, los recordatorios se guardan en PRTS pero NO notifican al celular.
  GOOGLE_CLIENT_ID: "824747017360-iq1mcbsitsq75vt1nmfe2a6h7c23qsoc.apps.googleusercontent.com",

  // Spotify Web API (control real: reproducir/pausar/buscar). Público por diseño (OAuth PKCE, sin secreto).
  // Setup en developer.spotify.com → Create app → copia el Client ID aquí. En "Redirect URIs"
  // agrega: <tu URL de Vercel>/spotify-callback.html y http://localhost:3210/spotify-callback.html
  // La reproducción requiere Spotify Premium + un dispositivo activo. Vacío = se usan deep links.
  SPOTIFY_CLIENT_ID: "",
};

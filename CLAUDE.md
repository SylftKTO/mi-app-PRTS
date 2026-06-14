# CLAUDE.md — PRTS

Sistema personal de organización de Sergio (Sylft): estudiante TecNM Celaya, instructor (Wolves robótica / LevelUp idiomas), atleta de gym. Usuario único. Idioma: **español (es-MX)** — UI, commits y documentación en español.

## Stack

- **Frontend:** HTML/JS **vanilla** (sin frameworks, sin build step). Cada módulo es un HTML autocontenido en `app/`. PWA (`manifest.json`, `sw.js`). Deploy en Vercel con root `app/`.
- **Backend:** Supabase — Postgres con **RLS** (`owner_all`, `auth.uid() = user_id`), Auth, **Edge Functions** (Deno/TS) para la capa IA.
- **LLM:** Anthropic (Claude tier económico) vía Edge Functions; la API key vive solo en Supabase secrets, **nunca en el cliente**.

## Comandos

```bash
npm run dev          # npx serve app
npm run db:push      # supabase db push (aplicar migraciones)
npm run db:new       # supabase migration new <nombre>
supabase functions deploy <nombre>
```

> Git y `supabase` los corre el usuario en PowerShell cuando hay deploy/push real.

## Estructura

```
app/                 # frontend: index.html (dashboard+tareas+inbox, ~1500 líneas), gym.html, dieta.html, apuntes.html
app/config.js        # URL + anon key de Supabase (pública por diseño)
app/styles.css       # tokens compartidos de diseño — único idioma visual
supabase/migrations/ # SQL versionado (timestamp YYYYMMDDNNNNNN_nombre.sql)
supabase/functions/  # Edge Functions: generate-briefing + _shared/ (llm.ts, prompts/*.vN.ts)
docs/Fase4_Arquitectura_IA.md  # ARQUITECTURA DE REFERENCIA para Fase 4 — leer antes de tocar la capa IA
PRODUCT.md / DESIGN.md         # identidad, principios de diseño, anti-referencias
```

## Convenciones

- **SQL:** tablas con `user_id default auth.uid()` (excepto las que escribe la Edge Function con service role → `user_id` explícito), RLS `owner_all`, TZ `America/Mexico_City`.
- **Diseño:** navy profundo, serif para títulos/cifras, mono mayúsculas para etiquetas, un solo acento azul acero. Nada de gamificación, gradientes ni glassmorphism. Targets táctiles ≥44px. Contraste AA. `prefers-reduced-motion`.
- **Prompts versionados:** `supabase/functions/_shared/prompts/<agente>.vN.ts`; cada llamada registra `prompt_version` en `ai_calls`.
- **Filosofía de fases:** un módulo a la vez; uso real antes de avanzar.

## Capa IA — principios no negociables (Fase 4)

1. **Degradación total:** si la IA falla o se apaga, todo tiene camino manual (el dashboard ya cae a `frasesBriefing()` determinista). Circuit breaker ante fallos repetidos.
2. **Intenciones, no ejecución:** el LLM devuelve JSON validado (Zod / tool calling); el **cliente** ejecuta contra whitelist cerrada (deep links permitidos: `spotify:`, `https://open.spotify.com/`, rutas internas). Nunca `eval`, nunca strings arbitrarios.
3. **La IA propone, el humano dispone:** en Fase 4 toda escritura a módulos pasa por tarjeta de confirmación. Nunca escribe en silencio.
4. **Costo observable:** cada llamada se registra en `ai_calls` (tokens, costo, `prompt_version`); tope mensual en `ai_settings` con `ai_spend_month()`; al superarlo, degradación automática.
5. **Contexto mínimo:** inyectar `dashboard_brief()` + lo necesario, nunca tablas completas.

### Estado actual

- ✅ **4.0** completada: migración `..0008_ai_layer.sql` (`ai_calls`, `daily_briefings`, `ai_settings`), `_shared/llm.ts`, `generate-briefing`, briefing diario pre-generado (~10:30 MX, lectura instantánea desde `daily_briefings`).
- ✅ **4.1 — Inbox (sugerir-y-confirmar):** Edge Function `process-inbox` (JWT del usuario, no service role) clasifica `inbox_entries` pendientes → sugerencia `{module, action, payload, confidence, summary}` validada en `_shared/schemas.ts`. Si `confidence ≥ 0.8` → tarjeta [Confirmar] [Editar] [Descartar] en el dashboard; al confirmar, el **cliente** inserta en la tabla destino y marca `status='procesada'` con `result = {module, target_id, summary}`. Editar = navegar al módulo (la entrada queda pendiente).
- ✅ **4.2 — Voz push-to-talk + comandos:** `app/ai/voice.js` (gate: `webkitSpeechRecognition` + escritorio; en móvil se oculta el botón) sobre `#cap-voz` (`pointerdown`/`pointerup`, `es-MX`). Router híbrido: patrones locales sin LLM en `PRTS_AI.routeLocal` (navegar, resumir); lo freeform → Edge Function `interpret-command` → intención del vocabulario cerrado (`open|navigate|summary|create_task|log_weight|unknown`) ejecutada por `app/ai/actions.js` (whitelist; `create_task`/`log_weight` con `confirm()`). "PRTS, …" escrito en el input de captura también enruta como comando. Wake word: **fuera de alcance**.

- ✅ **4.3 — Acciones automáticas:** migración `..0009_ai_auto_insights.sql` añade `ai_settings.auto_modules` (jsonb por módulo) y `auto_threshold` (default 0.90). Al procesar el inbox, si el módulo está habilitado y `confidence ≥ auto_threshold` → el cliente aplica sin confirmar y muestra tarjeta verde con **Deshacer** (borra el registro creado y la captura vuelve a `pendiente`). Acierto medido con `ai_inbox_accuracy()` (los rechazos guardan `result.suggested_module`); se muestra en el panel "Automático" para decidir qué activar. Todo apagado por defecto: el usuario activa módulo por módulo con datos.
- ✅ **4.4 — Insights:** Edge Function `generate-insights` (JWT del usuario) agrega ~4 semanas (sesiones gym + progresión por ejercicio, peso corporal, kcal/proteína por día, tareas por origen) en un JSON compacto → prompt `insights.v1` → 2-5 hallazgos `{kind, title, detail}` validados y guardados en `ai_insights` (upsert por `user_id, period_end`). Panel "PRTS · Insights" en el dashboard lee el último análisis; botón "Analizar patrones". Responde `insufficient` si hay <~2 semanas de datos.

### Cierre de Fase 4 (todo lo planeado, excepto wake word)

- ✅ Circuit breaker (§10.5) en `_shared/llm.ts`: 3 fallos consecutivos → pausa de 5 min (estado en memoria del isolate); el llamador degrada a manual.
- ✅ `ai/evals/` (§10.7): casos `inbox`/`command` en JSONL + runner Deno (`ai/evals/run.ts`); correr antes de subir un `prompt.vN+1` (ver su README).
- ✅ Intent `weather`: resuelto **en el cliente** con Open-Meteo (gratuita, sin key → sin Edge Function). Geolocalización del navegador o lugar nombrado ("clima en Celaya"). Prompt subido a `command.v2`.
- ✅ Playlists Spotify (§15.5): presets fijos en `app/ai/actions.js` (`PLAYLISTS`); el LLM/router devuelve `spotify:preset:<ctx>` y el cliente lo resuelve. **El usuario debe pegar los links de sus playlists** (marcado con TODO).
- ✅ Tarifas vigentes (Haiku 4.5): `LLM_PRICE_IN=1.00`, `LLM_PRICE_OUT=5.00` USD/M tokens.
- ❌ Wake word: fuera de alcance por decisión (§2); extensión futura con Picovoice Porcupine en primer plano.

### Extras post-Fase 4 (mejoras de uso diario)

- ✅ **Spotify de escritorio:** `abrirSpotify()` en `app/ai/actions.js` convierte links web a URI `spotify:tipo:id` y lanza la app de escritorio vía handler de protocolo; si no toma el foco en ~1.5 s, cae al reproductor web. Presets en `PLAYLISTS` (estudio/foco/entreno) — el usuario pega sus links.
- ✅ **TTS (PRTS responde por voz):** `PRTS_AI.say()` con `speechSynthesis` (`es-MX`), solo escritorio, sin costo/backend. Toda respuesta del ejecutor se muestra y se lee.
- ✅ **Intent `log_set`** (registrar serie de gym por voz/texto): `command.v3` + validación en `schemas.ts`. Router local resuelve "press banca 80 por 8"/"…80 kg x 8" sin LLM; el cliente matchea el ejercicio contra el catálogo `exercises`, crea la sesión del día si falta y calcula el `set_number`. Confirmación antes de insertar.
- ✅ **Inbox auto-procesado** (versión cliente del "cron"): `process-inbox` cachea la sugerencia en `inbox_entries.result.cached_suggestion` (sigue `pendiente`) y solo procesa las que aún no tienen sugerencia (`result is null`). El dashboard muestra lo cacheado al abrir (`refrescarSugerencias`) y auto-procesa lo nuevo en segundo plano (`autoInbox`); agregar una captura la auto-sugiere. Idempotente, sin re-gastar LLM al reabrir.

## Fase 5 — Wake word (escucha continua)

- ✅ **5.0 — Wake word sin dependencias** (`app/ai/wakeword.js`): `webkitSpeechRecognition` continuo como detector "suave". Palabra clave hablada **«Dalia»** (`WAKE = /dal[ií]a\w*/`; una palabra pronunciable se transcribe mucho mejor que el acrónimo «PRTS»). Internamente el comando se normaliza con prefijo "PRTS, " para el router. **Opt-in, apagada por defecto**, toggle en el panel de Captura; solo escritorio Chromium. Frase única ("Dalia, pon música") o dos pasos ("Dalia" → ventana de 6 s → comando). Enruta vía `ejecutarComando(cmd, spoken=true)`.
- ✅ **Protocolos de respuesta simple** (en `PRTS_AI.routeLocal`, sin LLM ni datos → intent local `say`): hora, fecha/día, saludo según la hora, gracias, "cómo estás", ayuda/qué puedes hacer. Respuesta hablada inmediata.
- ✅ **Intent `ask`** (`command.v4`): preguntas cotidianas / conocimiento general que no encajan en otra intención (cálculos, conversiones, traducciones, definiciones, datos) → el LLM pone la respuesta breve en `speak` y PRTS la dice. No se usa para notas/tareas (eso es create_task/unknown→captura). `ES_COMANDO` enruta interrogativos y saludos por push-to-talk (ojo: `\b` no sirve tras vocal acentuada en JS → se usa `(?=\s|$|\?)`).
- ✅ **Interacción por voz manos libres:** las escrituras dictadas (`create_task`/`log_weight`/`log_set`) se aplican **sin modal** y se confirman **hablando** (TTS `es-MX`); clima y resumen responden en voz alta. `opts.spoken` distingue voz (sin confirm) de teclado (con confirm).
- ✅ **Coordinación de un solo reconocedor:** push-to-talk pausa la escucha continua (`wakePause`/`wakeResume`); el TTS también la pausa mientras habla (anti-feedback).
- ✅ **5.0.1 — Escucha en segundo plano:** mientras la escucha está encendida, `wakeword.js` retiene un stream de micrófono (`getUserMedia({audio:true})`). Un tab que captura audio queda **exento del throttling/congelamiento** de pestañas en segundo plano de Chromium → los reinicios del reconocedor siguen disparándose con la pestaña detrás de otra ventana. Refuerzos: reinicio en `onend` (~300 ms), `watchdog` (`setInterval` 3 s re-arma si murió) y re-armado en `visibilitychange`/`resume`. El mic se libera al apagar (`wakeSet(false)`). **Límite honesto:** funciona con la pestaña ABIERTA en segundo plano; si se cierra el navegador o la laptop se suspende → companion nativo (Nivel C, fuera de alcance).
- ⚠️ **Privacidad asumida:** `webkitSpeechRecognition` envía audio a Google al transcribir; en continuo es audio ambiental constante → opt-in, off por defecto, indicador visible (y el de micrófono del navegador permanece encendido en segundo plano).
- ✅ **Lanzadores de apps/web/carpetas** (`LAUNCHERS` en `actions.js`, intents locales `launch` y `routine`): "abre Discord/Spotify/VS Code/Steam/WhatsApp" → handler de protocolo (`discord://`, `spotify:`, `vscode://`, `steam://`, `whatsapp://`) vía iframe oculto + fallback web; "abre YouTube/Helium/navegador" → pestaña web; "abre descargas/documentos/mi carpeta de proyectos" → `file://` (el navegador lo **bloquea desde http** → avisa que requiere companion nativo; rutas editables en `LAUNCHERS`). `matchLauncher` mapea sinónimos/mis-hears. "Buen día[, Dalia]" / "buenos días" → `routine` que abre Discord+Spotify+YouTube escalonados. La wake word ahora dispara también al **final** de la frase ("Buen día Dalia"), no solo al inicio.
- ⏭️ **5.1 (opcional):** detector on-device con Picovoice Porcupine (WASM, AccessKey gratis, `.ppn` custom) detrás de la misma API; al disparar abre el push-to-talk existente. Nivel C (SO, navegador cerrado) → companion nativo, fuera de alcance. Ver `docs/Fase5_WakeWord_Consideraciones.md`.

### UI/UX post-Fase 5

- ✅ **Insights como vista propia** (`#tab-insights` + link en sidebar): salió del stack derecho del dashboard; `TABS` incluye `insights` y `switchView` la carga (`cargarInsights`).
- ✅ **Botón «‹ Dashboard»** (`.back-dash`, `data-view="dashboard"`) en las vistas Semana, Proyectos, Tareas e Insights — se cablea con el mismo `querySelectorAll("[data-view]")` de `init()`.
- ✅ **Nodo PRTS animado en el mapa:** lee `PRTS_AI.attention` (capturando comando por wake word → pulso rápido + halo/anillo ámbar respirando + órbitas aceleradas) y `PRTS_AI.speaking` (TTS contestando → ondas de voz concéntricas azules expandiéndose). `attention` lo setea el `onState` de `initWake` (awaiting/trigger, con timeout de 2.5 s tras trigger); `speaking` lo setea `PRTS_AI.say()` (`utterance.onstart/onend`).
- ✅ **Voz de PRTS configurable:** selector "Voz de PRTS" + botón Probar en el panel de Captura. `PRTS_AI.getVoices()` (filtra voces `es-*` del sistema, fallback a todas), `setVoice(name)` persiste en `localStorage` (`prts_voice`); `say()` la aplica. "Automática (es-MX)" por defecto; las voces cargan async (`onvoiceschanged`).
- ✅ **Dashboard reacomodado (mockup constelación):** el `#tab-dashboard` pasó de "mapa full-width + grid 2-col" a dos filas — `.dash-top` (mapa `2.4fr` + `#rail` con Gimnasio·hoy y Progreso semanal) y `.dash-bottom` (Briefing · Captura `#panel-captura` · Tareas `#panel-tareas`). Encabezado `.dash-head` con título "PRTS" + control segmentado `#dash-seg` de 3 modos (`applyDashMode`, persiste en `localStorage` `prts_dash_mode`): **Constelación** (todo), **Mando** (sin mapa, riel en 2 col), **Diario** (sin mapa ni captura, briefing ancho). Colapsa a 1 col < 1080px.
- ✅ **Wake word renombrada a «Dalia»** (antes «Víctor»): `WAKE = /dal[ií]a\w*/` en `wakeword.js`; `routeLocal` (actions.js) y el atajo escrito del input de captura (index.html) aceptan `prts|dal[ií]a`.

### Módulo Finanzas (Fase 5 · básico con gráficas)

- ✅ Migración `..0010_finances_schema.sql`: tabla `finances` (`entry_date`, `kind` ingreso/gasto, `category` texto libre, `amount`, `note`), RLS `owner_all`, índice `(user_id, entry_date desc)`.
- ✅ `app/finanzas.html` (móvil, `styles.css` + Chart.js, mismo patrón que dieta/gym): navegador de mes, stat-cards Balance/Ingresos/Gastos, captura (toggle ingreso/gasto + chips de categoría + monto/fecha/nota), **gráficas**: dona de gastos por categoría con leyenda %, línea de balance acumulado del mes, y pestaña Tendencia con barras ingresos vs gastos + línea de balance (8 meses) y promedios/ahorro. Enlazado en sidebar y como nodo activo del mapa.

### Módulo Recordatorios (Fase 5 · notificación al celular vía Google Calendar)

- **Por qué Calendar y no Web Push:** el celular ya tiene la app de Google Calendar, que entrega la notificación a la hora con PRTS cerrado. PRTS solo crea el evento (con recordatorio "popup"); Google hace el resto. Cero backend de push.
- ✅ Migración `..0011_reminders_schema.sql`: tabla `reminders` (`title`, `notes`, `remind_at timestamptz`, `lead_minutes`, `status` pendiente/hecho/cancelado, `google_event_id`), RLS `owner_all`, índice `(user_id, remind_at)`.
- ✅ `app/ai/gcal.js` — integración **cliente puro** con Google Calendar: Google Identity Services (GIS) flujo token (access token ~1 h en memoria, re-pedido en silencio; sin refresh token, sin secretos → sin Edge Function). `PRTS_AI.gcal`: `available()` (hay `GOOGLE_CLIENT_ID`), `connected()`, `connect()`/`disconnect()`, `createEvent/updateEvent/deleteEvent` (REST sobre `calendars/primary/events`, TZ MX, `reminders.overrides` popup a `lead_minutes`). Degrada a `null` si no conectado/falla.
- ✅ `app/config.js` → `GOOGLE_CLIENT_ID` (público, vacío por defecto). **Setup del usuario en Google Cloud Console:** habilitar *Google Calendar API*; pantalla de consentimiento *Externo* + agregarse como *usuario de prueba* (sin verificación de Google); crear *ID de cliente OAuth* tipo Web con orígenes JS = URL de Vercel + `http://localhost:3210`; pegar el ID en config.js. Mientras esté vacío, los recordatorios se guardan pero NO notifican al celular.
- ✅ `app/recordatorios.html` (móvil): tarjeta Conectar/Desconectar Google con estado, captura (título + `datetime-local` + chips de antelación + nota), listas Próximos / Pasados-y-hechos con completar·editar·eliminar (sincroniza el evento GCal). Badge "● Calendar" vs "○ solo PRTS".
- ✅ **Fuente de verdad en Supabase** (PRTS posee los recordatorios; Google es la capa de notificación). Sincronización **una vía** PRTS→Google. **Degradación total:** sin Google conectado el recordatorio igual se guarda y aparece en el dashboard.
- ✅ **Voz (Dalia):** intent local `create_reminder` en `actions.js` con parser de fecha/hora en español (`parseRecordatorio`: "en N min/horas/días", hoy/mañana/pasado mañana, día de semana, "el día N", "a las H[:MM] am/pm/de la mañana/tarde/noche"; hora baja sin sufijo → PM). "Dalia, recuérdame …" inserta en `reminders` + crea evento GCal y confirma hablando.
- ✅ **Dashboard:** próximos recordatorios (48 h) y vencidos pendientes se anteponen en `#prts-alertas` (`renderRecordatoriosDash`); link en sidebar.
- ✅ **Inbox:** `aplicarSugerencia` para `recordatorio` con fecha/hora → tabla `reminders` (+ evento GCal); solo fecha → a las 9:00; sin fecha → tarea simple (como antes). `deshacerAplicacion` borra también el evento GCal.
- ⚠️ **Límite honesto:** el evento se crea con PRTS abierto; la notificación la entrega Google con PRTS cerrado. Editar en el celular no regresa a PRTS. App OAuth en modo testing (test user) basta para uso personal.

### Decisiones abiertas (resolver al implementar)

- Tarifas/modelo vigentes para `cost_usd` (verificar precios al implementar).
- API de clima y permiso de ubicación (intent `weather`).
- Playlists de estudio: presets fijos vs API de Spotify.

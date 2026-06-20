# CLAUDE.md — PRTS

Sistema personal de organización de Sylft: estudiante TecNM Celaya, instructor (Wolves robótica / LevelUp idiomas), atleta de gym. Usuario único. Idioma: **español (es-MX)** — UI, commits y documentación en español.

## Stack

- **Frontend:** HTML/JS **vanilla** (sin frameworks, sin build step). Cada módulo es un HTML autocontenido en `app/`. PWA (`manifest.json`, `sw.js`). Deploy en Vercel con root `app/`.
- **Desktop (Elfie):** app **Tauri 2** (Rust) en `elfie-desktop/` con `frontendDist: "../../app"` → carga el **mismo** `app/` (todo lo de Elfie es NO-OP en web vía `window.__TAURI__`). Sidecars Python locales en `elfie-desktop/sidecars/` (voz Whisper+Kokoro+Vosk, RAG/chat con Ollama+LanceDB, XTTS) en **venvs aislados** (`venv-voice` numpy2; `venv-xtts` torch+CUDA). **Venvs, modelos, `db/`, `voices/` y `target/` NO se versionan** (ver `.gitignore`).
- **Backend:** Supabase — Postgres con **RLS** (`owner_all`, `auth.uid() = user_id`), Auth, **Edge Functions** (Deno/TS) para la capa IA en la nube.
- **LLM (dos caminos):** **Web/nube** → Anthropic (Claude tier económico) vía Edge Functions, key solo en Supabase secrets, **nunca en el cliente**. **Desktop** → Ollama local (`qwen2.5:7b` + embeddings `bge-m3`), privado y $0; degrada a Anthropic si falla. Restricción rectora del desktop: **8 GB de VRAM compartida** (Whisper+Kokoro+Ollama+XTTS no caben todos calientes).

## Comandos

```bash
npm run dev          # npx serve app
npm run db:push      # supabase db push (aplicar migraciones)
npm run db:new       # supabase migration new <nombre>
supabase functions deploy <nombre>

# Elfie Desktop (Tauri) — dentro de elfie-desktop/
cd elfie-desktop && npm run dev    # tauri dev (compila Rust + lanza app + sidecar de voz)
cd elfie-desktop && npm run build  # tauri build (instalador Windows)
```

> Git y `supabase` los corre el usuario en PowerShell cuando hay deploy/push real.

## Estructura

```
app/                 # frontend vanilla (mismo en web y desktop)
  index.html         # dashboard radial (runa) + tareas/semana/proyectos/insights/recordatorios/levelup (SPA, ~2.5k líneas)
  gym.html dieta.html apuntes.html finanzas.html recordatorios.html elfie.html elfie-chat.html
  levelup-maestros.html levelup-alumnos.html levelup-admin.html
  config.js          # URL + anon key Supabase + GOOGLE_CLIENT_ID (público por diseño)
  styles.css         # tokens de diseño compartidos — único idioma visual
  ai/                # voice.js (push-to-talk web) wakeword.js (Dalia web) actions.js (router+ejecutor) gcal.js (Google Calendar)
  elfie/             # puentes Tauri (NO-OP en web): desktop.js rag.js chat.js elfie-config.js monitor.js routines.js
elfie-desktop/       # app Tauri 2
  src-tauri/src/     # Rust: lib.rs (tray/atajos/comandos) monitor.rs system_control.rs voice.rs
  sidecars/          # Python: voice_server.py rag.py chat.py xtts_server.py (corren en venv-voice/venv-xtts)
supabase/migrations/ # SQL versionado (timestamp YYYYMMDDNNNNNN_nombre.sql) — ..0019 = último
supabase/functions/  # Edge Functions: generate-briefing, generate-insights, process-inbox, interpret-command
                     #   + _shared/ (llm.ts, schemas.ts, prompts/*.vN.ts — command.v4 vigente)
docs/Fase4_Arquitectura_IA.md  # ARQUITECTURA DE REFERENCIA para Fase 4 — leer antes de tocar la capa IA
docs/Fase5_WakeWord_Consideraciones.md  # decisiones de wake word
PRODUCT.md / DESIGN.md         # identidad, principios de diseño, anti-referencias (⚠ paleta de DESIGN.md desactualizada)
```

## Convenciones

- **SQL:** tablas con `user_id default auth.uid()` (excepto las que escribe la Edge Function con service role → `user_id` explícito), RLS `owner_all`, TZ `America/Mexico_City`.
- **Diseño:** **fondo dark casi-negro cálido** (`--bg: #0D0C0E`), serif para títulos/cifras, mono mayúsculas para etiquetas, **un solo acento rosa** (`--accent: #E68AA2`; verde/ámbar/rojo solo como semántica de estado). Tokens en `app/styles.css` (fuente de verdad). Nada de gamificación, gradientes ni glassmorphism. Targets táctiles ≥44px. Contraste AA. `prefers-reduced-motion`. ⚠ **`DESIGN.md` aún describe la paleta vieja (navy/azul acero `#8FAEDC`) — está desactualizado; el CSS manda.**
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
- ✅ **Runa central con auras de voz:** el núcleo del dashboard es la **runa** (`app/runa.png`, blanca sobre el campo oscuro) en `#prts-core .core-stage`; respira en idle (`@keyframes rune-breathe`). Las auras de estado viven en **CSS** (`#prts-core.escuchando` → anillos ámbar `ring-listen`; `#prts-core.hablando` → anillos rosa `ring-speak`, con `@keyframes ring-ripple` y stagger por `.d1/.d2`); `drawMap` solo **sincroniza** las clases leyendo `PRTS_AI.attention`/`PRTS_AI.speaking` cada frame. `attention` lo setea el `onState` de `initWake` (awaiting/trigger, timeout 2.5 s); `speaking` lo setea `PRTS_AI.say()` (`utterance.onstart/onend`). El lienzo `#map` quedó como **campo de constelación de fondo** (estrellas + líneas del núcleo a las anclas de cada panel + partículas); ya no dibuja los nodos abstractos ni navega (la navegación es por sidebar y enlaces de cada tarjeta).
- ✅ **Voz de PRTS configurable:** selector "Voz de PRTS" + botón Probar en el panel de Captura. `PRTS_AI.getVoices()` (filtra voces `es-*` del sistema, fallback a todas), `setVoice(name)` persiste en `localStorage` (`prts_voice`); `say()` la aplica. "Automática (es-MX)" por defecto; las voces cargan async (`onvoiceschanged`).
- ✅ **Dashboard radial (runa al centro):** el `#tab-dashboard` usa un único grid `.constelacion` con la runa (`#prts-core`) en la columna central (`grid-area: runa`, abarca 2 filas) y los paneles **en órbita** — Gimnasio·hoy (`.c-gym`) y Tareas (`.c-tareas`) a la izquierda, Progreso (`.c-prog`) y Briefing (`.c-brief`) a la derecha, Captura (`#panel-captura`) a lo ancho abajo. `grid-template-columns: 1fr minmax(210px,0.8fr) 1fr` con `min-width:0` implícito → columnas laterales simétricas y runa centrada. Encabezado `.dash-head` con título "PRTS" + control segmentado `#dash-seg` de 3 modos (`applyDashMode`, persiste en `localStorage` `prts_dash_mode`): **Constelación** (runa + campo + paneles), **Mando** (sin runa/campo, paneles en rejilla de 3 col), **Diario** (1 col, briefing ancho, sin captura). Colapsa a 1 col (runa arriba, campo `#map` oculto) < 1024px.
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

### Apartado LevelUp (Fase 5 · mini-CRM/ERP de la academia de idiomas)

- ✅ Migración `..0012_levelup_schema.sql`: `levelup_teachers` (idiomas `text[]`, formatos, `pay_type` mensual/por_hora + `pay_rate`, notas), `levelup_students` (idioma, nivel, horas/sem, `teacher_id`, `monthly_fee`, status), `levelup_classes` (kind `recurrente`/`sesion`, weekday|class_date, start_time, duration_min, `week_block_id`, `google_event_id`), `levelup_class_students` (roster grupal), `levelup_payments` (mensual: period, amount_due, amount_paid, paid_at, unique por user+student+period). RLS `owner_all`.
- ✅ **3 páginas móviles** (patrón `finanzas.html`), grupo "LevelUp" en sidebar + navbar compartida:
  - `app/levelup-maestros.html`: CRUD maestros; tarjeta expandible con sus clases y alumnos; alta de clase (recurrente [día+hora+duración] o sesión [fecha]) con roster. Clase recurrente → inserta `week_blocks` (rol `levelup`) **y** evento recurrente en GCal; sesión → solo evento GCal. Eliminar clase borra bloque + evento.
  - `app/levelup-alumnos.html`: CRUD alumnos **agrupados/filtrables por maestro**; navegador de mes; pago mensual por alumno (registrar monto/fecha vía upsert en `levelup_payments`, muestra estado pagado/parcial/pendiente + faltante + historial).
  - `app/levelup-admin.html`: resumen del mes (ingresos cobrados vs esperado, sueldos, neto, alumnos, clases, horas/sem), desglose por maestro (sueldo = mensual o `pay_rate × horas × 4.33`), gráficas Chart.js (ingresos vs sueldos por maestro, dona estado de pagos) y lista de pagos pendientes.
- ✅ Migración `..0013_levelup_expenses.sql`: tabla `levelup_expenses` (`entry_date`, categoría, monto, nota) para **gastos de operación** de la academia (clases muestra, marketing, materiales, renta…), separados de los sueldos. El neto del admin = ingresos − sueldos − gastos. RLS `owner_all`; migración independiente de la ..0012.
- ✅ **Decisiones:** clases recurrentes **y** sesiones sueltas; cobro **mensual por alumno**; finanzas **self-contained** (NO tocan el módulo Finanzas personal); **varios maestros**.
- ✅ `gcal.js` extendido: `createClass`/`updateClass` (evento con duración real; `RRULE:FREQ=WEEKLY` si recurrente, inicio = próxima ocurrencia del weekday). Mapa: nodo `alumnos` enlaza a `levelup-alumnos.html`.
- ⚠️ **Límite honesto:** Semana es plantilla recurrente, así que solo las clases **recurrentes** entran a `week_blocks`; las sesiones sueltas van a GCal + lista (no al grid de Semana). Sin Google conectado, las clases se guardan y Semana funciona igual.
- ⏭️ **Futuro:** voz/Dalia para LevelUp ("registra pago de X"), recordatorios de cobro día 1/15, asistencia y progreso de nivel.

## Fase 6 — Elfie Desktop (plan en `docs/Elfie_PRTS_Desktop_Planificacion_v2.0.pdf`)

> El Elfie Desktop es la app Tauri en `elfie-desktop/` (`frontendDist: "../../app"` → carga el mismo `app/`). Fases F0–F5 ya estaban (tray, shortcuts, control SO, voz local Whisper+Kokoro+Vosk, router Ollama, personalidad, Routine Engine). Migraciones Elfie: `..0014_elfie_config` … `..0018_routines`.

### ✅ 6.1 — RAG local de Apuntes (búsqueda semántica)

- **Por qué:** el módulo Apuntes (tabla `notes`: subject, topic, key_concepts, formulas, doubts, connections, summary) solo se buscaba por texto. RAG permite *"Elfie, ¿qué anotamos sobre X?"* sin las palabras exactas. **Privacidad total:** las notas nunca salen de la máquina.
- **`elfie-desktop/sidecars/rag.py`** (nuevo): embeddings vía Ollama + vector store **LanceDB** en `elfie-desktop/db/apuntes.lance`. Modelo de embeddings **`bge-m3`** (multilingüe; rankea español mucho mejor que `nomic-embed-text`, que quedó descartado por pobre en es-MX). Distancia **coseno** (los vectores no están normalizados → L2 rankeaba por magnitud). Respuesta generada por `qwen2.5:7b` (env `ELFIE_LLM_MODEL`) fundamentada SOLO en los apuntes recuperados; si el LLM falla, devuelve los apuntes crudos. Carga perezosa: si falta LanceDB/Ollama, degrada con `{ok:false}` sin tumbar el sidecar. Envs: `ELFIE_EMBED_MODEL`, `ELFIE_RAG_DB`, `ELFIE_OLLAMA`.
- **`voice_server.py`**: 6 endpoints — `GET /rag/status`; `POST /rag/index` `/rag/index_batch` `/rag/query` `/rag/answer` `/rag/delete`.
- **`app/elfie/rag.js`** (nuevo): puente `window.elfieRag` (`available/status/index/del/reindex/query/answer`). **NO-OP en web** (sin `__TAURI__` → null), igual que `desktop.js`.
- **`apuntes.html`**: indexa al guardar (`guardar()` → `elfieRag.index`) y al borrar (`elfieRag.del`, ambas rutas). Panel **"Pregúntale a Elfie"** (`#rag-panel`, solo desktop): búsqueda semántica con respuesta + fuentes clicables (abren la nota) + botón **"Reindexar apuntes"** (backfill `index_batch` con `todasNotas`). El usuario debe reindexar una vez para poblar el índice con sus notas existentes.
- **`actions.js`**: intent local `note_query` en `routeLocal` ("qué anotamos/anoté sobre X", "busca en mis apuntes X") → ejecutor llama `elfieRag.answer` y responde **hablando** (Kokoro). En web avisa que es función de escritorio.
- ⚠️ **Cambio de modelo de embeddings rompe el índice** (bge-m3=1024-dim vs nomic=768): si se cambia, borrar `elfie-desktop/db/` y reindexar.

### ✅ 6.2 — XTTS v2 (voz clonada de Elfie)

- **Por qué venv aislado:** XTTS necesita **PyTorch**, pero el stack de voz (faster-whisper/CTranslate2 + kokoro-onnx) usa **numpy 2**; coqui-tts arrastra deps que lo degradarían. Solución: **`elfie-desktop/venv-xtts/`** separado (torch `2.11+cu128` para Blackwell sm_120 — **verificado: CUDA OK en la RTX 5060** — + `coqui-tts`). NO toca `venv-voice`.
- **`elfie-desktop/sidecars/xtts_server.py`** (nuevo): microservicio HTTP en **:7332** (venv-xtts). `GET /health`, `POST /synth {text, speaker_wav, language, speed}` → escribe WAV en temp y lo devuelve. Modelo `xtts_v2` carga perezoso (~1.8 GB en GPU). `COQUI_TOS_AGREED=1` (licencia **CPML, no comercial** — uso personal).
- **`voice_server.py`** (venv-voice): lanza `xtts_server` **perezosamente** (`ensure_xtts` → subprocess con el python de venv-xtts) al primer uso. `speak_dispatch` elige motor: `xtts` (si hay `speaker_wav`) con **fallback a Kokoro** si falla. `_play()` centraliza la reproducción + anti-feedback. Endpoints nuevos: `POST /voice/record {seconds,name}` (graba referencia del mic → `elfie-desktop/voices/<name>.wav`), `GET /voice/xtts/health` (proxy). `/tts` ahora acepta `engine` + `speaker_wav`.
- **Frontend:** `elfie-config.js` → `voiceEngine: kokoro|navegador|xtts` + `xttsVoiceName`/`xttsSpeakerWav` (ruta LOCAL → solo localStorage, no Supabase). `desktop.js` → `say()` manda `engine:"xtts"` + `speaker_wav` cuando el motor es xtts. `elfie.html` → botón XTTS en el selector + tarjeta **"Voz clonada · XTTS"**: graba 8 s, crea perfil en `voice_profiles` (Supabase, metadata) + activa, lista perfiles (usar/eliminar), prueba inmediata.
- **Flujo:** el usuario graba ~8 s de la voz objetivo (la suya o un clip ante el mic) → se guarda local + activa → `say()` la usa. **Verificado:** cold-start ~95 s (carga modelo), **warm ~6 s**, VRAM ~2.4 GB (total 6.4/8 GB con Whisper+Kokoro+Ollama; cabe). XTTS se descarga al detener el servicio (estado perezoso por defecto → Kokoro).
- **Stack de deps (no obvio, costó resolverlo):** `venv-xtts` con **torch 2.11.0+cu128** (Blackwell sm_120) + **coqui-tts 0.26.2** (NO la 0.27.x: exige `torchcodec`+FFmpeg) + **transformers 4.51.3** (la 0.26.2 la fija; >4.57/5.x rompe por `isin_mps_friendly`/`is_torchcodec_available`). `torchaudio 2.11` solo carga audio vía torchcodec → **shim en `xtts_server.load()`: `torchaudio.load = soundfile`** (libsndfile, sin FFmpeg). `load()` con `_load_lock` (precarga + 1er synth no cargan dos veces → era la causa de timeouts).
- ⏭️ **Pendiente F6:** —  **Obsidian: descartado** (Sylft no lo usa). **Fase 6 completa.**

## Fase 7 — Módulo Utilidades

> Tres frentes: **chat con memoria** (7.1), **generación de imágenes anime** (7.2) y **extras** (visión de pantalla, avatar de Dalia, briefing hablado…). Restricción rectora: la **VRAM de 8 GB compartida** (Whisper+Kokoro+Ollama+XTTS no caben todos calientes). 7.2 exigirá un orquestador de GPU que descargue Ollama antes de generar imagen — **aún no implementado**.

### ✅ 7.1 — Chat conversacional con Elfie (memoria + personalidad + TTS)

- **Por qué:** hasta ahora Elfie solo hacía comandos de un disparo (intents) y Q&A de apuntes (RAG). Faltaba conversación multi-turno con memoria y personalidad.
- **`elfie-desktop/sidecars/chat.py`** (nuevo): chat sobre Ollama **`/api/chat`** (qwen2.5:7b, no-streaming, `keep_alive 10m`). Personalidad inyectada en el system prompt vía `tone` (reusa `ElfieConfig`). **Memoria de 2 capas:** (a) corto plazo = historial de turnos que manda el cliente (últimos `MAX_TURNS=10`); (b) largo plazo = hechos durables embebidos con **bge-m3** en LanceDB (tabla **`memoria`**, MISMA DB que el RAG de apuntes, `elfie-desktop/db/`), recuperados por coseno (`recall`, score ≥0.45) e inyectados al prompt como `RECUERDOS`. Reutiliza `rag._embed` y `rag.DB_DIR`. Funciones: `reply`, `remember`, `recall`, `forget`, `mem_list`, `status`. Degrada con `{ok:false}` si Ollama/LanceDB fallan.
- **`voice_server.py`**: `import chat` + endpoints `GET /chat/status` `/chat/memories`; `POST /chat/send` `/chat/remember` `/chat/recall` `/chat/forget`.
- **`app/elfie/chat.js`** (nuevo): puente `window.elfieChat` (`available/status/send/remember/memories/forget/speak/stopSpeak`). **NO-OP en web** (sin `__TAURI__`). Centraliza el **TTS frase-a-frase** del chat leyendo `ElfieConfig` (Kokoro/XTTS), sin depender de `desktop.js`.
- **`app/elfie-chat.html`** (nuevo, móvil+desktop): página de chat autónoma (login propio, burbujas tú/Elfie, selector de personalidad, toggle Voz, **push-to-talk 🎤** vía `/stt`, botón Nueva, panel **Memoria** con olvidar). Persiste la conversación en Supabase (`elfie_chat_sessions`/`elfie_chat_messages`); al abrir recupera la última sesión. En web avisa que el chat conversacional es del escritorio (escribe pero Elfie no responde sin Ollama).
- **Migración `..0019_elfie_chat.sql`:** `elfie_chat_sessions` + `elfie_chat_messages` (role user/assistant), RLS `owner_all`. La memoria de largo plazo NO está en Supabase (vive on-device en LanceDB).
- **Voz/navegación:** intent local `navigate→chat` en `actions.js` ("Dalia, hablemos / charlemos / abre el chat"); `PAGINAS.chat = elfie-chat.html`. Enlace "Chat con Elfie" en el sidebar de `index.html` y en el navbar de la página.
- **Verificado:** sintaxis de sidecars OK (`py_compile`); página carga en web sin errores de consola, login visible, `elfieChat.available()=false` correcto, personalidades cargadas. La respuesta del LLM se prueba en el Elfie de escritorio con Ollama.

### ✅ Wake word «Dalia» también en el detector NATIVO

- Antes la wake word web (`wakeword.js`) usaba «Dalia» pero el detector **nativo** (Vosk, `voice_server.py`) solo disparaba con «Elfie». Ahora `WAKE_RE` y `_WAKE_STRIP` aceptan ambas + mis-hears de Vosk en es (`dalia/dalía/talía/valía/daría`). Reiniciar el sidecar para que tome el cambio.

### ✅ Wake word ON-DEVICE real (Picovoice Porcupine)

- **Por qué:** Vosk es STT general usado como detector "suave" → más falsos positivos y más CPU. **Porcupine** es un detector dedicado: 100% on-device, muy preciso, bajísimo CPU. Cumple la Fase 5.1 del plan.
- **`voice_server.py`:** `load_porcupine()` + `wake_loop_porcupine()` + dispatcher `wake_loop()` (Porcupine si está configurado; si no, `wake_loop_vosk()` — **degradación total**). `pvporcupine` instalado en `venv-voice`. Tras detectar, captura el comando en un stream propio y lo transcribe con Whisper (igual que Vosk). `/health` reporta `wake_engine: porcupine|vosk`.
- **Setup del usuario (una vez):** en `console.picovoice.ai` (gratis) → obtener **AccessKey** + crear wake word personalizada **«Dalia»** (plataforma Windows) → descargar el `.ppn`. Colocar: `.ppn` en `elfie-desktop/models/porcupine/dalia.ppn` y la key en `elfie-desktop/models/porcupine/accesskey.txt` (o env `ELFIE_PICOVOICE_KEY`). Para una «Dalia» en español, descargar también `porcupine_params_es.pv` y apuntar `ELFIE_PORCUPINE_MODEL`. Envs: `ELFIE_PORCUPINE_PPN`, `ELFIE_PORCUPINE_SENS` (def 0.6).
- ⚠️ `models/` está en `.gitignore` → el `.ppn` y la key se quedan locales (no se versionan). Mientras no exista key+`.ppn`, sigue usando Vosk.

### ✅ Spotify Web API (control real de reproducción)

- **Por qué:** antes solo se abrían deep links (`abrirSpotify`). Ahora control real por voz: buscar+reproducir, pausar, saltar, volumen. **Funciona en web y escritorio** (la Web API no es solo de escritorio).
- **`app/ai/spotify.js`** (nuevo): OAuth **Authorization Code + PKCE** (sin secreto → seguro en cliente). Refresh token en `localStorage`, access token (~1 h) en memoria con renovado automático. Flujo por **popup** → `app/spotify-callback.html` (postMessage del `code` a la ventana padre). `PRTS_AI.spotify`: `available/connected/connect/disconnect`, `play/pause/resume/next/previous/volume/nudgeVolume/current/state`, `searchAndPlay(q,type)`, `playUri`. Errores tipados: `no_device` (sin dispositivo activo → el llamador abre la app), `premium` (requiere Premium), `auth`, `not_found`.
- **`app/config.js`** → `SPOTIFY_CLIENT_ID` (público por PKCE, vacío por defecto). **Setup del usuario:** developer.spotify.com → Create app → copiar Client ID; en *Redirect URIs* agregar `<URL Vercel>/spotify-callback.html` y `http://localhost:3210/spotify-callback.html`.
- **Voz (`actions.js`):** intents locales `spotify_ctl` (pause/resume/next/previous/vol_up/vol_down) y `spotify_play` (buscar+reproducir). Router: "pon/reproduce <X>", "pausa", "siguiente canción", "sube/baja el volumen", etc. Los presets ("pon música de estudio/foco/entreno") siguen como `open` deep link.
- **UI:** tarjeta **Spotify** en `elfie.html` (Conectar/Desconectar + estado). `spotify.js` cargado en `index.html` y `elfie.html`.
- **Degradación:** sin `SPOTIFY_CLIENT_ID` o sin conectar → `available()/connected()` false y se avisa; los presets siguen abriendo por deep link. ⚠ Reproducir requiere **Premium + dispositivo activo**; sin dispositivo, abre la app de Spotify y se reintenta.

### ⏭️ Pendiente Fase 7

- **7.2 — Imágenes anime:** sidecar `image_server.py` (:7333, reusar `venv-xtts` + diffusers) con **Illustrious XL** (un checkpoint = un estilo; ~6-7 GB @1024² → cabe en 8 GB) + few-step (Hyper-SD/Lightning). Requiere **orquestador de GPU** (Fase 8.2, descargar Ollama antes de generar). Migración `..0022_elfie_images.sql` + `app/elfie-galeria.html` + intent `generate_image`.
- **7.3 — Extras sugeridos:** visión de pantalla (qwen2-vl/llava sobre `elfieSys.screenshot`), avatar anime de Dalia (sinergia con 7.2), briefing hablado matutino, diario por voz, RAG de PDFs.

## Fase 8 — Elfie Core, Orquestador y Lore

> Plan completo en `docs/Fase8_Elfie_Core_Plan.md`. Origen: `PRTS.docx`. Unifica los knobs sueltos de Elfie bajo un estado central con modos, un árbitro de recursos para los 8 GB de VRAM, y formaliza la identidad/personalidad.

### ✅ 8.3b — Perfil de personalidad estructurado

- **Por qué:** la personalidad era un solo string de tono. Ahora es un perfil por **ejes** que compone el tono efectivo que ya fluye al chat (`chat.py`) y al router por la tubería `ElfieConfig.tone()`.
- **`app/elfie/elfie-config.js`:** nuevos campos `iniciativa` (baja/media/alta), `detalle` (breve/normal/extenso), `confirmaciones` (estrictas/normales/mínimas), `personaDesc` (arquetipo libre). `tone()` compone: arquetipo (texto libre o preset) + frases por eje. Constantes `EJE_*`.
- **`app/elfie.html`:** tarjeta Personalidad ampliada con 3 controles segmentados + textarea de arquetipo + **vista previa del tono** en vivo (`renderTone`). Sin cambios en el sidecar (el tono compuesto viaja por el canal existente).
- **Migración `..0020_elfie_persona.sql`:** columna `persona jsonb` en `elfie_config` (sync best-effort; la feature funciona con localStorage).
- **Pendiente decisión:** "¿personalidad basada en un personaje?" → arquetipo propio (evitar copyright). El campo `personaDesc` ya permite definirlo libre.

### ✅ 8.1 — Elfie Core (estado + modos)

- **`app/elfie/elfie-config.js`:** `mode` (bajos/normal/conversacion) + flags `sttContinuous`, `memoryActive`. `MODES` (preset por modo) y `applyMode(name)` reconfiguran wake/voz/intérprete/modelo/memoria de golpe y persisten.
- **`app/elfie.html`:** tarjeta **Elfie Core** con selector de modo (segmentado) + descripción y **panel de semáforos** (`renderCore`): Supabase, STT·Whisper, Wake word (engine), IA local (ping a Ollama), TTS, Spotify, Calendar, y VRAM/CPU (vía `get_metrics` en escritorio). Fuentes: `/health`, puentes del cliente, Tauri invoke. En web los de sidecar muestran "escritorio".
- **`app/elfie/routines.js`:** acción **`set_mode`** (alias `modo:`) → las rutinas pueden cambiar de modo (p. ej. "modo juego → bajos recursos").
- **`app/elfie-chat.html`:** la extracción automática de memoria se **gatea con `memoryActive`** (off en modo bajos recursos).
- **Decisión tomada:** el modo solo tiene efecto pleno en escritorio (en web no hay sidecar → los modelos locales no aplican). Modos en **localStorage** (no se añadió columna a Supabase para no romper el sync hasta `db:push`).
- ⚠️ `sttContinuous` queda **plumbed pero sin comportamiento aún** (la escucha semi-continua real es un follow-up; hoy el modo conversación lo marca pero la voz sigue por wake word/push-to-talk).

### ✅ 8.2 — Orquestador de recursos

- **Reparto:** el **mecanismo de GPU** vive en el sidecar; la **política** (cuándo bajar de modo) en el frontend (que ya recibe métricas de `monitor.rs`).
- **`elfie-desktop/sidecars/orchestrator.py`** (nuevo): semáforo de "dueño pesado" (`claim`/`release`), `unload_ollama()` (`ollama stop` → fallback keep_alive=0), `free_for(owner)` (descarga Ollama si la VRAM libre < umbral; **clave para 7.2 imágenes**), `gpu_vram()` vía nvidia-smi (sin deps). Nota: qwen+XTTS **sí coexisten** (~6.4/8 GB) → XTTS NO descarga Ollama; descargar se reserva para imágenes.
- **`voice_server.py`:** `import orchestrator` + `GET /orchestrator/status`, `POST /orchestrator/claim|release|unload_ollama`. `ensure_xtts()` registra a XTTS como dueño (sin descargar Ollama).
- **Rust:** comando `foreground_app()` (`system_control.rs`, feature `Win32_UI_WindowsAndMessaging` + sysinfo) → nombre del proceso en primer plano. Registrado en `lib.rs`.
- **`app/elfie/desktop.js`:** `resourceGuard` sobre el evento `elfie:metrics` → si VRAM/CPU ≥90% sostenido (2 ticks) o hay juego/IDE en primer plano (`HEAVY_APPS`, throttle ~15 s) → `applyMode("bajos")` + `setWake(false)` + notifica; al despejarse (4 ticks) restaura el modo previo. Toggle **Auto-recursos** en Elfie Core (`features.autoResources`, default on). `elfieSys.foregroundApp`.
- ⚠️ La regla "pausar Ollama al generar imagen" queda lista (`free_for`/`claim`) pero su consumidor real es la Fase 7.2 (aún no existe).

### ✅ 8.3a — Archivo interno / Lore (`PRTS-NNN`)

- **Migración `..0021_lore.sql`:** tabla `lore_entries` (`code` PRTS-NNN único por usuario, `title`, `body`, `kind` sistema/elfie/diario), RLS `owner_all`.
- **`app/lore.html`** (nuevo, patrón apuntes): lista + buscador + editor con código autoincremental (`nextCode` → PRTS-001…), tipos, y botón **sembrar entradas base** (PRTS-001 sistema, 002 elfie, 003 perfil de personalidad, del documento). Enlace en sidebar + navbar.
- **Sinergia IA:** al guardar (o sembrar) en escritorio, la entrada se indexa en la memoria de Elfie (`elfieChat.remember(..., "lore")`, LanceDB) → Elfie **conoce su propio lore** y lo recupera en el chat.
- **Voz/navegación:** intent local `navigate→lore` ("abre el lore/codex/archivo/diario"); `PAGINAS.lore`.

> **Fase 8 completa** (8.1 Core + 8.2 Orquestador + 8.3a Lore + 8.3b Personalidad). Decisión abierta heredada: arquetipo/identidad de Elfie ("¿basada en un personaje?") — el campo `personaDesc` y la entrada PRTS-003 lo dejan listo para definir.

## Fase 9 — Mascota Virtual de Elfie (plan en `docs/Fase9_Mascota_Elfie_Plan.md`)

> Ventana **flotante** sobre el escritorio: un avatar que **alterna archivos según su estado**, habla con voz ligera, muestra burbuja de texto y ejecuta acciones/protocolos. **Cerebro en la nube (Anthropic) por defecto** → GPU casi libre; lo local queda como respaldo (degradación total). Restricción rectora heredada: la VRAM de 8 GB.

### ✅ 9.0 — Ventana flotante + estados base

- **`app/pet.html`** (nuevo): la mascota. Avatar + burbuja + tarjeta de confirmación + historial + acciones rápidas. **3 tamaños** (mini = solo avatar · normal = avatar+texto · panel = +historial+acciones). Ventana Tauri **transparent + always-on-top + sin decoración**, arrastrable (`data-tauri-drag-region`).
- **`app/pet/avatar.js`** (nuevo): máquina de estados `window.Avatar` (web-safe: corre como demo sin Tauri). `setState` **alterna el archivo del avatar por estado**; parpadeo idle, burbuja, confirmación, tamaños. Conducida por **eventos app-wide** del cerebro.
- **`app/pet/assets/*.svg`** (nuevos): placeholders on-brand rosa/gris. 5 estados base (neutral/listening/thinking/speaking/error) + boca (`speaking-closed`) + 6 contextuales (study/gym/finance/diet/levelup/music).
- **`elfie-desktop/src-tauri/src/lib.rs`:** ventana `pet` (creada oculta al arranque para recibir eventos); comandos `pet_toggle/show/hide/set_size/click_through`; **atajo global Ctrl+Shift+E**; ítem de tray "Mascota Elfie".
- **`app/elfie/desktop.js`:** `elfieSys.pet*` (toggle/show/hide/setSize/clickThrough/**context**); emite `elfie:say`/`elfie:speaking`/`elfie:listening` para conducir el avatar; escucha `pet:action` (acciones rápidas: captura, chat, voz→wake, dashboard).
- **`app/elfie.html`:** botón **"Mostrar mascota"** en Elfie Core (deshabilitado en web).

### ✅ 9.1 — Cerebro nube + voz ligera (Piper)

- **Modo `mascota`** en `elfie-config.js` (`MODES.mascota`): interpreter=anthropic, voz=piper, memoria on → GPU casi libre. Botón de modo + motor "Piper" en `elfie.html`.
- **Piper** en `voice_server.py` (`load_piper`/`speak_piper`, carga perezosa CPU, ~0 GPU): tier de **voz rápida** para confirmaciones; `engine:"piper"` en `speak_dispatch` con **fallback a Kokoro**; `/health` reporta `piper`. **Setup usuario:** `pip install piper-tts` en `venv-voice` + modelo es_MX `.onnx` en `models/piper/` (o env `ELFIE_PIPER_MODEL`). Sin modelo → degrada a Kokoro.
- **Burbuja + confirmación:** tarjeta junto al avatar; confirmar/cancelar **por voz** (`Avatar.voiceConfirm` / evento `elfie:voice-confirm`) — API lista; conectar al router real (`actions.js`) queda para 9.3.

### ✅ 9.2 — Vida visual

- **Boca animada (lip-sync simple):** al hablar, alterna 2 sprites (`speaking`/`speaking-closed`) cada 150 ms — ilusión de habla sin analizar audio ni GPU.
- **Idle:** respiración sutil en `.avatar-wrap` (CSS `pet-breathe`) + parpadeo en estados de reposo (`prefers-reduced-motion` respetado).
- **Estados contextuales por módulo (pose de reposo):** `restState` + `Avatar.setContext(ctx)` + evento `elfie:context` + helper `elfieSys.petContext()`. 6 contextos con glifo. ⚠️ El **disparo automático** por módulo desde páginas separadas queda pendiente (solo `index.html` carga el bridge) → hoy se fija vía API/evento.
- **WebP-ready:** `assetUrl()` arma la ruta con la extensión activa; `Avatar.setExt("webp")` cambia de SVG a WebP cuando exista arte animado (sin tocar la lógica).

> **Pendiente Fase 9:** 9.3 (miniacciones clic-derecho + protocolos sobre `routines.js` con narración/bitácora) · 9.4 (anclajes, opacidad, click-through, auto-ocultar, tono por estado). **Arte real del avatar** (anime, coherente con PRTS-002) reemplaza los placeholders SVG. **A probar en escritorio** (recompilar Tauri): ventana `pet`, atajo, tray, comandos y voz Piper real.

### Decisiones abiertas (resolver al implementar)

- Tarifas/modelo vigentes para `cost_usd` (verificar precios al implementar).
- API de clima y permiso de ubicación (intent `weather`).
- Playlists de estudio: presets fijos vs API de Spotify.

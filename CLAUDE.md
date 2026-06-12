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

### Decisiones abiertas (resolver al implementar)

- Tarifas/modelo vigentes para `cost_usd` (verificar precios al implementar).
- API de clima y permiso de ubicación (intent `weather`).
- Playlists de estudio: presets fijos vs API de Spotify.

# Fase 8 — Elfie Core, Orquestador de recursos y Lore

> Plan de desarrollo. Creado: **2026-06-19**. Origen: `PRTS.docx` (sección "Siguiente adición").
> Fuente de verdad técnica: `CLAUDE.md`.

**Hilo conductor:** hoy la configuración de Elfie está dispersa en knobs sueltos
(`ElfieConfig.features.wake`, `voiceEngine`, `interpreter`, `localModel`). Esta fase
los unifica bajo un **estado central con 3 modos**, le da un **árbitro de recursos**
para los 8 GB de VRAM, y formaliza la **identidad/personalidad** de Elfie.

---

## 8.1 — Elfie Core (panel de estado + modos)

**Objetivo:** vista única con el estado vivo de cada subsistema + 3 modos de operación.

**Fuentes que ya existen:**

| Indicador | De dónde sale |
|---|---|
| IA local activa | ping a Ollama / `voice_server /health` (`model`) |
| Wake word | `ElfieConfig.features.wake` / `elfieWake.enabled` + `/health.wake_engine` |
| Whisper/STT | `/health.whisper` |
| TTS | `ElfieConfig.voiceEngine` (kokoro/xtts/navegador) |
| Spotify | `PRTS_AI.spotify.connected()` |
| Google Calendar | `PRTS_AI.gcal.connected()` |
| Supabase | sesión `sb.auth` |
| GPU/VRAM/CPU/RAM | `monitor.rs get_metrics` (evento `elfie:metrics`) |

**Entregables:**
- `GET /status` en `voice_server.py` (agrega whisper, wake_engine, TTS, Ollama, VRAM, modo).
- Vista "Elfie Core" en `elfie.html` (o `index.html?elfie=core`): semáforos por subsistema.
- 3 modos como presets sobre los knobs existentes:

| Modo | wake | voiceEngine | interpreter | STT | memoria | LLM |
|---|---|---|---|---|---|---|
| **Bajos recursos** | off | navegador/off | solo protocolos | atajo manual | off | sin modelo pesado |
| **Normal** | Elfie/Dalia on | Kokoro | local (Ollama) | push-to-talk | corto plazo | qwen local |
| **Conversación** | on | XTTS/natural | local + fallback Anthropic | semi-continuo | activa | qwen / API si VRAM baja |

- `ElfieConfig.mode` + `applyMode(name)` (setea wake, voiceEngine, interpreter, `sttContinuous`, `memoryActive`; llama `/config`).
- Integración con Rutinas (`routines.js`): acción `set_mode`.
- Migración `..0020` (campos `mode` y flags en `elfie_config`).

**Decisión abierta:** ¿modo global o web vs escritorio? (propuesta: solo escritorio; web = "bajos recursos").

## 8.2 — Orquestador de recursos (árbitro de GPU/VRAM)

**Objetivo:** reglas simples que eviten saturar los 8 GB y degraden con elegancia. Vive en el sidecar.

**Entregables:**
- `orchestrator.py` (o sección en `voice_server.py`) con **semáforo de GPU** (un dueño pesado a la vez) + lectura de métricas.
- Reglas v1:
  1. Generar imagen → `ollama stop` antes; recargar al terminar.
  2. XTTS activo → bloquear otra carga pesada (mutex).
  3. CPU/RAM/GPU altas → degradar a modo bajos recursos (avisa).
  4. App en primer plano = juego/IDE → reducir procesos (comando Rust `foreground_app()`).
  5. VRAM insuficiente → `interpreter=anthropic` + voz del sistema.
- Estado del árbitro expuesto en `/status`.

**Dependencias:** la regla 1 es prerrequisito de la Fase 7.2 (imágenes). La regla 4 necesita comando Rust nuevo.

## 8.3 — Archivo/Lore interno + perfil de personalidad

**8.3a — Codex/Lore (`PRTS-NNN`):**
- Migración `..0021_lore.sql`: `lore_entries` (`code`, `title`, `body` md, `kind`, `created_at`), RLS `owner_all`.
- Página `app/lore.html` (patrón apuntes): lista + editor, código autoincremental.
- Sinergia IA: indexar en RAG/memoria (bge-m3) → Elfie conoce su propio lore.

**8.3b — Perfil de personalidad estructurado (PRTS-003):**
- Extender `ElfieConfig` con ejes: `tono`, `iniciativa`, `detalle`, `confirmaciones`, `persona` (texto), (voz = `voiceEngine`).
- Constructor de prompt: `tone()` compone los ejes → fluye al chat (`chat.py`) y al router por la tubería existente.
- UI: rehacer la tarjeta "Personalidad" en `elfie.html` con selectores por eje + vista previa.
- "¿Personalidad basada en un personaje?" → decisión de identidad (propio, evitar copyright).

---

## Orden propuesto

1. **8.3b Perfil de personalidad** (bajo esfuerzo, alto valor; mejora el chat ya existente).
2. **8.1 Elfie Core + modos** (medio; unifica todo y da el tablero).
3. **8.2 Orquestador** (medio-alto; desbloquea 7.2 imágenes).
4. **8.3a Lore/Codex** (bajo-medio; contenido + sinergia RAG).

**Constante:** los 8 GB de VRAM mandan; 8.2 hace viable imágenes + voz + LLM sin chocar.

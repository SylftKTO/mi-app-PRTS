# Fase 9 — Mascota Virtual de Elfie (plan)

> Subproyecto: una **ventana flotante** sobre el escritorio que es la cara de Elfie.
> Un avatar que **alterna archivos según su estado**, habla con voz ligera, muestra
> una burbuja de texto y ejecuta protocolos/miniacciones. **El cerebro vive en la
> nube (Anthropic) por defecto** para dejar la GPU casi libre; lo local queda como
> respaldo (degradación total — principio no negociable de la Fase 4).

## 0. Idea rectora y principio de GPU/costo

La mascota es una segunda interfaz, no solo decorativa: interpreta, responde, confirma
y ejecuta. Para cumplir el objetivo de **bajar la carga de GPU**, el modo "mascota"
mueve el razonamiento a Anthropic y apaga Ollama.

| Componente | Desktop actual | Mascota (Fase 9) | Efecto GPU |
|---|---|---|---|
| Interpretación de comandos | Ollama `qwen2.5:7b` local | **Anthropic** (`interpret-command`) | libera ~5 GB VRAM |
| Chat / conversación | Ollama local | **Anthropic** (Haiku) | libera GPU |
| TTS | Kokoro / XTTS | **Piper (corto) / Kokoro (largo)** — CPU | ~0 GPU |
| STT | Whisper local | Whisper local **o** Web Speech | opcional |

→ En modo mascota la GPU queda esencialmente ociosa. Lo local sigue como **fallback
offline**: si no hay red o se supera el tope mensual de `ai_settings`, degrada a Ollama
y a respuestas deterministas (igual que el dashboard cae a `frasesBriefing()`).

## 1. Motor de voz (decisión: Piper + Kokoro)

Tres tiers, del más ligero al más expresivo:

| Tier | Motor | Uso | Notas |
|---|---|---|---|
| **Rápida** | **Piper** (CPU, modelo es_MX ~20–60 MB, ~50–150 ms) | confirmaciones cortas ("Listo", "Registré 72.4 kg") | nuevo en `venv-voice`; el 80% de las respuestas de la mascota |
| **Expresiva** | **Kokoro** (ONNX/CPU, ya integrado) | conversación, briefing | reusa `voice_server.py` |
| **Sistema** | **SAPI5 / Web Speech** | fallback | nunca se queda muda |

- **XTTS queda fuera de la mascota** (cold-start ~95 s, ~2.4 GB VRAM) — sigue solo para
  "voz clonada" bajo demanda en el Elfie grande.
- **Trabajo de backend de voz**: añadir Piper a `venv-voice` y un `engine:"piper"` en
  `speak_dispatch` (mismo patrón que ya existe para `xtts`/`kokoro`). Selección de tier
  por longitud del texto o por estado (confirmación → Piper; conversación → Kokoro).

## 2. Arquitectura técnica (reusar vs. construir)

### Ventana flotante `pet` (nueva, Tauri 2)
- Segunda `WebviewWindow`: `transparent:true`, `decorations:false`, `alwaysOnTop:true`,
  `skipTaskbar:true`, `shadow:false`. Carga `app/pet.html` (autocontenido, mismo
  `styles.css` rosa/gris).
- Arrastre con `data-tauri-drag-region` (sin JS de drag).
- **Comandos Rust nuevos** (`lib.rs`/`system_control.rs`):
  `pet_show` · `pet_hide` · `pet_set_size(mini|normal|panel)` · `pet_set_opacity(f)` ·
  `pet_anchor(corner)` · `pet_click_through(bool)`.

### Máquina de estados del avatar (`app/pet/avatar.js`, nuevo)
- Punto único: `Avatar.setState(state, { sub, text })`.
- Se alimenta del **bus de eventos existente** (`elfie:metrics`, `elfie:fullscreen`,
  `elfie:open-capture`, …) + nuevos (`elfie:state`, `elfie:speaking`, `elfie:listening`).
- Reaprovecha la lógica ya viva en el dashboard: `PRTS_AI.attention` / `PRTS_AI.speaking`
  y las clases `escuchando`/`hablando` (auras de la runa) ya hacen exactamente este
  mapeo estado→visual.

### Cerebro en la nube
- Reusa `ElfieConfig.interpreter="anthropic"` + Edge Functions `interpret-command` y chat.
- **Modo "mascota" nuevo** en `MODES` (elfie-config.js): interpreter=anthropic,
  voz=piper, memoria=on, wake=on, Ollama apagado (vía orquestador `unload_ollama`).

### Protocolos
- Reusa `app/elfie/routines.js` (`execStep`: `open_app`, `navigate`, `say`, `set_mode`,
  `spotify_preset`, `set_volume`, `mute_toggle`, `screenshot`, `wait`).
- La mascota solo añade **narración + cambio de avatar por paso** y **bitácora**.

## 3. Estrategia de assets (decisión: PNG → WebP)

| Etapa | Formato | Vivacidad |
|---|---|---|
| MVP (9.0) | **PNG transparente por estado** | estático, cero riesgo/GPU |
| v1 (9.2) | **WebP animado** (loop con alfa) | parpadeo / idle / habla |
| lip-sync | **2–3 sprites de boca** alternados por amplitud de audio | sin lip-sync real |

- Convención: `app/pet/assets/<estado>.{png,webp}`.
- Estados: `neutral, listening, thinking, speaking, executing, confirming, error, alert,
  rest, low, conversation` + contextuales `study, gym, finance, diet, levelup, music`.
- `setState` solo cambia `src`/clase. `app/pet/assets/` **no se versiona si pesa**
  (alinear con `.gitignore` como `voices/`, `models/`).

## 4. Catálogo de funciones priorizado (MVP / v1 / v2)

### Estados visuales
- **MVP**: neutral, escuchando, pensando, hablando, error.
- **v1**: ejecutando, confirmando, alerta, descanso, bajo consumo, conversación; contextuales por módulo (estudio/gym/finanzas/dieta/levelup/música).
- **v2**: proyecto activo, rutina en ejecución, captura recibida, protocolo activado.

### Animación
- **MVP**: parpadeo por timer; cambio de expresión al recibir comando.
- **v1**: idle sutil, pulso al escuchar, boca al hablar, ojos cerrados en espera, glitch en error, brillo al confirmar.
- **v2**: mirada lateral al pensar, pose por módulo.

### Ventana flotante
- **MVP**: 3 tamaños (Mini = solo avatar · Normal = avatar+texto · Panel = avatar+historial+acciones), arrastrar, mostrar/ocultar por atajo.
- **v1**: anclar a esquina, siempre-visible opcional, transparencia ajustable, auto-ocultar, mostrar al activar por voz.
- **v2**: click-through ("solo avatar", sin capturar ratón).

### Burbuja de diálogo
- **MVP**: "procesando…", lo que entendió, respuesta breve, acción ejecutada, error.
- **v1**: confirmaciones, sugerencias, advertencias.

### Confirmaciones (cara visual de "la IA propone, el humano dispone")
- **MVP**: tarjeta junto al avatar; confirmar/cancelar por voz ("sí/confirma/hazlo" · "no/cancela").
- **v1**: reversible vs irreversible (color + copy distintos), "acción pendiente", expresión de espera.

### Voz
- **MVP**: confirmar acciones, responder, modo "solo texto" si bajo rendimiento.
- **v1**: leer briefing/tareas/gym/recordatorios, interrumpir voz por comando, pausar/reanudar, tono por estado.

### Boca/voz
- **v1**: abrir/cerrar boca con audio (2–3 sprites por volumen), quieto en frases cortas, animación solo en conversación.

### Miniacciones (menú clic-derecho / panel)
- **MVP**: captura rápida, activar voz, abrir dashboard/chat.
- **v1**: agregar tarea, registrar peso, registrar gasto, cambiar modo, música, ver estado del sistema, iniciar protocolo.

### Protocolos (sobre `routines.js`)
- **v1**: protocolo activo visible, avatar por protocolo, narrar inicio/cierre, pedir confirmación si modifica datos, bitácora.
- **v2**: mostrar pasos ejecutados en vivo.
- Ejemplos: **Amanecer**, **Enfoque**, **Descanso**, **Bajo Consumo** (encajan con `set_mode`).

## 5. Fases de implementación

- **9.0 — Ventana flotante + estados base**: `pet.html`, segunda WebviewWindow, `Avatar.setState`, 5 estados MVP (PNG), atajo mostrar/ocultar, 3 tamaños.
- **9.1 — Cerebro nube + voz ligera**: modo "mascota" (Anthropic + Ollama off), Piper en `voice_server.py`, burbuja de diálogo, confirmar/cancelar por voz.
- **9.2 — Vida visual**: WebP animado, parpadeo/idle/pulso, boca por audio, estados contextuales por módulo.
- **9.3 — Miniacciones + protocolos**: menú clic-derecho, protocolos sobre `routines.js` con narración + bitácora.
- **9.4 — Pulido**: anclajes, opacidad, click-through, auto-ocultar, tono por estado.

## 6. Datos (migraciones tentativas)

- `..00NN_pet_settings.sql`: preferencias de la mascota (tamaño, posición/ancla, opacidad,
  siempre-visible, motor de voz). *Best-effort*; la feature funciona con `localStorage`
  (mismo criterio que Elfie Core).
- Bitácora de protocolos: reutilizar `lore_entries` (kind `diario`) **o** tabla nueva
  `protocol_log` (`protocol`, `started_at`, `ended_at`, `steps jsonb`, `status`).

## 7. Decisiones tomadas

- **Assets**: PNG estático en el MVP → WebP animado en 9.2.
- **Voz**: Piper (confirmaciones) + Kokoro (conversación) + SAPI/Web Speech (fallback). XTTS fuera.
- **Cerebro**: Anthropic por defecto en modo mascota; Ollama apagado vía orquestador (Fase 8.2); fallback local total.

## 8. Decisiones abiertas

- Arte del avatar: ¿quién/cómo se producen los archivos por estado? (estilo anime coherente con identidad de Elfie / PRTS-002).
- Atajo global para mostrar/ocultar la mascota (¿reusar uno existente o nuevo?).
- ¿La mascota y la ventana grande de Elfie conviven abiertas, o la mascota la reemplaza en modo compacto?
- Voz de Piper: elegir modelo es_MX concreto y licencia.

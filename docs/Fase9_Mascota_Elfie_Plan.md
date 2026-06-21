# Fase 9 — Mascota Virtual de Elfie (plan)

> Subproyecto: una **ventana flotante** sobre el escritorio que es la cara de Elfie.
> Un avatar que **alterna archivos según su estado**, habla con voz ligera, muestra
> una burbuja de texto y ejecuta protocolos/miniacciones. **El cerebro vive en la
> nube (Anthropic) por defecto** para dejar la GPU casi libre; lo local queda como
> respaldo (degradación total — principio no negociable de la Fase 4).

## Correcciones post-cierre (revisión de bugs)

- **Menú contextual recortado**: la ventanita (~250 px) no contenía el menú (12 ítems ≈ 400 px) →
  ítems inferiores inaccesibles. Fix: `pet_resize` (Rust) agranda la ventana mientras el menú está
  abierto y la restaura al cerrarlo; + respaldo CSS `max-height/overflow` (desplazable en el borde).
- **Trampa de "solo avatar"**: si se activaba el click-through, no había forma fácil de salir. Fix:
  mostrar la mascota (atajo Ctrl+Shift+E / tray / `pet_show`) **siempre** la vuelve interactiva
  (`set_ignore_cursor_events(false)` + evento `pet:exit-solo`).
- **Voz "navegador" no animaba la mascota**: `elfie:say` se emitía después del `return` → sin burbuja.
  Fix: emitir `elfie:say` antes de la rama de motor (la mascota refleja lo dicho en cualquier motor).
- **Piper con API obsoleta**: `synthesize(text, wf)` no existe en piper-tts 1.x → siempre caía a Kokoro.
  Fix: usar `synthesize_wav` (con `SynthesisConfig` para velocidad) y fallback a la API antigua.
- **Cambiar modo desde la mascota** no reconfiguraba el sidecar (wake/modelo). Fix: replica las llamadas
  `/wake/enable|disable` + `/config` del selector de Elfie Core.

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

- ✅ **9.0 — Ventana flotante + estados base**: `pet.html`, segunda WebviewWindow, `Avatar.setState`, 5 estados MVP (SVG), atajo mostrar/ocultar, 3 tamaños. *(implementado)*
- ✅ **9.1 — Cerebro nube + voz ligera**: modo "mascota" (Anthropic + Piper), Piper en `voice_server.py`, burbuja de diálogo, tarjeta de confirmación + confirmar/cancelar por voz. *(implementado; ver §9)*
- ✅ **9.2 — Vida visual**: boca animada (2 sprites), respiración idle + parpadeo, estados contextuales por módulo, soporte WebP. *(implementado; ver §9)*
- ✅ **9.3 — Miniacciones + protocolos**: menú clic-derecho, protocolos sobre `routines.js` con narración + bitácora. *(implementado; ver §9)*
- ✅ **9.4 — Pulido**: anclajes a esquina, opacidad, click-through "solo avatar", auto-ocultar, tono visual por estado. *(implementado; ver §9)*

**Fase 9 completa.**

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

- Arte del avatar: ¿quién/cómo se producen los archivos por estado? (estilo anime coherente con identidad de Elfie / PRTS-002). Hoy hay **placeholders SVG** en `app/pet/assets/`.
- ¿La mascota y la ventana grande de Elfie conviven abiertas, o la mascota la reemplaza en modo compacto?
- Voz de Piper: elegir modelo es_MX concreto y licencia.

## 9. Estado de implementación (9.0 + 9.1)

### Archivos
- `app/pet.html` — ventana flotante (avatar + burbuja + confirmación + historial + acciones; 3 tamaños).
- `app/pet/avatar.js` — máquina de estados `window.Avatar` (web-safe): `setState`, `bubble`, `confirmCard`, `voiceConfirm`, `setSize`, parpadeo idle, escucha de eventos del cerebro.
- `app/pet/assets/{neutral,listening,thinking,speaking,error}.svg` — placeholders on-brand.
- `elfie-desktop/src-tauri/src/lib.rs` — ventana `pet` (transparent, always-on-top, sin decoración, oculta al inicio); comandos `pet_toggle/show/hide/set_size/click_through`; atajo **Ctrl+Shift+E**; ítem de tray "Mascota Elfie".
- `app/elfie/desktop.js` — `elfieSys.pet*`; emite `elfie:say`/`elfie:speaking`/`elfie:listening` para conducir el avatar; escucha `pet:action` (acciones rápidas).
- `app/elfie/elfie-config.js` — modo **`mascota`** (Anthropic + Piper + memoria); `voiceEngine: "piper"`.
- `app/elfie.html` — botón "Mostrar mascota"; modo Mascota; motor Piper en el selector.
- `elfie-desktop/sidecars/voice_server.py` — motor **Piper** (`load_piper`/`speak_piper`), `engine:"piper"` en `speak_dispatch` con fallback a Kokoro; `/health` reporta `piper`.

### Conducción del avatar (eventos app-wide)
`elfie:state {state,text}` · `elfie:say {text}` · `elfie:speaking <bool>` · `elfie:listening <bool>` ·
`elfie:thinking` · `elfie:bubble {text,kind,sticky}` · `elfie:confirm {text,irreversible}` ·
`elfie:voice-confirm {text}` · y de vuelta `pet:action {act}` / `pet:confirm-result {ok}`.

### Setup del usuario (una vez, para la voz ligera)
Instalar Piper en `venv-voice` y dejar un modelo es_MX:
```
elfie-desktop/venv-voice/Scripts/pip install piper-tts
# Descargar voz es_MX (.onnx + .onnx.json) y colocarla en:
elfie-desktop/models/piper/   (o exportar ELFIE_PIPER_MODEL=<ruta .onnx>)
```
Mientras no exista el modelo, `speak_piper` degrada a **Kokoro** automáticamente (nada se rompe).
`models/` está en `.gitignore` → el `.onnx` se queda local.

### Verificado
- `pet.html` carga en web (sin Tauri) en modo demo: cicla estados, alterna el archivo de avatar
  por estado, burbuja/confirmación/tamaños (mini/normal/panel) OK, **sin errores de consola**.
- `elfie.html` carga sin errores; modo "mascota" y motor "piper" presentes.
- `voice_server.py` compila (`py_compile`).

### Pendiente de probar en escritorio (requiere recompilar Tauri)
- Creación/transparencia de la ventana `pet`, atajo Ctrl+Shift+E, tray, comandos de tamaño/click-through.
- Voz Piper real (tras instalar el modelo).

### Cableado parcial (siguiente iteración)
- `pet:action` enruta **captura** y **chat**; **voz** reanuda wake y **dashboard** hace scroll.
  Falta integrar mostrar la ventana principal oculta desde la mascota.
- Confirmar/cancelar por voz: la API (`Avatar.voiceConfirm`/`elfie:voice-confirm`) está lista,
  pero conectarla al router de voz real (`actions.js`) queda para 9.3.

### 9.2 — Vida visual (añadido)
- **Boca animada**: `startTalk()` alterna `speaking` ↔ `speaking-closed` cada 150 ms mientras
  el estado es `speaking` (ilusión de habla sin analizar audio → 0 GPU).
- **Idle**: respiración en `.avatar-wrap` (CSS `pet-breathe`, en `.avatar-wrap` para no chocar
  con el `scaleY` del parpadeo del `img`); parpadeo en estados de reposo. `prefers-reduced-motion` ok.
- **Contextos por módulo**: `restState` + `Avatar.setContext(ctx)` + evento `elfie:context` +
  `elfieSys.petContext()`. 6 SVG con glifo (study/gym/finance/diet/levelup/music). El **disparo
  automático** por módulo es follow-up (solo `index.html` carga el bridge); hoy se fija por API/evento.
- **WebP-ready**: `assetUrl()` + `Avatar.setExt("webp")` cambian de SVG a WebP sin tocar la lógica.
- **Verificado en web**: contexto (gym → pose+status), boca alterna sprites, `pet-breathe` aplicado,
  6 contextos OK, API completa, **0 errores de consola**.

### 9.3 — Miniacciones + protocolos (añadido)
- **Menú clic-derecho** (`#pet-menu`): captura, voz, música, protocolo…, cambiar modo, ver estado,
  dashboard, chat, tamaño. `avatar.js` lo abre en el cursor y lo cierra con clic/Escape; enruta por `pet:action`.
- **`pet:action` (desktop.js)**: `music` (contexto + resume Spotify), `mode` (cicla modos + narra),
  `status` (burbuja modo/voz/wake), `protocol` (abre gestor de rutinas), + captura/voz/chat/dashboard.
- **Protocolos = rutinas narradas**: `routines.js run()` narra inicio/cierre (`say`), pone el avatar en
  `executing`, muestra cada paso en la burbuja y vuelve a reposo. Cubre voz (`tryRun`), gestor (▶) y mascota.
- **Bitácora**: `localStorage` (`prts_protocol_log`) durable + best-effort Supabase `protocol_log`
  (migración `..0022`). `elfieRoutines.bitacora()` la lee. Degradación total sin la tabla.
- **Verificado en web**: menú aparece/cierra con 9 ítems; `run()` de un protocolo de 2 pasos registra
  en bitácora (`{steps_total:2, steps_done:2, status:"completado"}`); **0 errores de consola**.

### Pendiente de probar en escritorio (9.3)
- Narración real (Piper/Kokoro) y burbuja por paso en la ventana `pet` mientras corre un protocolo.
- Inserción en Supabase `protocol_log` (requiere `db:push` de la migración `..0022`).

### 9.4 — Pulido (añadido)
- **Anclaje a esquina**: comando Rust `pet_anchor(corner)` (monitor actual + margen); menú "Anclar a
  esquina" cicla `tr→br→bl→tl`. Persiste en `prts_pet_cfg`.
- **Opacidad**: `Avatar.setOpacity`/`cycleOpacity` (100/85/70/55 %) sobre el contenido; menú "Opacidad".
- **Solo-avatar (click-through)**: menú "Solo avatar" → `pet_click_through(true)` + `body.solo` oculta el
  chrome. Salida confiable desde el toggle **"Solo avatar"** en Elfie Core (`pet:config {solo:false}`).
- **Auto-ocultar**: toggle en Elfie Core; tras ~20 s en reposo `pet_hide`, reaparece (`pet_show`) con actividad.
- **Tono por estado (visual)**: `KIND` mapea estado→color de burbuja + etiqueta. El tono **auditivo** por
  estado queda como follow-up (Kokoro/Piper solo exponen velocidad).
- **Verificado en web**: opacidad (body.opacity=0.85), ancla (tr→br), solo (chrome oculto, sobrevive al
  cambio de tamaño), tono (error→rojo, speaking→rosa), menú con 12 ítems, tamaños ciclan; **0 errores**.

### Pendiente de probar en escritorio (9.4)
- Posicionamiento real de `pet_anchor`, click-through del SO, `pet_hide`/`pet_show` del auto-ocultar.

### Cierre (todo lo de código dejado listo)
- **Contexto automático por módulo**: `app/pet/context-bridge.js` incluido en gym/dieta/finanzas/apuntes/
  levelup-* → emite `elfie:context` por `location.pathname`; el dashboard repone `neutral`.
- **WebP**: toggle "Avatar animado (WebP)" en Elfie Core (`pet:config {ext}`); manifiesto de arte en
  `app/pet/assets/README.md` (nombres exactos por estado).
- **Follow-ups de código menores** (no bloquean la fase): confirmar/cancelar por voz conectado al router
  real (`actions.js`) y tono **auditivo** por estado.

## 10. Checklist para finalizar (acciones del usuario)

1. **Recompilar el desktop** para activar lo nativo (ventana `pet`, atajo Ctrl+Shift+E, tray, anclaje,
   click-through, auto-ocultar): `cd elfie-desktop && npm run dev` (o `npm run build`).
2. **`npm run db:push`** → crea la tabla `protocol_log` (la bitácora ya funciona en localStorage sin esto).
3. **Instalar Piper** para la voz ligera: en `venv-voice`, `pip install piper-tts` + modelo es_MX `.onnx`
   en `elfie-desktop/models/piper/` (o env `ELFIE_PIPER_MODEL`). Sin modelo → cae a Kokoro solo.
4. **Arte real del avatar** (opcional, mejora visual): dejar los `.webp` en `app/pet/assets/` según el
   `README.md` y activar el toggle "Avatar animado (WebP)" en Elfie Core.
5. **Deploy web** (`git push` ya hecho → Vercel redeploya): la mascota es de escritorio, pero el resto
   de la app (incluido `context-bridge.js` NO-OP) funciona igual en web.

# PRTS — Visión, alcance y capacidades de Elfie

> Documento de referencia del producto. Última actualización: **2026-06-19**.
> Fuente de verdad técnica: `CLAUDE.md`. Este documento es la vista de alto nivel.

**PRTS** es el sistema personal de organización de Sylft (estudiante TecNM Celaya,
instructor en Wolves robótica y LevelUp idiomas, atleta de gym). Es una **PWA
vanilla** (HTML/JS, sin frameworks ni build) sobre **Supabase**, que existe en dos
formas del **mismo código**:

- **Web** — desplegada en Vercel, móvil y escritorio.
- **App de escritorio Elfie** — Tauri (Rust) que carga el mismo `app/` y añade voz
  local, control del sistema operativo y la IA on-device.

---

## 🧩 Funciones de la aplicación (módulos)

| Módulo | Qué hace |
|---|---|
| **Dashboard** | Núcleo radial con la **runa** al centro y paneles en órbita (gym, tareas, progreso, briefing, captura). 3 modos: Constelación / Mando / Diario. Briefing diario pre-generado por IA. |
| **Tareas / Semana / Proyectos** | Pendientes por origen (escuela/wolves/levelup/personal), plantilla semanal recurrente, proyectos. |
| **Inbox (captura)** | Bandeja de entrada que la IA **clasifica y sugiere** a qué módulo va cada nota (sugerir-y-confirmar, o automático con umbral). |
| **Gimnasio** | Catálogo de ejercicios, sesiones, series, progresión por ejercicio. |
| **Dieta** | Registro de kcal/proteína y peso corporal. |
| **Apuntes** | Notas de clase con plantilla, enlaces `[[wiki]]`, LaTeX y **búsqueda semántica (RAG)**. |
| **Finanzas** | Ingresos/gastos personales con gráficas (dona, balance, tendencia). |
| **Recordatorios** | Notifican al **celular vía Google Calendar** (PRTS crea el evento; Google avisa con la app cerrada). |
| **LevelUp** | Mini-ERP de la academia: maestros, alumnos, clases (recurrentes y sueltas), pagos mensuales, sueldos, gastos de operación y administración con gráficas. |
| **Insights** | La IA agrega ~4 semanas de datos y entrega 2-5 hallazgos accionables. |
| **Chat con Elfie** | Conversación multi-turno con memoria y personalidad (solo escritorio). |

---

## 📍 Alcance actual (lo que ya funciona)

- **Fases 1–5 completas:** todos los módulos de arriba, la capa IA en la nube
  (Edge Functions + Anthropic), voz web push-to-talk, wake word «Dalia»,
  recordatorios a celular, y los módulos LevelUp y Finanzas.
- **Fase 6 completa:** RAG local de apuntes + **XTTS (voz clonada)** en el escritorio.
- **Fase 7.1 + extras:** chat conversacional con memoria, interfaz pulida,
  **wake word on-device real (Porcupine)** y **control real de Spotify**.

**Principios firmes (no negociables):**

1. **Degradación total** — si la IA falla o se apaga, todo tiene camino manual.
2. **La IA propone, el humano dispone** — las escrituras pasan por confirmación
   (salvo manos libres por voz, que confirma hablando).
3. **Intenciones, no ejecución** — el LLM devuelve JSON validado; el cliente
   ejecuta contra una whitelist cerrada (nunca `eval`).
4. **Costo observable** — cada llamada en la nube se registra; tope mensual.
5. **Privacidad** — lo local (voz, LLM, memoria, RAG) nunca sale de la máquina.

**Límites honestos hoy:**

- La generación de imágenes aún no existe.
- La **VRAM de 8 GB compartida** es el cuello de botella del escritorio
  (Whisper + Kokoro + Ollama + XTTS no caben todos calientes).
- Varios features dependen de setup del usuario: claves de Spotify/Picovoice,
  conectar Google Calendar.

---

## 🤖 Capacidades de Elfie

### Dentro de la app

- **Briefing diario** hablado/escrito y **resúmenes** del día/tareas/gym por voz.
- **Inbox inteligente:** clasifica capturas y las enruta al módulo correcto.
- **Comandos de voz** (vocabulario cerrado, ejecutado por whitelist): navegar,
  crear tareas, registrar peso y series de gym, recordatorios, clima.
- **Chat con memoria y personalidad:** conversación real; recuerda hechos durables
  (explícito "recuerda que…" + extracción automática) con memoria vectorial on-device.
- **RAG de apuntes:** "¿qué anotamos sobre X?" con respuesta fundamentada en tus notas.
- **Insights:** detecta patrones en tus datos.
- **Voz:** responde hablando (Kokoro o tu **voz clonada XTTS**), configurable.

### Fuera de la app (escritorio, vía Tauri)

- **Control del SO:** abrir apps/carpetas/webs (Discord, Spotify, VS Code…),
  volumen, mute, **apagar/suspender**, portapapeles, **captura de pantalla**,
  métricas CPU/RAM/GPU en vivo.
- **Escucha continua manos libres:** wake word «Dalia» **on-device real**
  (Porcupine), funciona con la ventana en segundo plano.
- **Atajos globales** (Ctrl+Space captura, Alt+E voz, F11 pantalla completa),
  **tray**, autostart y **notificaciones nativas** de Windows.
- **Control de Spotify** real (reproducir/pausar/saltar/volumen) y rutinas
  ("Buen día Dalia" abre tu espacio de trabajo).
- **Todo local y privado:** STT (Whisper), TTS (Kokoro/XTTS), LLM (Ollama qwen2.5)
  y memoria (LanceDB) corren en tu máquina, $0 y sin enviar datos.

---

## 🔭 Vista a futuro

### Próximo (Fase 7 pendiente)

- **7.2 — Generación de imágenes anime** (Illustrious XL + diffusers): un modelo,
  un estilo. Requiere un **orquestador de GPU** que libere Ollama antes de generar
  (el reto de los 8 GB).
- **7.3 — Extras:** **visión de pantalla** (Elfie "ve" la pantalla y responde),
  **avatar anime de Dalia**, briefing hablado matutino, diario por voz, RAG de PDFs.

### Más allá

- Búsqueda semántica **global** (no solo apuntes).
- Spotify y Google Calendar **bidireccionales**.
- Captura remota por Telegram/WhatsApp; Supabase Storage para adjuntos.
- **Salud del proyecto:** respaldo remoto (resolver el push tras limpiar la
  historia de binarios), `requirements.txt` reproducible para los venvs, CI ligero.

### El norte

Que Elfie pase de asistente de comandos a **compañera proactiva** — que vea,
recuerde, converse y actúe en la PC y en la vida de Sylft (escuela, academias, gym,
finanzas) manteniéndose **local, privada y siempre con camino manual** si la IA se apaga.

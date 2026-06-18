#!/usr/bin/env python3
"""Genera el documento de planificación Elfie-PRTS v2 como PDF."""

HTML_CONTENT = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.65;
    color: #1a1a2e;
    background: #ffffff;
  }

  /* ── PORTADA ── */
  .cover {
    background: #0d1b2a;
    color: #fff;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 60pt 64pt;
    page-break-after: always;
    position: relative;
  }
  .cover-accent { position: absolute; right: 0; top: 0; bottom: 0; width: 6pt; background: #4a90b8; }
  .cover-ver {
    font-family: 'Courier New', monospace;
    font-size: 8pt; letter-spacing: 3px; text-transform: uppercase;
    color: #4a90b8; margin-bottom: 20pt;
  }
  .cover-title {
    font-family: Georgia, serif;
    font-size: 56pt; font-weight: 700; line-height: 1;
    color: #fff; margin-bottom: 6pt;
  }
  .cover-subtitle {
    font-family: Georgia, serif;
    font-size: 18pt; font-weight: 400;
    color: #4a90b8; margin-bottom: 32pt;
  }
  .cover-desc {
    font-size: 11pt; color: #8aa8c0;
    max-width: 380pt; line-height: 1.75; margin-bottom: 40pt;
  }
  .cover-chips { display: flex; flex-wrap: wrap; gap: 8pt; margin-bottom: 40pt; }
  .cover-chip {
    font-family: 'Courier New', monospace; font-size: 7.5pt;
    padding: 4pt 10pt; border: 1pt solid #1e3a52;
    color: #4a90b8; letter-spacing: 1px; border-radius: 3pt;
  }
  .cover-footer {
    font-family: 'Courier New', monospace; font-size: 7.5pt;
    color: #2e4a60; border-top: 1pt solid #1e3a52;
    padding-top: 14pt; letter-spacing: 1px;
  }

  /* ── TABLA DE CONTENIDOS ── */
  .toc { padding: 50pt 64pt; page-break-after: always; }
  .page-title {
    font-family: Georgia, serif;
    font-size: 22pt; color: #0d1b2a;
    border-bottom: 2pt solid #4a90b8;
    padding-bottom: 8pt; margin-bottom: 24pt;
  }
  .toc-row {
    display: flex; justify-content: space-between;
    align-items: baseline; padding: 5pt 0;
    border-bottom: 1pt dotted #dde3ea;
  }
  .toc-row.main { font-weight: 600; color: #0d1b2a; margin-top: 10pt; font-size: 10.5pt; }
  .toc-row.sub  { color: #4a6280; padding-left: 14pt; font-size: 9.5pt; }
  .toc-num { font-family: 'Courier New', monospace; font-size: 9pt; color: #4a90b8; }

  /* ── PÁGINAS ── */
  .page { padding: 44pt 64pt; page-break-after: always; }
  .page:last-child { page-break-after: avoid; }

  /* Encabezado de sección */
  .sec-head { display: flex; align-items: center; gap: 12pt; margin-bottom: 22pt; }
  .sec-n {
    font-family: 'Courier New', monospace; font-size: 8pt;
    background: #eef4fa; color: #4a90b8;
    padding: 4pt 9pt; border-radius: 3pt; letter-spacing: 1px;
    white-space: nowrap;
  }
  .sec-t { font-family: Georgia, serif; font-size: 21pt; font-weight: 700; color: #0d1b2a; }

  h3 {
    font-size: 11.5pt; font-weight: 700; color: #0d1b2a;
    margin: 18pt 0 7pt 0; padding-left: 10pt;
    border-left: 3pt solid #4a90b8;
  }
  h4 {
    font-family: 'Courier New', monospace; font-size: 8.5pt;
    font-weight: 700; color: #4a90b8;
    text-transform: uppercase; letter-spacing: 1.5px;
    margin: 12pt 0 5pt 0;
  }
  p { margin-bottom: 8pt; color: #2c3e50; }

  /* ── CALLOUTS ── */
  .call {
    border-radius: 5pt; padding: 13pt 16pt; margin: 13pt 0;
  }
  .call-info { background: #eef4fa; border-left: 4pt solid #4a90b8; }
  .call-warn { background: #fef9e7; border-left: 4pt solid #f39c12; }
  .call-ok   { background: #eafaf1; border-left: 4pt solid #27ae60; }
  .call-dark { background: #0d1b2a; color: #a8c8e0; border-left: 4pt solid #4a90b8; }
  .call-dark p, .call-dark li { color: #8aa8c0; }
  .call-dark h4, .call-dark .call-t { color: #4a90b8; }
  .call-t {
    font-family: 'Courier New', monospace; font-size: 8pt;
    font-weight: 700; text-transform: uppercase; letter-spacing: 1px;
    margin-bottom: 5pt; color: #4a90b8;
  }
  .call-warn .call-t { color: #c0882a; }
  .call-ok .call-t   { color: #1e8449; }

  /* ── TABLAS ── */
  table { width: 100%; border-collapse: collapse; margin: 10pt 0; font-size: 9.5pt; }
  thead tr { background: #0d1b2a; color: #fff; }
  thead th {
    padding: 8pt 10pt; text-align: left;
    font-family: 'Courier New', monospace;
    font-size: 7.5pt; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
  }
  tbody tr:nth-child(even) { background: #f4f7fb; }
  tbody tr:nth-child(odd)  { background: #fff; }
  tbody td { padding: 7pt 10pt; border-bottom: 1pt solid #e0e8f0; vertical-align: top; }

  .b { display:inline-block; font-family:'Courier New',monospace; font-size:7pt;
       padding:2pt 6pt; border-radius:3pt; font-weight:700; }
  .b-g { background:#d5f5e3; color:#1e8449; }
  .b-b { background:#d6eaf8; color:#1a5276; }
  .b-y { background:#fdebd0; color:#784212; }
  .b-r { background:#fadbd8; color:#78281f; }
  .b-p { background:#e8daef; color:#6c3483; }

  /* ── CÓDIGO ── */
  .code {
    background: #0d1b2a; color: #a8d8f0;
    font-family: 'Courier New', monospace; font-size: 7.8pt;
    padding: 13pt 15pt; border-radius: 5pt;
    margin: 8pt 0; line-height: 1.7;
  }
  .code .kw  { color: #4a90b8; }
  .code .cm  { color: #405060; font-style: italic; }
  .code .st  { color: #7ecb7a; }
  .code .num { color: #e8b84b; }
  .code .hl  { color: #c8daea; font-weight: bold; }
  code {
    font-family: 'Courier New', monospace; font-size: 8.5pt;
    background: #eef4fa; color: #1a5276;
    padding: 1pt 4pt; border-radius: 2pt;
  }

  ul, ol { padding-left: 16pt; margin-bottom: 8pt; }
  li { margin-bottom: 3pt; color: #2c3e50; }
  li strong { color: #0d1b2a; }

  /* ── TARJETAS DE FASE ── */
  .phase-grid { display:grid; grid-template-columns:1fr 1fr; gap:10pt; margin:10pt 0; }
  .ph {
    border:1.5pt solid #dde3ea; border-radius:7pt;
    padding:13pt; background:#fafcff;
  }
  .ph-head { display:flex; align-items:center; gap:8pt; margin-bottom:7pt; }
  .ph-n {
    font-family:'Courier New',monospace; font-size:7.5pt; font-weight:700;
    background:#0d1b2a; color:#4a90b8; padding:3pt 7pt; border-radius:3pt;
  }
  .ph-name { font-weight:700; font-size:10.5pt; color:#0d1b2a; }
  .ph-dur  { font-family:'Courier New',monospace; font-size:7.5pt; color:#4a90b8; margin-left:auto; }
  .ph ul   { font-size:9pt; }
  .ph .tag {
    display:inline-block; font-family:'Courier New',monospace;
    font-size:6.5pt; padding:1pt 5pt; border-radius:2pt;
    background:#d6eaf8; color:#1a5276; font-weight:700; margin-left:4pt;
  }
  .ph .tag-g { background:#d5f5e3; color:#1e8449; }
  .ph .tag-p { background:#e8daef; color:#6c3483; }

  /* ── HARDWARE ── */
  .hw-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:8pt; margin:10pt 0; }
  .hw {
    background:#0d1b2a; border-radius:7pt;
    padding:13pt; text-align:center;
  }
  .hw-ico  { font-size:18pt; margin-bottom:5pt; }
  .hw-lbl  { font-family:'Courier New',monospace; font-size:7pt; color:#4a90b8; letter-spacing:1px; text-transform:uppercase; }
  .hw-val  { font-size:11pt; font-weight:700; color:#fff; margin:3pt 0; }
  .hw-note { font-size:7.5pt; color:#6a8aaa; line-height:1.4; }

  /* ── VOZ CARDS ── */
  .vc-grid { display:grid; grid-template-columns:1fr 1fr; gap:9pt; margin:10pt 0; }
  .vc {
    border-radius:7pt; padding:12pt;
    border:1.5pt solid #dde3ea; background:#fafcff;
  }
  .vc.rec  { border-color:#4a90b8; background:#eef4fa; }
  .vc.cld  { border-color:#c0882a; background:#fef9e7; }
  .vc-name { font-weight:700; font-size:10.5pt; color:#0d1b2a; margin-bottom:3pt; }
  .vc-tag  { font-family:'Courier New',monospace; font-size:7pt; text-transform:uppercase; letter-spacing:1px; color:#4a6280; }
  .vc-row  { display:flex; justify-content:space-between; font-size:9pt; margin-top:5pt; color:#4a6280; }
  .vc-row strong { color:#0d1b2a; }

  /* ── MODELO GRID ── */
  .mod-grid { display:grid; grid-template-columns:1fr 1fr; gap:9pt; margin:10pt 0; }
  .mod {
    border:1.5pt solid #dde3ea; border-radius:7pt;
    padding:12pt; background:#fafcff;
  }
  .mod-name { font-weight:700; color:#0d1b2a; font-size:10.5pt; margin-bottom:5pt; }
  .mod-row  { display:flex; justify-content:space-between; font-size:9pt; color:#4a6280; margin-top:3pt; }
  .mod-row strong { color:#0d1b2a; }

  /* ── SUGERENCIAS ── */
  .sug-grid { display:grid; grid-template-columns:1fr 1fr; gap:9pt; margin:10pt 0; }
  .sug {
    border-radius:7pt; padding:12pt 13pt;
    border:1pt solid #dde3ea; background:#fafcff;
  }
  .sug.hi { border-left:4pt solid #27ae60; }
  .sug.md { border-left:4pt solid #4a90b8; }
  .sug.ex { border-left:4pt solid #9b59b6; }
  .sug-t  { font-weight:700; font-size:10pt; margin-bottom:3pt; color:#0d1b2a; }
  .sug-b  { font-size:9pt; color:#4a6280; line-height:1.5; }

  /* ── REPO STRUCTURE ── */
  .repo {
    background:#0d1b2a; color:#c8daea;
    font-family:'Courier New',monospace; font-size:8pt;
    padding:14pt 16pt; border-radius:7pt; margin:10pt 0; line-height:1.75;
  }
  .repo .hl  { color:#4a90b8; font-weight:bold; }
  .repo .new { color:#5dbb6d; }
  .repo .dim { color:#405060; }
  .repo .cm  { color:#405060; font-style:italic; }

  /* ── DECISIÓN BOX ── */
  .dec {
    background:#f4f7fb; border-radius:7pt;
    padding:14pt 16pt; margin:10pt 0; border:1pt solid #dde3ea;
  }
  .dec-lbl { font-family:'Courier New',monospace; font-size:8pt;
             text-transform:uppercase; letter-spacing:1px; color:#4a90b8;
             margin-bottom:4pt; font-weight:700; }
  .dec-val { font-size:13pt; font-weight:700; color:#0d1b2a; margin-bottom:3pt; }
  .dec-why { font-size:9pt; color:#4a6280; }

  /* ── WIN10 BOX ── */
  .win10-grid { display:grid; grid-template-columns:1fr 1fr; gap:9pt; margin:10pt 0; }
  .win10-card {
    border-radius:7pt; padding:11pt 13pt;
    border:1pt solid #dde3ea; background:#fafcff;
  }
  .win10-card.ok   { border-left:4pt solid #27ae60; }
  .win10-card.warn { border-left:4pt solid #f39c12; }
  .win10-card.risk { border-left:4pt solid #e74c3c; }
  .win10-t { font-weight:700; font-size:10pt; margin-bottom:4pt; color:#0d1b2a; }
  .win10-b { font-size:9pt; color:#4a6280; line-height:1.5; }

  .divider { border:none; border-top:1pt solid #dde3ea; margin:14pt 0; }

  @page { margin: 0; size: A4; }
</style>
</head>
<body>

<!-- ══════════ PORTADA ══════════ -->
<div class="cover">
  <div class="cover-accent"></div>
  <div class="cover-ver">Planificación · v2.0 · Junio 2026</div>
  <div class="cover-title">Elfie</div>
  <div class="cover-subtitle">PRTS Desktop Edition</div>
  <div class="cover-desc">
    Evolución de PRTS a aplicación de escritorio nativa con control
    del sistema operativo, IA local, voz configurable y personalidad
    propia. Base de datos compartida con la versión web.
    Uso exclusivo de Sylft.
  </div>
  <div class="cover-chips">
    <div class="cover-chip">PROPIETARIO: SYLFT</div>
    <div class="cover-chip">IA: ELFIE</div>
    <div class="cover-chip">FRAMEWORK: TAURI 2.x</div>
    <div class="cover-chip">RTX 5060 · 8 GB VRAM</div>
    <div class="cover-chip">16 GB RAM · RYZEN 5 5600G</div>
    <div class="cover-chip">WINDOWS 10 / 11</div>
  </div>
  <div class="cover-footer">
    MONOREPO: sylftkto/mi-app-PRTS &nbsp;·&nbsp;
    BRANCH: elfie-desktop/ &nbsp;·&nbsp;
    BD: SUPABASE COMPARTIDA
  </div>
</div>

<!-- ══════════ TABLA DE CONTENIDOS ══════════ -->
<div class="toc">
  <div class="page-title">Contenido</div>

  <div class="toc-row main"><span>1 · Visión y Diferencias vs PRTS Web</span><span class="toc-num">3</span></div>
  <div class="toc-row main"><span>2 · Estructura del Repositorio (Monorepo)</span><span class="toc-num">4</span></div>
  <div class="toc-row main"><span>3 · Compatibilidad Windows 10</span><span class="toc-num">4</span></div>
  <div class="toc-row main"><span>4 · Arquitectura del Sistema</span><span class="toc-num">5</span></div>
  <div class="toc-row sub"><span>Hardware y presupuesto de VRAM</span><span class="toc-num">5</span></div>
  <div class="toc-row sub"><span>Diagrama de sistema</span><span class="toc-num">5</span></div>
  <div class="toc-row main"><span>5 · Módulos del Sistema</span><span class="toc-num">6</span></div>
  <div class="toc-row sub"><span>Control del SO · Monitor · Personalidad Elfie</span><span class="toc-num">6</span></div>
  <div class="toc-row main"><span>6 · Capa de Voz (STT + TTS)</span><span class="toc-num">7</span></div>
  <div class="toc-row sub"><span>Whisper.cpp · Kokoro · XTTS v2 · Opciones cloud</span><span class="toc-num">7</span></div>
  <div class="toc-row main"><span>7 · IA Local con Ollama (RTX 5060)</span><span class="toc-num">8</span></div>
  <div class="toc-row sub"><span>Modelos · Router híbrido · Ahorro estimado</span><span class="toc-num">8</span></div>
  <div class="toc-row main"><span>8 · Base de Datos Compartida</span><span class="toc-num">9</span></div>
  <div class="toc-row sub"><span>Nuevas tablas · Sincronización Realtime</span><span class="toc-num">9</span></div>
  <div class="toc-row main"><span>9 · Fases de Desarrollo (Restructuradas)</span><span class="toc-num">10</span></div>
  <div class="toc-row main"><span>10 · Mejoras Técnicas Internas</span><span class="toc-num">11</span></div>
  <div class="toc-row sub"><span>RAG local (LanceDB) · Global Shortcuts</span><span class="toc-num">11</span></div>
  <div class="toc-row main"><span>11 · Expansiones de Capacidad</span><span class="toc-num">12</span></div>
  <div class="toc-row sub"><span>Routine Engine Visual · Integración Obsidian</span><span class="toc-num">12</span></div>
  <div class="toc-row main"><span>12 · Integraciones y Visión a Largo Plazo</span><span class="toc-num">13</span></div>
</div>

<!-- ══════════ 1 · VISIÓN ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">01</div><div class="sec-t">Visión y Diferencias vs PRTS Web</div></div>

  <div class="call call-info">
    <div class="call-t">Propósito</div>
    <p>Elfie-PRTS Desktop extiende PRTS web sin reemplazarla. Mientras PRTS web es accesible desde cualquier
    dispositivo, Elfie vive permanentemente en la máquina de Sylft con acceso nativo al SO, IA local y
    personalidad configurable. Comparten la misma base de datos Supabase — los datos siempre están sincronizados.</p>
  </div>

  <h3>Qué cambia y añade Elfie Desktop</h3>
  <table>
    <thead><tr><th>Capacidad</th><th>PRTS Web (actual)</th><th>Elfie Desktop (nuevo)</th></tr></thead>
    <tbody>
      <tr><td><strong>Control del SO</strong></td><td>Solo protocol handlers (discord://, spotify:...)</td><td>Nativo: procesos, ventanas, volumen, archivos</td></tr>
      <tr><td><strong>STT</strong></td><td>webkitSpeechRecognition → Google Cloud</td><td>Whisper.cpp local, sin Google, funciona offline</td></tr>
      <tr><td><strong>Wake word</strong></td><td>webkitSpeechRecognition continuo (Dalia)</td><td>Picovoice Porcupine on-device (real nivel SO)</td></tr>
      <tr><td><strong>TTS / Voz de Elfie</strong></td><td>speechSynthesis del navegador</td><td>Kokoro / Piper local · XTTS v2 (clonación)</td></tr>
      <tr><td><strong>LLM</strong></td><td>Solo Anthropic API (costo por llamada)</td><td>Ollama local (RTX 5060) + Anthropic fallback</td></tr>
      <tr><td><strong>Accesos rápidos</strong></td><td>Sin atajos globales</td><td>Ctrl+Space · Alt+E desde cualquier app</td></tr>
      <tr><td><strong>Búsqueda en notas</strong></td><td>Búsqueda textual simple</td><td>RAG local semántico (Apuntes)</td></tr>
      <tr><td><strong>Rutinas de inicio</strong></td><td>Hardcodeadas en actions.js</td><td>Routine Engine Visual — configurables en UI</td></tr>
      <tr><td><strong>Monitoreo</strong></td><td>Sin métricas del sistema</td><td>CPU / GPU / RAM / temperatura en tiempo real</td></tr>
      <tr><td><strong>Disponibilidad</strong></td><td>Necesita navegador abierto</td><td>Tray icon · siempre activo · auto-start</td></tr>
    </tbody>
  </table>

  <h3>Estado actual de PRTS Web — Base que se reutiliza</h3>
  <table>
    <thead><tr><th>Módulo</th><th>Estado</th><th>En Elfie Desktop</th></tr></thead>
    <tbody>
      <tr><td>Dashboard · Tareas · Semana · Proyectos · Insights</td><td><span class="b b-g">ACTIVO</span></td><td>Reutilizado en WebView sin cambios</td></tr>
      <tr><td>Gym · Dieta · Apuntes · Finanzas · Recordatorios</td><td><span class="b b-g">ACTIVO</span></td><td>Reutilizado en WebView sin cambios</td></tr>
      <tr><td>Capa IA: 4 Edge Functions + circuit breaker</td><td><span class="b b-g">ACTIVO</span></td><td>Reutilizada · Ollama la sustituye parcialmente</td></tr>
      <tr><td>Wake word "Dalia" · TTS · Voz push-to-talk</td><td><span class="b b-g">ACTIVO</span></td><td>Reemplazado por Whisper + Kokoro + Porcupine</td></tr>
      <tr><td>Alumnos · Contenido</td><td><span class="b b-y">PENDIENTE</span></td><td>Se implementan en Fase 5 del desktop</td></tr>
    </tbody>
  </table>
</div>

<!-- ══════════ 2 · MONOREPO ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">02</div><div class="sec-t">Estructura del Repositorio (Monorepo)</div></div>

  <div class="dec">
    <div class="dec-lbl">Decisión</div>
    <div class="dec-val">Mismo repositorio — carpeta elfie-desktop/ como módulo nuevo</div>
    <div class="dec-why">Tauri carga <code>../app</code> directamente como su WebView. Separar repos implicaría mantener dos copias del
    mismo frontend HTML/JS en sincronía. Las migraciones de Supabase son compartidas. Para un solo desarrollador/usuario
    es la arquitectura correcta.</div>
  </div>

  <div class="repo">
<span class="hl">mi-app-PRTS/</span>
├── <span class="hl">app/</span>                        <span class="cm">← frontend compartido (HTML/JS vanilla — sin cambios)</span>
│   ├── index.html              <span class="cm">← dashboard · tareas · semana · proyectos · insights</span>
│   ├── gym.html · dieta.html · apuntes.html · finanzas.html · recordatorios.html
│   ├── config.js               <span class="cm">← SUPABASE_URL · SUPABASE_ANON_KEY · GOOGLE_CLIENT_ID</span>
│   ├── styles.css · sw.js · manifest.json
│   └── ai/
│       ├── actions.js · voice.js · wakeword.js · gcal.js
│
├── <span class="hl">supabase/</span>                   <span class="cm">← BD compartida (sin cambios)</span>
│   ├── migrations/             <span class="cm">← 0001→0011 existentes · 0012→0015 nuevas (elfie)</span>
│   └── functions/              <span class="cm">← Edge Functions existentes reutilizadas</span>
│       └── _shared/ · generate-briefing/ · process-inbox/ · ...
│
├── <span class="new">elfie-desktop/</span>              <span class="new">← NUEVO: app Tauri 2.x</span>
│   ├── <span class="new">src-tauri/</span>              <span class="new">← Rust backend</span>
│   │   ├── Cargo.toml
│   │   ├── tauri.conf.json     <span class="cm">← distDir: "../../app" (apunta al frontend compartido)</span>
│   │   └── src/
│   │       ├── main.rs
│   │       ├── <span class="new">system_control.rs</span>   <span class="new">← open_app · volumen · archivos · portapapeles</span>
│   │       ├── <span class="new">monitor.rs</span>          <span class="new">← CPU/RAM (sysinfo) · GPU (nvml-wrapper)</span>
│   │       ├── <span class="new">audio.rs</span>            <span class="new">← Porcupine wake word · Whisper STT · TTS engines</span>
│   │       └── <span class="new">ai_router.rs</span>        <span class="new">← Ollama local · Anthropic fallback</span>
│   └── package.json            <span class="cm">← solo Tauri CLI ("@tauri-apps/cli")</span>
│
├── docs/
│   ├── Elfie_PRTS_Desktop_Planificacion_v2.0.pdf   <span class="new">← este documento</span>
│   └── Fase4_Arquitectura_IA.md · Fase5_WakeWord...
│
├── CLAUDE.md · PRODUCT.md · DESIGN.md
└── package.json                <span class="cm">← npm run dev (serve app/) · db:push · db:new</span></div>

  <div class="call call-ok">
    <div class="call-t">Tauri apuntando al frontend de PRTS</div>
    <p>En <code>elfie-desktop/src-tauri/tauri.conf.json</code>, la clave <code>"distDir": "../../app"</code>
    hace que el WebView cargue la misma carpeta que ya sirve Vercel. Cero duplicación de código frontend.</p>
  </div>
</div>

<!-- ══════════ 3 · WINDOWS 10 ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">03</div><div class="sec-t">Compatibilidad Windows 10</div></div>

  <div class="call call-warn">
    <div class="call-t">Contexto importante</div>
    <p>Windows 10 llegó a su fin de soporte el <strong>14 de octubre de 2025</strong>. A junio de 2026 ya no recibe
    parches de seguridad. Elfie Desktop puede desarrollarse y correrse en Windows 10, pero hay consideraciones
    que vale tener presentes.</p>
  </div>

  <h3>Qué funciona igual en Windows 10</h3>
  <div class="win10-grid">
    <div class="win10-card ok">
      <div class="win10-t">Tauri 2.x + WebView2</div>
      <div class="win10-b">Compatible. En Windows 10 WebView2 no siempre está preinstalado, pero Tauri puede empaquetarlo automáticamente con <code>webview2InstallMode = "embedBootstrapper"</code> en tauri.conf.json. Transparente para el usuario.</div>
    </div>
    <div class="win10-card ok">
      <div class="win10-t">Ollama + Whisper + Kokoro</div>
      <div class="win10-b">Todos soportan Windows 10 oficialmente. No dependen de APIs del SO — corren sobre CUDA y DirectX disponibles en Win10.</div>
    </div>
    <div class="win10-card ok">
      <div class="win10-t">Auto-start · Tray · Shortcuts</div>
      <div class="win10-b">Registro de Windows (auto-start), tray icon y global shortcuts funcionan exactamente igual en Windows 10 y 11.</div>
    </div>
    <div class="win10-card ok">
      <div class="win10-t">Notificaciones nativas</div>
      <div class="win10-b">Toast Notifications disponibles desde Windows 10 1809+. Tauri las usa por defecto sin configuración adicional.</div>
    </div>
    <div class="win10-card ok">
      <div class="win10-t">Rutas y LAUNCHERS existentes</div>
      <div class="win10-b">Las rutas en <code>actions.js</code> (<code>C:/Users/Sylft/...</code>) ya son rutas de Windows. Sin cambio al migrar el launcher a Tauri.</div>
    </div>
    <div class="win10-card ok">
      <div class="win10-t">Picovoice Porcupine</div>
      <div class="win10-b">SDK disponible para Windows 10. Requiere Visual C++ Redistributable (normalmente ya instalado).</div>
    </div>
  </div>

  <h3>Puntos a verificar antes de comprometerse</h3>
  <div class="win10-grid">
    <div class="win10-card warn">
      <div class="win10-t">Drivers RTX 5060 en Win10</div>
      <div class="win10-b">La RTX 5060 (Blackwell, 2025) es posterior al EOL de Win10. NVIDIA generalmente mantiene soporte de drivers, pero verificar que los drivers actuales de la tarjeta soporten CUDA en Windows 10 antes de asumir que Ollama/Whisper funcionan con GPU.</div>
    </div>
    <div class="win10-card risk">
      <div class="win10-t">Seguridad — SO sin parches</div>
      <div class="win10-b">Elfie Desktop maneja tokens de Supabase y OAuth de Google. Sin actualizaciones de seguridad del SO desde octubre 2025, existe riesgo real. Recomendable migrar a Windows 11 antes o durante Fase 4 (IA local).</div>
    </div>
  </div>

  <div class="call call-info">
    <div class="call-t">Recomendación</div>
    <p><strong>Desarrollar normalmente en Windows 10.</strong> El código no cambia entre versiones de Windows.
    Verificar drivers de la RTX 5060 antes de la Fase 3 (voz local). Planificar migración a Windows 11
    antes de la Fase 4 para aprovechar mejor el hardware y resolver el riesgo de seguridad.</p>
  </div>
</div>

<!-- ══════════ 4 · ARQUITECTURA ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">04</div><div class="sec-t">Arquitectura del Sistema</div></div>

  <h3>Hardware disponible y presupuesto de VRAM</h3>
  <div class="hw-grid">
    <div class="hw">
      <div class="hw-ico">⬛</div>
      <div class="hw-lbl">GPU</div>
      <div class="hw-val">RTX 5060 · 8 GB</div>
      <div class="hw-note">Whisper: ~1.5 GB (siempre)<br>LLM Mistral 7B Q4: ~4.5 GB (al procesar)<br>XTTS v2: ~2.5 GB (al sintetizar, ~2 s)<br>Peak máximo: ~7.5 GB</div>
    </div>
    <div class="hw">
      <div class="hw-ico">🔷</div>
      <div class="hw-lbl">RAM</div>
      <div class="hw-val">16 GB DDR4</div>
      <div class="hw-note">Tauri + frontend: ~200 MB<br>Ollama runtime: ~500 MB<br>Sistema + otras apps: ~8 GB<br>Disponible para Elfie: ~7 GB</div>
    </div>
    <div class="hw">
      <div class="hw-ico">🔴</div>
      <div class="hw-lbl">CPU</div>
      <div class="hw-val">Ryzen 5 5600G · 6C/12T</div>
      <div class="hw-note">Rust backend (Tauri): mínimo<br>Porcupine wake word: ~3% CPU<br>Piper TTS (fallback CPU): &lt;50 ms<br>LanceDB RAG queries: &lt;100 ms</div>
    </div>
  </div>

  <h3>Diagrama de sistema</h3>
  <div class="repo">
<span class="hl">┌─── ELFIE DESKTOP (Tauri 2.x) ───────────────────────────────────────────────────┐</span>
│                                                                                   │
│  <span class="hl">Frontend (WebView — app/ compartido)</span>        <span class="hl">Core Rust (Tauri IPC)</span>              │
│  ┌──────────────────────────────────┐      ┌──────────────────────────────┐       │
│  │ Módulos PRTS (sin cambios)        │      │ system_control.rs            │       │
│  │ + app/elfie/                      │◄────►│   open_app · volumen         │       │
│  │     personality.js               │  IPC │   archivos · portapapeles    │       │
│  │     voice_desktop.js             │      │                              │       │
│  │     routines.js  (nuevo)         │      │ monitor.rs                   │       │
│  │     rag.js       (nuevo)         │      │   sysinfo (CPU/RAM)          │       │
│  └──────────────────────────────────┘      │   nvml-wrapper (RTX 5060)    │       │
│                                            │                              │       │
│  <span class="hl">Atajos Globales (tauri-plugin-global-shortcut)</span>  audio.rs             │       │
│  Ctrl+Space → abrir captura            │   Porcupine (wake word)      │       │
│  Alt+E      → activar escucha          │   Whisper.cpp (STT)          │       │
│                                            │   Kokoro / Piper (TTS)       │       │
│  <span class="hl">RAG local (LanceDB)</span>                        │                              │       │
│  LanceDB en disco (~elfie-desktop/db/) │   ai_router.rs               │       │
│  Embeddings de Apuntes                 │   Ollama (local) ←→          │       │
│  Consultas semánticas por voz/texto    │   Anthropic (fallback)       │       │
│                                            └──────────────────────────────┘       │
<span class="hl">└─────────────────────────────────────────────────────────────────────────────────────┘</span>
            │
  <span class="hl">┌───────────────────────────────────────────────────────┐</span>
  │          SUPABASE (compartido con PRTS web)            │
  │  Tablas existentes (RLS) · Realtime websocket          │
  │  Nuevas: elfie_config · voice_profiles                 │
  │          system_actions · system_metrics · routines    │
  <span class="hl">└───────────────────────────────────────────────────────┘</span>
            │
  PRTS Web (Vercel) — misma BD · sync &lt;1 s bidireccional</div>
</div>

<!-- ══════════ 5 · MÓDULOS ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">05</div><div class="sec-t">Módulos del Sistema</div></div>

  <h3>Control del Sistema Operativo (Rust)</h3>
  <table>
    <thead><tr><th>Comando Tauri IPC</th><th>Función</th><th>Activación</th></tr></thead>
    <tbody>
      <tr><td><code>open_app</code></td><td>Lanza ejecutables por nombre; alias configurables en elfie_config</td><td>"Elfie, abre Discord"</td></tr>
      <tr><td><code>kill_process</code></td><td>Termina procesos por nombre o PID</td><td>"Elfie, cierra Steam"</td></tr>
      <tr><td><code>run_routine</code></td><td>Ejecuta secuencia del Routine Engine</td><td>"Elfie, modo estudio"</td></tr>
      <tr><td><code>set_volume</code></td><td>Volumen maestro del sistema (0–100)</td><td>"Elfie, sube el volumen a 60"</td></tr>
      <tr><td><code>mute_toggle</code></td><td>Silenciar/activar audio</td><td>"Elfie, silencia"</td></tr>
      <tr><td><code>clipboard_read/write</code></td><td>Leer o escribir el portapapeles</td><td>"Elfie, ¿qué tengo copiado?"</td></tr>
      <tr><td><code>open_folder</code></td><td>Abre carpeta en Explorador de Windows</td><td>"Elfie, abre mis proyectos"</td></tr>
      <tr><td><code>screenshot</code></td><td>Captura de pantalla → disco o clipboard</td><td>"Elfie, toma una captura"</td></tr>
      <tr><td><code>power_action</code></td><td>Apagar / reiniciar / suspender</td><td>"Elfie, suspende la computadora"</td></tr>
    </tbody>
  </table>

  <h3>Monitor de Recursos (crates: sysinfo + nvml-wrapper)</h3>
  <p>Emite datos cada 3 s al frontend vía eventos Tauri. El panel vive en el dashboard de Elfie y puede mostrarse como widget flotante.</p>
  <div class="call call-dark">
    <h4>Métricas disponibles</h4>
    <ul>
      <li>CPU (Ryzen 5 5600G): uso total y por núcleo · frecuencia actual · temperatura</li>
      <li>GPU (RTX 5060): % uso · VRAM usada/total (8 GB) · temperatura · potencia · ventilador</li>
      <li>RAM: usada / disponible / total (16 GB)</li>
      <li>Disco: espacio libre por partición</li>
      <li>Red: Mbps bajada y subida en tiempo real</li>
      <li>Procesos: top-10 por CPU y por RAM</li>
    </ul>
  </div>

  <h3>Personalidad de Elfie</h3>
  <table>
    <thead><tr><th>Perfil</th><th>Tono</th><th>TTS</th><th>Verbosidad</th></tr></thead>
    <tbody>
      <tr><td><strong>Profesional</strong> (default)</td><td>Directa, eficiente, sin rodeos</td><td>Voz neutra · velocidad 1.0</td><td>Concisa</td></tr>
      <tr><td><strong>Casual</strong></td><td>Informal, comentarios breves</td><td>Voz cálida · velocidad 1.05</td><td>Media</td></tr>
      <tr><td><strong>Silenciosa</strong></td><td>Solo confirmaciones de 1–2 palabras</td><td>TTS desactivado · solo texto</td><td>Mínima</td></tr>
      <tr><td><strong>Técnica</strong></td><td>Datos concretos, sin suavizar</td><td>Voz neutra · velocidad 0.95</td><td>Detallada</td></tr>
      <tr><td><strong>Nocturna</strong></td><td>Suave, volumen reducido automático</td><td>Voz suave · velocidad 0.9</td><td>Mínima</td></tr>
    </tbody>
  </table>
  <p>Persiste en <code>elfie_config.personality</code> (Supabase) — sincronizada entre desktop y web.</p>
</div>

<!-- ══════════ 6 · CAPA DE VOZ ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">06</div><div class="sec-t">Capa de Voz</div></div>

  <h3>STT — Whisper.cpp (reemplaza webkitSpeechRecognition)</h3>
  <table>
    <thead><tr><th>Característica</th><th>webkitSpeechRecognition (actual)</th><th>Whisper.cpp (desktop)</th></tr></thead>
    <tbody>
      <tr><td>Privacidad</td><td>Audio enviado a Google</td><td><span class="b b-g">100% local, sin Google</span></td></tr>
      <tr><td>Offline</td><td>Requiere internet</td><td><span class="b b-g">Funciona sin internet</span></td></tr>
      <tr><td>Precisión es-MX</td><td>Buena</td><td><span class="b b-g">Superior en español</span></td></tr>
      <tr><td>VRAM requerida</td><td>0 (cloud)</td><td>~1.5 GB (large-v3-turbo)</td></tr>
      <tr><td>Latencia</td><td>~500 ms</td><td>~300 ms (frase corta, GPU)</td></tr>
    </tbody>
  </table>

  <h3>TTS — Motores Locales (sin costo)</h3>
  <div class="vc-grid">
    <div class="vc rec">
      <div class="vc-name">Kokoro TTS <span class="b b-b">PRIMARIO</span></div>
      <div class="vc-tag">Local · 82M params · ONNX · GPU</div>
      <div class="vc-row"><span>Calidad</span><strong>Excelente</strong></div>
      <div class="vc-row"><span>Latencia</span><strong>&lt;100 ms (GPU)</strong></div>
      <div class="vc-row"><span>VRAM</span><strong>~0.5 GB</strong></div>
      <div class="vc-row"><span>Clonación</span><strong>No</strong></div>
    </div>
    <div class="vc">
      <div class="vc-name">Piper TTS <span class="b b-g">FALLBACK CPU</span></div>
      <div class="vc-tag">Local · CPU · Ultrarrápido</div>
      <div class="vc-row"><span>Calidad</span><strong>Buena</strong></div>
      <div class="vc-row"><span>Latencia</span><strong>&lt;50 ms (CPU)</strong></div>
      <div class="vc-row"><span>VRAM</span><strong>0 — solo CPU</strong></div>
      <div class="vc-row"><span>Uso</span><strong>Si GPU ocupada</strong></div>
    </div>
    <div class="vc">
      <div class="vc-name">XTTS v2 (Coqui) <span class="b b-p">CLONACIÓN</span></div>
      <div class="vc-tag">Local · Clona voz con 5 s de audio</div>
      <div class="vc-row"><span>Calidad</span><strong>Muy alta</strong></div>
      <div class="vc-row"><span>Latencia</span><strong>~500 ms (GPU)</strong></div>
      <div class="vc-row"><span>VRAM</span><strong>~2.5 GB</strong></div>
      <div class="vc-row"><span>Clonación</span><strong>Sí — cualquier voz</strong></div>
    </div>
    <div class="vc">
      <div class="vc-name">Fish Speech <span class="b b-b">ALTERNATIVA</span></div>
      <div class="vc-tag">Local · Estado del arte</div>
      <div class="vc-row"><span>Calidad</span><strong>Estado del arte</strong></div>
      <div class="vc-row"><span>Latencia</span><strong>~200 ms (GPU)</strong></div>
      <div class="vc-row"><span>VRAM</span><strong>~4 GB</strong></div>
      <div class="vc-row"><span>Clonación</span><strong>Sí</strong></div>
    </div>
  </div>

  <h3>TTS — Fallback Cloud</h3>
  <div class="vc-grid">
    <div class="vc cld">
      <div class="vc-name">edge-tts: es-MX-DaliaNeural <span class="b b-g">GRATUITO</span></div>
      <div class="vc-tag">Microsoft Edge TTS · Sin API key</div>
      <div class="vc-row"><span>Costo</span><strong>Gratuito (500k chars/mes)</strong></div>
      <div class="vc-row"><span>Latencia</span><strong>~200 ms</strong></div>
      <div class="vc-row"><span>Nota</span><strong>La voz se llama "Dalia" — misma wake word</strong></div>
    </div>
    <div class="vc cld">
      <div class="vc-name">ElevenLabs</div>
      <div class="vc-tag">Cloud · Máxima calidad · Clonación</div>
      <div class="vc-row"><span>Costo</span><strong>$5–22/mes</strong></div>
      <div class="vc-row"><span>Calidad</span><strong>La mejor del mercado</strong></div>
      <div class="vc-row"><span>Uso</span><strong>Opcional — momentos especiales</strong></div>
    </div>
  </div>

  <div class="call call-dark">
    <h4>Stack de voz — Estrategia en capas</h4>
    <p><strong>1 · Kokoro (local GPU)</strong> — respuestas cotidianas · &lt;100 ms · $0</p>
    <p><strong>2 · Piper (local CPU)</strong> — fallback si GPU saturada · &lt;50 ms · $0</p>
    <p><strong>3 · edge-tts es-MX-DaliaNeural (cloud gratuita)</strong> — si modelos locales no están cargados</p>
    <p><strong>4 · XTTS v2 (local)</strong> — perfil de voz clonada para identidad de Elfie · Fase 6</p>
  </div>
</div>

<!-- ══════════ 7 · IA LOCAL ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">07</div><div class="sec-t">IA Local con Ollama (RTX 5060)</div></div>

  <h3>Modelos recomendados para 8 GB VRAM</h3>
  <div class="mod-grid">
    <div class="mod">
      <div class="mod-name">Phi-3.5 Mini · Q4_K_M</div>
      <div class="mod-row"><span>VRAM</span><strong>~2.5 GB</strong></div>
      <div class="mod-row"><span>Velocidad</span><strong>~120 tok/s</strong></div>
      <div class="mod-row"><span>Calidad</span><strong>Muy buena</strong></div>
      <div class="mod-row"><span>Uso ideal</span><strong>Router · comandos rápidos · respuestas simples</strong></div>
    </div>
    <div class="mod">
      <div class="mod-name">Qwen2.5 7B · Q4_K_M</div>
      <div class="mod-row"><span>VRAM</span><strong>~4.5 GB</strong></div>
      <div class="mod-row"><span>Velocidad</span><strong>~50 tok/s</strong></div>
      <div class="mod-row"><span>Calidad</span><strong>Excelente en español</strong></div>
      <div class="mod-row"><span>Uso ideal</span><strong>Inbox · clasificación · razonamiento</strong></div>
    </div>
    <div class="mod">
      <div class="mod-name">Llama 3.1 8B · Q4_K_M</div>
      <div class="mod-row"><span>VRAM</span><strong>~5.0 GB</strong></div>
      <div class="mod-row"><span>Velocidad</span><strong>~40 tok/s</strong></div>
      <div class="mod-row"><span>Calidad</span><strong>Excelente</strong></div>
      <div class="mod-row"><span>Uso ideal</span><strong>Conversación profunda · intent ask</strong></div>
    </div>
    <div class="mod">
      <div class="mod-name">Mistral 7B v0.3 · Q4_K_M</div>
      <div class="mod-row"><span>VRAM</span><strong>~4.5 GB</strong></div>
      <div class="mod-row"><span>Velocidad</span><strong>~50 tok/s</strong></div>
      <div class="mod-row"><span>Calidad</span><strong>Excelente</strong></div>
      <div class="mod-row"><span>Uso ideal</span><strong>Clasificación de texto · análisis</strong></div>
    </div>
  </div>

  <h3>Router Híbrido — Local + Nube</h3>
  <div class="repo">
<span class="hl">Elfie recibe comando (voz o texto)</span>
         │
         ▼
<span class="hl">¿Patrón local sin LLM?</span> ──SÍ──► Resolver en cliente (0 ms · $0)
         │ NO                          hora · fecha · saludo · navegar · abrir apps · clima
         ▼
<span class="hl">¿Ollama disponible?</span> ──SÍ──► Phi-3.5 Mini / Qwen2.5 7B local (~300–800 ms · $0)
         │ NO                    inbox · clasificación · preguntas · comandos complejos
         ▼
<span class="hl">¿Anthropic API disponible?</span> ──SÍ──► Claude Haiku 4.5 (~600 ms · ~$0.001/llamada)
         │ NO                            briefing diario · insights (calidad máxima)
         ▼
<span class="hl">Modo degradado</span> ── respuesta determinista / manual (sin IA)</div>

  <div class="call call-ok">
    <div class="call-t">Ahorro estimado con IA local</div>
    <p>PRTS web gasta Anthropic API en: clasificación inbox (~5 llamadas/día) + comandos de voz (~10/día) + briefing (1/día).
    Con Ollama local, las clasificaciones y comandos simples cuestan $0. <strong>Reducción estimada: 70–80% del gasto mensual.</strong>
    Solo briefings e insights quedan en Claude API por calidad de contexto amplio.</p>
  </div>
</div>

<!-- ══════════ 8 · BASE DE DATOS ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">08</div><div class="sec-t">Base de Datos Compartida</div></div>

  <p>La base de datos Supabase existente es la fuente de verdad única. Elfie Desktop usa las mismas credenciales,
  el mismo RLS y el mismo cliente JavaScript de PRTS. Se añaden 5 migraciones nuevas.</p>

  <h3>Nuevas Tablas (migraciones 0012–0016)</h3>
  <div class="code">
<span class="cm">-- 0012: Configuración de Elfie (personalidad, voz, modelo local)</span>
<span class="kw">CREATE TABLE</span> elfie_config (
  user_id          <span class="kw">uuid DEFAULT</span> auth.uid() <span class="kw">PRIMARY KEY</span>,
  personality      <span class="kw">text DEFAULT</span> <span class="st">'profesional'</span>,
  voice_engine     <span class="kw">text DEFAULT</span> <span class="st">'kokoro'</span>,    <span class="cm">-- kokoro|piper|xtts|edge|elevenlabs</span>
  voice_name       <span class="kw">text DEFAULT</span> <span class="st">'es-MX-DaliaNeural'</span>,
  voice_speed      <span class="kw">float DEFAULT</span> <span class="num">1.0</span>,
  verbosity        <span class="kw">text DEFAULT</span> <span class="st">'concisa'</span>,
  tts_enabled      <span class="kw">bool DEFAULT true</span>,
  local_llm_model  <span class="kw">text DEFAULT</span> <span class="st">'phi3.5'</span>,
  updated_at       <span class="kw">timestamptz DEFAULT now</span>()
);

<span class="cm">-- 0013: Perfiles de voz clonados (XTTS v2 / Fish Speech)</span>
<span class="kw">CREATE TABLE</span> voice_profiles (
  id                   <span class="kw">uuid DEFAULT</span> gen_random_uuid() <span class="kw">PRIMARY KEY</span>,
  user_id              <span class="kw">uuid DEFAULT</span> auth.uid(),
  name                 <span class="kw">text NOT NULL</span>,
  engine               <span class="kw">text NOT NULL</span>,
  reference_audio_url  <span class="kw">text</span>,
  config               <span class="kw">jsonb</span>,
  is_active            <span class="kw">bool DEFAULT false</span>,
  created_at           <span class="kw">timestamptz DEFAULT now</span>()
);

<span class="cm">-- 0014: Log de acciones del sistema operativo</span>
<span class="kw">CREATE TABLE</span> system_actions (
  id           <span class="kw">uuid DEFAULT</span> gen_random_uuid() <span class="kw">PRIMARY KEY</span>,
  user_id      <span class="kw">uuid DEFAULT</span> auth.uid(),
  action_type  <span class="kw">text NOT NULL</span>,
  payload      <span class="kw">jsonb</span>,
  executed_at  <span class="kw">timestamptz DEFAULT now</span>()
);

<span class="cm">-- 0015: Métricas del sistema (historial para gráficas)</span>
<span class="kw">CREATE TABLE</span> system_metrics (
  id               <span class="kw">uuid DEFAULT</span> gen_random_uuid() <span class="kw">PRIMARY KEY</span>,
  user_id          <span class="kw">uuid DEFAULT</span> auth.uid(),
  cpu_percent      <span class="kw">float</span>, ram_used_gb <span class="kw">float</span>,
  gpu_percent      <span class="kw">float</span>, gpu_vram_used_gb <span class="kw">float</span>,
  gpu_temp_c       <span class="kw">float</span>, gpu_power_w <span class="kw">float</span>,
  recorded_at      <span class="kw">timestamptz DEFAULT now</span>()
);

<span class="cm">-- 0016: Rutinas configurables (Routine Engine Visual)</span>
<span class="kw">CREATE TABLE</span> routines (
  id               <span class="kw">uuid DEFAULT</span> gen_random_uuid() <span class="kw">PRIMARY KEY</span>,
  user_id          <span class="kw">uuid DEFAULT</span> auth.uid(),
  name             <span class="kw">text NOT NULL</span>,
  trigger_phrase   <span class="kw">text</span>,        <span class="cm">-- "modo estudio"</span>
  shortcut         <span class="kw">text</span>,        <span class="cm">-- "Ctrl+Shift+E"</span>
  steps            <span class="kw">jsonb NOT NULL</span>, <span class="cm">-- [{action, params, delay_ms}]</span>
  is_active        <span class="kw">bool DEFAULT true</span>,
  created_at       <span class="kw">timestamptz DEFAULT now</span>()
);</div>

  <h3>Sincronización en Tiempo Real (Supabase Realtime)</h3>
  <table>
    <thead><tr><th>Canal</th><th>Dirección</th><th>Efecto en Elfie</th></tr></thead>
    <tbody>
      <tr><td><code>tasks</code></td><td>Web ↔ Desktop</td><td>Tarea creada en web → aparece en Elfie en &lt;1 s</td></tr>
      <tr><td><code>daily_briefings</code></td><td>Web → Desktop</td><td>Briefing pre-generado → notificación nativa</td></tr>
      <tr><td><code>reminders</code></td><td>Web ↔ Desktop</td><td>Recordatorio próximo → alerta de sistema</td></tr>
      <tr><td><code>inbox_entries</code></td><td>Web ↔ Desktop</td><td>Capturas procesadas en cualquier cliente</td></tr>
      <tr><td><code>routines</code></td><td>Desktop → Web</td><td>Nueva rutina creada en desktop (solo aplica en desktop)</td></tr>
    </tbody>
  </table>
</div>

<!-- ══════════ 9 · FASES ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">09</div><div class="sec-t">Fases de Desarrollo (Restructuradas)</div></div>

  <div class="phase-grid">
    <div class="ph">
      <div class="ph-head">
        <div class="ph-n">F0</div>
        <div class="ph-name">Setup Base</div>
        <div class="ph-dur">~1 sem</div>
      </div>
      <ul>
        <li>Crear <code>elfie-desktop/</code> en el repo</li>
        <li>Inicializar Tauri 2.x</li>
        <li><code>distDir: "../../app"</code> → PRTS en WebView</li>
        <li>WebView2 embebido (Windows 10 compat.)</li>
        <li>Conexión Supabase reutilizada</li>
        <li>Verificar que los 10 módulos corren en WebView</li>
      </ul>
    </div>
    <div class="ph">
      <div class="ph-head">
        <div class="ph-n">F1</div>
        <div class="ph-name">Core Desktop</div>
        <div class="ph-dur">~2 sem</div>
      </div>
      <ul>
        <li>Tray icon + menú contextual</li>
        <li>Auto-start en Windows (registro)</li>
        <li>Notificaciones nativas de Windows</li>
        <li>Supabase Realtime (sync live)</li>
        <li><strong>tauri-plugin-global-shortcut</strong> <span class="tag tag-g">INFRAESTRUCTURA</span></li>
        <li>Ctrl+Space = captura · Alt+E = voz</li>
      </ul>
    </div>
    <div class="ph">
      <div class="ph-head">
        <div class="ph-n">F2</div>
        <div class="ph-name">Control del Sistema</div>
        <div class="ph-dur">~2 sem</div>
      </div>
      <ul>
        <li>Launcher de aplicaciones (<code>open_app</code>)</li>
        <li>Control de volumen nativo</li>
        <li>Monitor CPU/GPU/RAM (NVML)</li>
        <li>Gestión de archivos y carpetas</li>
        <li>Portapapeles (leer/escribir)</li>
        <li>Screenshot nativo</li>
      </ul>
    </div>
    <div class="ph">
      <div class="ph-head">
        <div class="ph-n">F3</div>
        <div class="ph-name">Voz Local</div>
        <div class="ph-dur">~2 sem</div>
      </div>
      <ul>
        <li>Whisper.cpp STT (sin Google)</li>
        <li>Kokoro TTS + Piper fallback</li>
        <li>Picovoice Porcupine wake word</li>
        <li>Flujo: wake → Whisper → router → TTS</li>
        <li>Indicador visual en tray (escucha/habla)</li>
        <li>Verificar drivers RTX 5060 en Windows</li>
      </ul>
    </div>
    <div class="ph">
      <div class="ph-head">
        <div class="ph-n">F4</div>
        <div class="ph-name">IA Local</div>
        <div class="ph-dur">~2–3 sem</div>
      </div>
      <ul>
        <li>Instalar Ollama + modelos base</li>
        <li>Router híbrido local → Anthropic</li>
        <li>Personalidad Elfie configurable</li>
        <li>Panel de personalidad en la UI</li>
        <li>Perfiles de voz (múltiples motores)</li>
        <li><em>Migración recomendada a Win11 aquí</em></li>
      </ul>
    </div>
    <div class="ph">
      <div class="ph-head">
        <div class="ph-n">F5</div>
        <div class="ph-name">Módulos Nuevos</div>
        <div class="ph-dur">~2–3 sem</div>
      </div>
      <ul>
        <li><strong>Routine Engine Visual</strong> <span class="tag tag-g">ALTA PRIORIDAD</span></li>
        <li>Panel de monitor de sistema completo</li>
        <li>Historial de métricas en gráficas</li>
        <li>Módulo Alumnos (tabla + UI)</li>
        <li>Módulo Contenido (planificador)</li>
      </ul>
    </div>
    <div class="ph">
      <div class="ph-head">
        <div class="ph-n">F6</div>
        <div class="ph-name">RAG + Obsidian + Voz</div>
        <div class="ph-dur">~2 sem</div>
      </div>
      <ul>
        <li><strong>RAG local (LanceDB)</strong> para Apuntes <span class="tag">semántico</span></li>
        <li>Embeddings de notas al crear/editar</li>
        <li>"Elfie, ¿qué anotamos sobre X?"</li>
        <li>XTTS v2 clonación de voz</li>
        <li>Obsidian export <em>(si lo usás activamente)</em></li>
      </ul>
    </div>
    <div class="ph">
      <div class="ph-head">
        <div class="ph-n">F7</div>
        <div class="ph-name">Distribución</div>
        <div class="ph-dur">~1 sem</div>
      </div>
      <ul>
        <li>Installer .msi / .exe (WebView2 embebido)</li>
        <li>Script de setup (Ollama + modelos)</li>
        <li>Documentación de configuración inicial</li>
        <li>Firma del ejecutable (opcional)</li>
      </ul>
    </div>
  </div>

  <div class="call call-info">
    <div class="call-t">Tiempo total estimado: ~13–15 semanas</div>
    <p>Fases 0–3 entregan la app funcional básica con voz local en ~7 semanas.
    Fases 4–7 añaden IA local, Routine Engine, RAG y distribución.
    Misma filosofía de PRTS: uso real después de cada fase antes de avanzar.</p>
  </div>
</div>

<!-- ══════════ 10 · MEJORAS TÉCNICAS ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">10</div><div class="sec-t">Mejoras Técnicas Internas</div></div>

  <h3>RAG Local con LanceDB</h3>
  <div class="call call-info">
    <div class="call-t">Qué resuelve</div>
    <p>El módulo Apuntes de PRTS tiene notas por materia con 5 campos (conceptos, fórmulas, dudas, conexiones, resumen).
    Hoy solo se puede buscar por texto exacto. Con RAG, Elfie puede responder preguntas semánticas:
    <em>"¿Qué anotamos sobre complejidad algorítmica?"</em> aunque no uses esas palabras exactas.</p>
  </div>

  <h4>Alcance claro</h4>
  <p><strong>Para qué sirve el RAG en PRTS:</strong> exclusivamente para el módulo <strong>Apuntes</strong> —
  el resto de los módulos ya son datos estructurados en Supabase que el LLM puede consultar directamente
  con SQL. RAG no aporta nada que una query SQL no haga mejor para tareas, gym o finanzas.</p>

  <h4>Implementación</h4>
  <div class="code">
<span class="cm">// Flujo RAG para Apuntes (LanceDB local)</span>
<span class="cm">// 1. Al crear/editar una nota → generar embedding</span>
<span class="kw">const</span> embedding = <span class="kw">await</span> ollama.embeddings({
  model: <span class="st">'nomic-embed-text'</span>,  <span class="cm">// modelo de embeddings, ~270MB VRAM</span>
  prompt: nota.conceptos + <span class="st">' '</span> + nota.resumen
});
<span class="cm">// 2. Guardar en LanceDB (elfie-desktop/db/apuntes.lance)</span>
<span class="kw">await</span> table.add([{ id: nota.id, materia: nota.materia,
                    vector: embedding.embedding, text: nota.resumen }]);

<span class="cm">// 3. Al preguntar por voz → buscar similares → prompt al LLM</span>
<span class="kw">const</span> resultados = <span class="kw">await</span> table.search(queryEmbedding).limit(<span class="num">3</span>).execute();
<span class="kw">const</span> contexto = resultados.map(r => r.text).join(<span class="st">'\n'</span>);
<span class="cm">// → LLM recibe contexto + pregunta → responde basado en TUS notas</span></div>

  <p>LanceDB es un vector store embebido (como SQLite pero para vectores). No requiere servidor ni Docker.
  Los embeddings se generan con Ollama local (<code>nomic-embed-text</code>, ~270 MB VRAM) y viven en disco.
  <strong>Privacidad total: tus notas nunca salen de la computadora.</strong></p>

  <div class="call call-warn">
    <div class="call-t">Cuándo implementarlo</div>
    <p>RAG tiene sentido cuando hay suficiente volumen de notas (20+ apuntes distintos). Implementarlo en Fase 6 da tiempo
    para acumular contenido real y validar que el caso de uso efectivamente ocurre en el uso diario.</p>
  </div>

  <hr class="divider">

  <h3>tauri-plugin-global-shortcut <span class="b b-g">FASE 1 — INFRAESTRUCTURA</span></h3>
  <div class="call call-ok">
    <div class="call-t">Por qué va en Fase 1, no en Fase 5</div>
    <p>Sin atajos globales, para interactuar con Elfie tenés que cambiar de ventana y hacer clic en la app.
    Eso destruye el propósito de un asistente de escritorio. Los atajos globales son la diferencia entre
    un asistente que interrumpe el flujo y uno que lo complementa.</p>
  </div>

  <div class="code">
<span class="cm">// src-tauri/src/main.rs</span>
<span class="kw">use</span> tauri_plugin_global_shortcut::{Code, Modifiers, ShortcutState};

app.plugin(tauri_plugin_global_shortcut::Builder::new().build())?;

<span class="cm">// Registrar al iniciar la app</span>
let app_handle = app.handle().clone();
app.global_shortcut().on_shortcuts(
  [<span class="st">"Ctrl+Space"</span>, <span class="st">"Alt+E"</span>],
  <span class="kw">move</span> |_app, shortcut, event| {
    <span class="kw">if</span> event.state() == ShortcutState::Pressed {
      <span class="kw">match</span> shortcut.key_string() {
        <span class="st">"ctrl+space"</span> => app_handle.emit(<span class="st">"elfie:open-capture"</span>, ()),
        <span class="st">"alt+e"</span>     => app_handle.emit(<span class="st">"elfie:start-voice"</span>, ()),
        _ => {}
      }
    }
  }
)?;</div>

  <table>
    <thead><tr><th>Atajo</th><th>Acción</th><th>Funciona desde</th></tr></thead>
    <tbody>
      <tr><td><code>Ctrl+Space</code></td><td>Abrir input de captura de Elfie</td><td>Cualquier app activa</td></tr>
      <tr><td><code>Alt+E</code></td><td>Activar escucha de voz (push-to-talk)</td><td>Cualquier app activa</td></tr>
      <tr><td><code>Ctrl+Shift+R</code></td><td>Ejecutar rutina rápida (configurable)</td><td>Cualquier app activa</td></tr>
      <tr><td><em>Personalizable</em></td><td>Cualquier acción de Elfie</td><td>Cualquier app activa</td></tr>
    </tbody>
  </table>
</div>

<!-- ══════════ 11 · EXPANSIONES ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">11</div><div class="sec-t">Expansiones de Capacidad</div></div>

  <h3>Routine Engine Visual <span class="b b-g">ALTA PRIORIDAD — Fase 5</span></h3>
  <div class="call call-info">
    <div class="call-t">Qué resuelve</div>
    <p>Las rutinas de inicio en PRTS web están hardcodeadas en <code>actions.js</code>:
    <em>"Buen día" abre Discord + Spotify + YouTube escalonados</em>. Para cambiar qué abre, hay que editar el archivo.
    El Routine Engine Visual convierte esas rutinas en datos configurables desde la UI, sin tocar código.</p>
  </div>

  <h4>Interfaz de creación de rutinas</h4>
  <div class="code">
<span class="hl">Panel "Mis Rutinas" en Elfie Desktop</span>

[+ Nueva rutina]

Nombre: <span class="st">"Modo estudio"</span>
Activar con voz: <span class="st">"modo estudio"</span>
Atajo de teclado: <span class="st">Ctrl+Shift+E</span>

Pasos:
  1. Abrir VS Code              [delay: 500ms]
  2. Abrir Spotify → playlist foco [delay: 800ms]
  3. Silenciar Discord          [delay: 300ms]
  4. Volumen del sistema → 40%  [delay: 0ms]
  5. Abrir PRTS → vista Tareas  [delay: 600ms]

[Probar rutina]  [Guardar]  [Eliminar]

──────────────────────────────────
Rutinas guardadas:
  ● Modo estudio         Ctrl+Shift+E  · "modo estudio"
  ● Modo entreno         Ctrl+Shift+G  · "modo gym"
  ● Modo clase Wolves    Ctrl+Shift+W  · "modo clase"
  ● Buen día             —             · "buen día" / "buenos días"</div>

  <h4>Modelo de datos</h4>
  <div class="code">
<span class="cm">-- Tabla routines (migración 0016)</span>
steps: <span class="kw">jsonb</span> = [
  { <span class="st">"action"</span>: <span class="st">"open_app"</span>,     <span class="st">"params"</span>: { <span class="st">"name"</span>: <span class="st">"vscode"</span> },        <span class="st">"delay_ms"</span>: <span class="num">500</span> },
  { <span class="st">"action"</span>: <span class="st">"spotify_preset"</span>, <span class="st">"params"</span>: { <span class="st">"preset"</span>: <span class="st">"foco"</span> },      <span class="st">"delay_ms"</span>: <span class="num">800</span> },
  { <span class="st">"action"</span>: <span class="st">"set_volume"</span>,    <span class="st">"params"</span>: { <span class="st">"level"</span>: <span class="num">40</span> },             <span class="st">"delay_ms"</span>: <span class="num">300</span> },
  { <span class="st">"action"</span>: <span class="st">"navigate"</span>,     <span class="st">"params"</span>: { <span class="st">"view"</span>: <span class="st">"tareas"</span> },        <span class="st">"delay_ms"</span>: <span class="num">600</span> }
]</div>

  <p>El ejecutor de rutinas es una extensión del <code>aplicarAccion()</code> existente en <code>actions.js</code> —
  ya sabe abrir apps, navegar vistas y controlar Spotify. Solo se añade la capa de secuenciación con delays.</p>

  <hr class="divider">

  <h3>Integración con Obsidian <span class="b b-y">CONDICIONAL — solo si usás Obsidian</span></h3>

  <div class="call call-warn">
    <div class="call-t">Evaluación honesta</div>
    <p>Esta integración solo tiene valor si Obsidian ya es parte de tu flujo diario de notas. Si no lo usás,
    implementarla solo crea dependencia sin beneficio. Evaluá primero si el RAG local (Fase 6) resuelve
    la búsqueda semántica que necesitás — probablemente sí.</p>
  </div>

  <h4>Si se implementa: sincronización PRTS → Obsidian</h4>
  <table>
    <thead><tr><th>Dirección</th><th>Complejidad</th><th>Cómo</th></tr></thead>
    <tbody>
      <tr><td><strong>PRTS → Obsidian</strong> (export)</td><td><span class="b b-g">BAJA</span></td><td>Tauri escribe archivos .md al vault de Obsidian cuando se crea/edita una nota en PRTS. Formato: frontmatter YAML + contenido.</td></tr>
      <tr><td><strong>Obsidian → PRTS</strong> (sync bidireccional)</td><td><span class="b b-r">ALTA</span></td><td>Requiere watcher de archivos (<code>tauri-plugin-fs-watch</code>) + parseo de Markdown. Conflictos posibles si se edita en ambos lados. No recomendado.</td></tr>
    </tbody>
  </table>

  <div class="code">
<span class="cm">// Export de nota a .md (Tauri Rust → disco)</span>
<span class="kw">fn</span> export_to_obsidian(nota: &amp;Nota, vault_path: &amp;str) {
  <span class="kw">let</span> md = format!(<span class="st">"---\nid: {}\nmateria: {}\nfecha: {}\n---\n\n## Conceptos\n{}\n\n## Resumen\n{}"</span>,
    nota.id, nota.materia, nota.created_at, nota.conceptos, nota.resumen);
  std::fs::write(format!(<span class="st">"{}/{}/{}.md"</span>, vault_path, nota.materia, nota.title), md);
}</div>
</div>

<!-- ══════════ 12 · INTEGRACIONES ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">12</div><div class="sec-t">Integraciones y Visión a Largo Plazo</div></div>

  <h3>Integraciones con Apps ya en uso</h3>
  <div class="sug-grid">
    <div class="sug hi">
      <div class="sug-t">Discord RPC + Webhook</div>
      <div class="sug-b">Cambiar estado "Ahora jugando", enviar mensajes a canales definidos, alertar cuando llega un mensaje prioritario. "Elfie, dile a #wolves que llego en 10 min". Discord ya está en LAUNCHERS.</div>
    </div>
    <div class="sug hi">
      <div class="sug-t">Spotify Web API real</div>
      <div class="sug-b">Reemplazar los presets estáticos actuales por la API real: reproducir cualquier playlist/canción por nombre, ver canción actual, control de reproducción. El GOOGLE_CLIENT_ID en config.js ya muestra el patrón OAuth a seguir.</div>
    </div>
    <div class="sug md">
      <div class="sug-t">OBS Studio WebSocket</div>
      <div class="sug-b">Control de escenas, iniciar/detener grabación. "Elfie, empieza la grabación", "Elfie, cambia a escena de juego". Útil para contenido/streams.</div>
    </div>
    <div class="sug md">
      <div class="sug-t">Google Calendar bidireccional</div>
      <div class="sug-b">Actualmente PRTS solo escribe a Calendar (recordatorios). Elfie Desktop puede leer los eventos del día en el briefing sin abrir el navegador. Sincronización en ambas vías.</div>
    </div>
    <div class="sug md">
      <div class="sug-t">Time Tracker automático</div>
      <div class="sug-b">Detectar qué ventana tiene el foco (GetForegroundWindow en Windows) y registrar tiempo activo por app. Elfie analiza: "Pasaste 3 h en VS Code hoy." Sin servicios externos, datos locales.</div>
    </div>
    <div class="sug ex">
      <div class="sug-t">Screenshot + descripción IA</div>
      <div class="sug-b">Elfie captura pantalla y el LLM multimodal (llama3.2-vision vía Ollama) la describe o extrae texto/código. Útil para agregar contexto visual al inbox sin teclear.</div>
    </div>
  </div>

  <h3>Visión a Largo Plazo</h3>
  <div class="sug-grid">
    <div class="sug ex">
      <div class="sug-t">Módulo Alumnos (Wolves + LevelUp)</div>
      <div class="sug-b">Registro de asistencia, progreso por alumno, calendario de sesiones, notas de clase. Elfie sugiere qué repasar en la próxima sesión basándose en el historial. Se implementa en Fase 5.</div>
    </div>
    <div class="sug ex">
      <div class="sug-t">Monitor de progreso TecNM</div>
      <div class="sug-b">Módulo Escuela: fechas de exámenes, proyectos, calificaciones. Elfie alerta cuando se acerca un parcial y conecta con los Apuntes de esa materia automáticamente.</div>
    </div>
    <div class="sug ex">
      <div class="sug-t">Fine-tuning con datos propios</div>
      <div class="sug-b">Con 6+ meses de datos en Supabase (tareas, inbox, gym, dieta), hacer fine-tuning de un modelo pequeño (Phi-3.5, Qwen2.5) para que entienda el vocabulario y contexto de Sylft sin prompts largos.</div>
    </div>
    <div class="sug ex">
      <div class="sug-t">API local de Elfie</div>
      <div class="sug-b">Exponer un endpoint REST local (localhost:XXXX) para que scripts, VS Code y otras herramientas le hablen a Elfie directamente sin abrir la app. "curl localhost:7300/elfie?q=modo+estudio"</div>
    </div>
  </div>

  <hr class="divider" style="margin-top:20pt">

  <h3>Resumen de Prioridades</h3>
  <table>
    <thead><tr><th>Mejora / Expansión</th><th>Prioridad</th><th>Fase</th><th>Justificación</th></tr></thead>
    <tbody>
      <tr><td><strong>tauri-plugin-global-shortcut</strong></td><td><span class="b b-g">ALTA</span></td><td>Fase 1</td><td>Infraestructura básica del asistente de escritorio</td></tr>
      <tr><td><strong>Routine Engine Visual</strong></td><td><span class="b b-g">ALTA</span></td><td>Fase 5</td><td>Caso de uso diario real, sustituye código hardcodeado</td></tr>
      <tr><td><strong>RAG local (LanceDB)</strong></td><td><span class="b b-b">MEDIA</span></td><td>Fase 6</td><td>Válido solo para Apuntes, requiere volumen acumulado</td></tr>
      <tr><td><strong>Integración Obsidian</strong></td><td><span class="b b-y">CONDICIONAL</span></td><td>Fase 6</td><td>Solo si Obsidian ya es parte del flujo diario</td></tr>
      <tr><td>Spotify Web API real</td><td><span class="b b-b">MEDIA</span></td><td>Post F5</td><td>Mejora sobre presets estáticos actuales</td></tr>
      <tr><td>Time Tracker automático</td><td><span class="b b-b">MEDIA</span></td><td>Post F5</td><td>Datos de productividad sin servicios externos</td></tr>
      <tr><td>Fine-tuning propio</td><td><span class="b b-p">FUTURA</span></td><td>Post F7</td><td>Requiere 6+ meses de datos acumulados</td></tr>
    </tbody>
  </table>

  <hr class="divider" style="margin-top:20pt">
  <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:16pt">
    <div>
      <div style="font-family:'Courier New',monospace;font-size:8pt;color:#4a90b8;letter-spacing:1px;text-transform:uppercase;">Elfie · PRTS Desktop Edition</div>
      <div style="font-family:'Courier New',monospace;font-size:7.5pt;color:#8a9ab0;margin-top:2pt;">Planificación v2.0 · Junio 2026 · Uso personal exclusivo · Sylft</div>
    </div>
    <div style="font-family:Georgia,serif;font-size:32pt;font-weight:700;color:#eef4fa;">Elfie</div>
  </div>
</div>

</body>
</html>"""

import os, sys

output_path = "/home/user/mi-app-PRTS/docs/Elfie_PRTS_Desktop_Planificacion_v2.0.pdf"

try:
    from weasyprint import HTML
    print("Generando PDF con WeasyPrint...")
    HTML(string=HTML_CONTENT, base_url="/").write_pdf(output_path)
    size = os.path.getsize(output_path)
    print(f"PDF generado: {output_path}")
    print(f"Tamaño: {size / 1024:.1f} KB")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

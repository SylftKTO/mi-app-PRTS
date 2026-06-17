#!/usr/bin/env python3
"""Genera el documento de planificación Elfie-PRTS como PDF."""

HTML_CONTENT = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 10.5pt;
    line-height: 1.6;
    color: #1a1a2e;
    background: #ffffff;
  }

  /* ── PORTADA ── */
  .cover {
    background: #0d1b2a;
    color: #ffffff;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
    padding: 60pt 60pt;
    page-break-after: always;
    position: relative;
  }
  .cover-eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 8pt;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #4a90b8;
    margin-bottom: 24pt;
  }
  .cover-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 48pt;
    font-weight: 900;
    line-height: 1.1;
    color: #ffffff;
    margin-bottom: 8pt;
  }
  .cover-subtitle {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 20pt;
    font-weight: 400;
    color: #4a90b8;
    margin-bottom: 36pt;
  }
  .cover-desc {
    font-size: 11pt;
    color: #a0b4c8;
    max-width: 400pt;
    line-height: 1.7;
    margin-bottom: 48pt;
  }
  .cover-meta {
    font-family: 'Space Mono', monospace;
    font-size: 8pt;
    color: #4a90b8;
    letter-spacing: 1px;
    border-top: 1px solid #1e3a52;
    padding-top: 16pt;
    width: 100%;
  }
  .cover-meta span { margin-right: 24pt; }
  .cover-line {
    position: absolute;
    right: 60pt;
    top: 60pt;
    bottom: 60pt;
    width: 3pt;
    background: linear-gradient(to bottom, #4a90b8, transparent);
  }

  /* ── TABLA DE CONTENIDOS ── */
  .toc-page {
    padding: 50pt 60pt;
    page-break-after: always;
  }
  .toc-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 24pt;
    color: #0d1b2a;
    margin-bottom: 24pt;
    border-bottom: 2pt solid #4a90b8;
    padding-bottom: 8pt;
  }
  .toc-item {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 5pt 0;
    border-bottom: 1pt dotted #dde3ea;
    font-size: 10pt;
  }
  .toc-item.section { font-weight: 600; color: #0d1b2a; margin-top: 8pt; }
  .toc-item.sub { color: #4a6280; padding-left: 16pt; font-size: 9.5pt; }
  .toc-page-num { color: #4a90b8; font-family: 'Space Mono', monospace; font-size: 9pt; }

  /* ── PÁGINAS DE CONTENIDO ── */
  .page {
    padding: 44pt 60pt;
    page-break-after: always;
  }
  .page:last-child { page-break-after: avoid; }

  /* Encabezado de sección */
  .section-header {
    display: flex;
    align-items: center;
    margin-bottom: 24pt;
    gap: 12pt;
  }
  .section-num {
    font-family: 'Space Mono', monospace;
    font-size: 9pt;
    color: #4a90b8;
    background: #eef4fa;
    padding: 4pt 8pt;
    border-radius: 3pt;
    letter-spacing: 1px;
    white-space: nowrap;
  }
  .section-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 22pt;
    font-weight: 700;
    color: #0d1b2a;
  }

  /* Subtítulos */
  h3 {
    font-family: 'Inter', sans-serif;
    font-size: 12pt;
    font-weight: 600;
    color: #0d1b2a;
    margin: 20pt 0 8pt 0;
    padding-left: 10pt;
    border-left: 3pt solid #4a90b8;
  }
  h4 {
    font-family: 'Space Mono', monospace;
    font-size: 9pt;
    font-weight: 700;
    color: #4a90b8;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 14pt 0 6pt 0;
  }

  p { margin-bottom: 8pt; color: #2c3e50; }

  /* ── CALLOUT BOXES ── */
  .callout {
    border-radius: 6pt;
    padding: 14pt 18pt;
    margin: 14pt 0;
  }
  .callout-info { background: #eef4fa; border-left: 4pt solid #4a90b8; }
  .callout-warn { background: #fef9e7; border-left: 4pt solid #f39c12; }
  .callout-ok   { background: #eafaf1; border-left: 4pt solid #27ae60; }
  .callout-dark { background: #0d1b2a; color: #c8daea; border-left: 4pt solid #4a90b8; }
  .callout-dark h4 { color: #4a90b8; }
  .callout-dark p, .callout-dark li { color: #a0b4c8; }
  .callout-title {
    font-family: 'Space Mono', monospace;
    font-size: 8.5pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6pt;
    color: #4a90b8;
  }

  /* ── TABLAS ── */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 9.5pt;
  }
  thead tr { background: #0d1b2a; color: #ffffff; }
  thead th {
    padding: 8pt 10pt;
    text-align: left;
    font-family: 'Space Mono', monospace;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
  tbody tr:nth-child(even) { background: #f4f7fb; }
  tbody tr:nth-child(odd)  { background: #ffffff; }
  tbody td {
    padding: 7pt 10pt;
    border-bottom: 1pt solid #e0e8f0;
    vertical-align: top;
  }
  .badge {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 7.5pt;
    padding: 2pt 6pt;
    border-radius: 3pt;
    font-weight: 700;
  }
  .badge-green  { background: #d5f5e3; color: #1e8449; }
  .badge-blue   { background: #d6eaf8; color: #1a5276; }
  .badge-yellow { background: #fdebd0; color: #784212; }
  .badge-red    { background: #fadbd8; color: #78281f; }
  .badge-gray   { background: #eaecee; color: #515a5a; }

  /* ── CÓDIGO / BLOQUES TÉCNICOS ── */
  .code-block {
    background: #0d1b2a;
    color: #a8d8f0;
    font-family: 'Space Mono', monospace;
    font-size: 8pt;
    padding: 14pt 16pt;
    border-radius: 6pt;
    margin: 10pt 0;
    line-height: 1.7;
    overflow: hidden;
  }
  .code-block .kw  { color: #4a90b8; }
  .code-block .cm  { color: #516070; font-style: italic; }
  .code-block .st  { color: #7ecb7a; }
  .code-block .num { color: #e8b84b; }
  code {
    font-family: 'Space Mono', monospace;
    font-size: 8.5pt;
    background: #eef4fa;
    color: #1a5276;
    padding: 1pt 4pt;
    border-radius: 2pt;
  }

  /* ── LISTAS ── */
  ul, ol { padding-left: 18pt; margin-bottom: 8pt; }
  li { margin-bottom: 4pt; color: #2c3e50; }
  li strong { color: #0d1b2a; }

  /* ── TARJETAS DE FASE ── */
  .phase-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12pt;
    margin: 12pt 0;
  }
  .phase-card {
    border: 1.5pt solid #dde3ea;
    border-radius: 8pt;
    padding: 14pt;
    background: #fafcff;
  }
  .phase-card-head {
    display: flex;
    align-items: center;
    gap: 8pt;
    margin-bottom: 8pt;
  }
  .phase-num {
    font-family: 'Space Mono', monospace;
    font-size: 8pt;
    font-weight: 700;
    background: #0d1b2a;
    color: #4a90b8;
    padding: 3pt 7pt;
    border-radius: 4pt;
  }
  .phase-name { font-weight: 600; font-size: 10.5pt; color: #0d1b2a; }
  .phase-duration {
    font-family: 'Space Mono', monospace;
    font-size: 7.5pt;
    color: #4a90b8;
    margin-left: auto;
  }
  .phase-card ul { font-size: 9pt; }

  /* ── HARDWARE CARDS ── */
  .hw-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10pt;
    margin: 10pt 0;
  }
  .hw-card {
    background: #0d1b2a;
    border-radius: 8pt;
    padding: 14pt;
    text-align: center;
  }
  .hw-icon { font-size: 20pt; margin-bottom: 6pt; }
  .hw-name { font-family: 'Space Mono', monospace; font-size: 7.5pt; color: #4a90b8; letter-spacing: 1px; text-transform: uppercase; }
  .hw-spec { font-size: 11pt; font-weight: 600; color: #ffffff; margin: 4pt 0; }
  .hw-note { font-size: 8pt; color: #6a8aaa; }

  /* ── VOZ CARDS ── */
  .voice-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10pt;
    margin: 12pt 0;
  }
  .voice-card {
    border-radius: 8pt;
    padding: 14pt;
    border: 1.5pt solid #dde3ea;
  }
  .voice-card.recommended { border-color: #4a90b8; background: #eef4fa; }
  .voice-card.cloud { border-color: #e0b84a; background: #fef9e7; }
  .voice-name { font-weight: 700; font-size: 11pt; color: #0d1b2a; margin-bottom: 4pt; }
  .voice-tag { font-family: 'Space Mono', monospace; font-size: 7pt; text-transform: uppercase; letter-spacing: 1px; }
  .voice-row { display: flex; justify-content: space-between; font-size: 9pt; margin-top: 6pt; color: #4a6280; }
  .voice-row strong { color: #0d1b2a; }

  /* ── ARQUITECTURA ASCII ── */
  .arch-block {
    background: #0d1b2a;
    color: #c8daea;
    font-family: 'Space Mono', monospace;
    font-size: 7.8pt;
    line-height: 1.65;
    padding: 16pt 18pt;
    border-radius: 8pt;
    margin: 12pt 0;
  }
  .arch-block .hl  { color: #4a90b8; font-weight: 700; }
  .arch-block .ok  { color: #5dbb6d; }
  .arch-block .dim { color: #405060; }

  /* ── SEPARADOR ── */
  .divider {
    border: none;
    border-top: 1pt solid #dde3ea;
    margin: 16pt 0;
  }

  /* ── FOOTER de página ── */
  @page {
    margin: 0;
    size: A4;
    @bottom-center {
      content: counter(page);
      font-family: 'Space Mono', monospace;
      font-size: 8pt;
      color: #8a9ab0;
    }
  }

  /* ── SUGERENCIAS ── */
  .sug-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10pt;
    margin: 12pt 0;
  }
  .sug-card {
    border-radius: 8pt;
    padding: 12pt 14pt;
    border: 1pt solid #dde3ea;
    background: #fafcff;
  }
  .sug-card.high  { border-left: 4pt solid #27ae60; }
  .sug-card.med   { border-left: 4pt solid #4a90b8; }
  .sug-card.ext   { border-left: 4pt solid #9b59b6; }
  .sug-card.hard  { border-left: 4pt solid #e74c3c; }
  .sug-title { font-weight: 700; font-size: 10pt; margin-bottom: 4pt; color: #0d1b2a; }
  .sug-body  { font-size: 9pt; color: #4a6280; line-height: 1.5; }

  /* ── DECISION MATRIX ── */
  .decision-box {
    background: #f4f7fb;
    border-radius: 8pt;
    padding: 16pt;
    margin: 12pt 0;
    border: 1pt solid #dde3ea;
  }
  .decision-label {
    font-family: 'Space Mono', monospace;
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #4a90b8;
    margin-bottom: 6pt;
    font-weight: 700;
  }
  .decision-value { font-size: 14pt; font-weight: 700; color: #0d1b2a; margin-bottom: 4pt; }
  .decision-why { font-size: 9pt; color: #4a6280; }
</style>
</head>
<body>

<!-- ═══════════════════════════════════════ PORTADA ═══════════════════════════════════════ -->
<div class="cover">
  <div class="cover-line"></div>
  <div class="cover-eyebrow">Documento de Planificación · v1.0 · Junio 2026</div>
  <div class="cover-title">Elfie</div>
  <div class="cover-subtitle">PRTS Desktop Edition</div>
  <div class="cover-desc">
    Evolución de PRTS a una aplicación de escritorio nativa con control
    del sistema operativo, procesamiento de IA local y personalidad
    configurable. Desarrollada para uso exclusivo de Sylft, con base
    de datos compartida con la versión web.
  </div>
  <div class="cover-meta">
    <span>PROPIETARIO: SYLFT</span>
    <span>IA: ELFIE</span>
    <span>PLATAFORMA: WINDOWS 11</span>
    <span>HARDWARE: RTX 5060 · 16 GB RAM · RYZEN 5 5600G</span>
  </div>
</div>

<!-- ═══════════════════════════════════════ TABLA DE CONTENIDOS ═══════════════════════════════════════ -->
<div class="toc-page">
  <div class="toc-title">Contenido</div>

  <div class="toc-item section"><span>1 · Visión del Proyecto</span><span class="toc-page-num">3</span></div>
  <div class="toc-item sub"><span>Estado actual de PRTS web</span><span class="toc-page-num">3</span></div>
  <div class="toc-item sub"><span>Qué cambia con Elfie Desktop</span><span class="toc-page-num">3</span></div>

  <div class="toc-item section"><span>2 · Decisiones de Arquitectura</span><span class="toc-page-num">4</span></div>
  <div class="toc-item sub"><span>Framework de escritorio: Tauri 2.x</span><span class="toc-page-num">4</span></div>
  <div class="toc-item sub"><span>Diagrama de sistema completo</span><span class="toc-page-num">4</span></div>
  <div class="toc-item sub"><span>Hardware disponible y uso</span><span class="toc-page-num">4</span></div>

  <div class="toc-item section"><span>3 · Módulos del Sistema</span><span class="toc-page-num">5</span></div>
  <div class="toc-item sub"><span>Control del sistema operativo</span><span class="toc-page-num">5</span></div>
  <div class="toc-item sub"><span>Monitor de recursos en tiempo real</span><span class="toc-page-num">5</span></div>
  <div class="toc-item sub"><span>Dashboard sincronizado con PRTS web</span><span class="toc-page-num">5</span></div>
  <div class="toc-item sub"><span>Personalidad de Elfie</span><span class="toc-page-num">5</span></div>

  <div class="toc-item section"><span>4 · Capa de Voz</span><span class="toc-page-num">6</span></div>
  <div class="toc-item sub"><span>STT local (Whisper.cpp)</span><span class="toc-page-num">6</span></div>
  <div class="toc-item sub"><span>Opciones de TTS locales</span><span class="toc-page-num">6</span></div>
  <div class="toc-item sub"><span>Opciones de TTS en la nube</span><span class="toc-page-num">7</span></div>
  <div class="toc-item sub"><span>Stack de voz recomendado</span><span class="toc-page-num">7</span></div>

  <div class="toc-item section"><span>5 · IA Local (RTX 5060)</span><span class="toc-page-num">8</span></div>
  <div class="toc-item sub"><span>Ollama + modelos recomendados</span><span class="toc-page-num">8</span></div>
  <div class="toc-item sub"><span>Estrategia híbrida local + nube</span><span class="toc-page-num">8</span></div>

  <div class="toc-item section"><span>6 · Base de Datos Compartida</span><span class="toc-page-num">9</span></div>
  <div class="toc-item sub"><span>Nuevas tablas de Supabase</span><span class="toc-page-num">9</span></div>
  <div class="toc-item sub"><span>Sincronización en tiempo real</span><span class="toc-page-num">9</span></div>

  <div class="toc-item section"><span>7 · Fases de Desarrollo</span><span class="toc-page-num">10</span></div>

  <div class="toc-item section"><span>8 · Sugerencias de Desarrollo y Expansión</span><span class="toc-page-num">11</span></div>
  <div class="toc-item sub"><span>Mejoras técnicas internas</span><span class="toc-page-num">11</span></div>
  <div class="toc-item sub"><span>Expansiones de capacidad</span><span class="toc-page-num">12</span></div>
  <div class="toc-item sub"><span>Integraciones externas</span><span class="toc-page-num">12</span></div>
  <div class="toc-item sub"><span>Visión a largo plazo</span><span class="toc-page-num">13</span></div>
</div>

<!-- ═══════════════════════════════════════ 1 · VISIÓN ═══════════════════════════════════════ -->
<div class="page">
  <div class="section-header">
    <div class="section-num">01</div>
    <div class="section-title">Visión del Proyecto</div>
  </div>

  <div class="callout callout-info">
    <div class="callout-title">Propósito</div>
    <p>Elfie-PRTS Desktop no reemplaza la versión web — la extiende. Mientras PRTS web es accesible desde cualquier dispositivo,
    Elfie Desktop vive permanentemente en la máquina de Sylft, tiene acceso nativo al sistema operativo, procesa IA localmente
    y funciona como asistente ambiental de escritorio con personalidad propia.</p>
  </div>

  <h3>Estado actual de PRTS Web — Qué ya existe</h3>
  <table>
    <thead><tr><th>Área</th><th>Estado</th><th>Detalle</th></tr></thead>
    <tbody>
      <tr><td><strong>Frontend</strong></td><td><span class="badge badge-green">COMPLETO</span></td><td>HTML/JS vanilla, 10 módulos funcionales, PWA</td></tr>
      <tr><td><strong>Base de datos</strong></td><td><span class="badge badge-green">COMPLETO</span></td><td>Supabase Postgres, 11 migraciones, RLS completo, 27+ tablas</td></tr>
      <tr><td><strong>Capa IA (Anthropic)</strong></td><td><span class="badge badge-green">COMPLETO</span></td><td>4 Edge Functions: briefing, inbox, comandos, insights</td></tr>
      <tr><td><strong>Voz web</strong></td><td><span class="badge badge-green">COMPLETO</span></td><td>webkitSpeechRecognition + speechSynthesis (es-MX)</td></tr>
      <tr><td><strong>Wake word "Dalia"</strong></td><td><span class="badge badge-green">COMPLETO</span></td><td>Escucha continua en desktop Chromium</td></tr>
      <tr><td><strong>Google Calendar</strong></td><td><span class="badge badge-green">COMPLETO</span></td><td>Recordatorios → notificación al celular</td></tr>
      <tr><td><strong>Alumnos / Contenido</strong></td><td><span class="badge badge-yellow">PENDIENTE</span></td><td>Solo nodos en el mapa, sin HTML ni tablas</td></tr>
    </tbody>
  </table>

  <h3>Qué cambia y añade Elfie Desktop</h3>
  <table>
    <thead><tr><th>Capacidad</th><th>PRTS Web</th><th>Elfie Desktop</th></tr></thead>
    <tbody>
      <tr><td><strong>Control del SO</strong></td><td>Solo deep links (protocol handlers)</td><td>Nativo: procesos, ventanas, volumen, archivos</td></tr>
      <tr><td><strong>STT</strong></td><td>Google (cloud, privacidad limitada)</td><td>Whisper.cpp local, sin Google, funciona offline</td></tr>
      <tr><td><strong>Wake word</strong></td><td>webkitSpeechRecognition continuo</td><td>Picovoice Porcupine on-device (real nivel C)</td></tr>
      <tr><td><strong>TTS / Voz de Elfie</strong></td><td>speechSynthesis del navegador</td><td>Kokoro / XTTS v2 local, clonación de voz</td></tr>
      <tr><td><strong>LLM</strong></td><td>Solo Anthropic API (costo por llamada)</td><td>Ollama local (RTX 5060) + Anthropic fallback</td></tr>
      <tr><td><strong>Memoria contextual</strong></td><td>Sin memoria entre sesiones</td><td>RAG local (ChromaDB / LanceDB)</td></tr>
      <tr><td><strong>Disponibilidad</strong></td><td>Necesita navegador abierto</td><td>Tray icon, siempre activo, auto-start</td></tr>
      <tr><td><strong>Monitoreo</strong></td><td>Sin métricas del sistema</td><td>CPU/GPU/RAM/temperatura en tiempo real</td></tr>
      <tr><td><strong>Personalidad</strong></td><td>Respuestas funcionales</td><td>Perfiles configurables, nombre Elfie, tono propio</td></tr>
    </tbody>
  </table>
</div>

<!-- ═══════════════════════════════════════ 2 · ARQUITECTURA ═══════════════════════════════════════ -->
<div class="page">
  <div class="section-header">
    <div class="section-num">02</div>
    <div class="section-title">Decisiones de Arquitectura</div>
  </div>

  <div class="decision-box">
    <div class="decision-label">Framework de Escritorio</div>
    <div class="decision-value">Tauri 2.x (Rust + WebView)</div>
    <div class="decision-why">Elegido sobre Electron por ser 15× más liviano (~8 MB vs ~150 MB), backend en Rust para operaciones nativas de alto rendimiento,
    y porque el frontend puede reutilizar <strong>exactamente</strong> el código HTML/JS vanilla de PRTS. La identidad visual migra sin reescritura.</div>
  </div>

  <div class="arch-block">
<span class="hl">┌─── ELFIE DESKTOP (Tauri 2.x) ───────────────────────────────────────────────┐</span>
│                                                                                 │
│  <span class="hl">Frontend (WebView)</span>                    <span class="hl">Core Rust (Tauri Commands)</span>              │
│  ┌─────────────────────────┐           ┌──────────────────────────────┐         │
│  │ app/index.html          │           │ system_control.rs            │         │
│  │ app/gym.html            │◄──IPC────►│   open_app(), list_procs()   │         │
│  │ app/dieta.html          │           │   set_volume(), clipboard()  │         │
│  │ ... (módulos PRTS)      │           │                              │         │
│  │                         │           │ monitor.rs                   │         │
│  │ app/elfie/              │           │   cpu/gpu/ram en tiempo real │         │
│  │   personality.js        │           │   NVML para RTX 5060         │         │
│  │   voice.js (nueva)      │           │                              │         │
│  │   dashboard_sync.js     │           │ audio.rs                     │         │
│  └─────────────────────────┘           │   Porcupine (wake word)      │         │
│                                        │   Whisper.cpp (STT)          │         │
│                                        │   Kokoro/XTTS TTS engine     │         │
│                                        │                              │         │
│                                        │ ai_router.rs                 │         │
│                                        │   Ollama local API           │         │
│                                        │   Anthropic fallback         │         │
│                                        └──────────────────────────────┘         │
│                                                     │                           │
│                          ┌──────────────────────────┴────────────────────┐      │
│                          │           SUPABASE (compartido con web)        │      │
│                          │  mismas tablas · RLS · Realtime websocket      │      │
│                          │  + nuevas: elfie_config, voice_profiles,       │      │
│                          │    system_actions, system_metrics               │      │
│                          └────────────────────────────────────────────────┘      │
<span class="hl">└─────────────────────────────────────────────────────────────────────────────────┘</span>
                                         │
                    <span class="hl">┌────────────────────▼────────────────────┐</span>
                    │      PRTS Web (Vercel) — misma BD        │
                    │  Cambios en Elfie → reflejados en web    │
                    │  Cambios en web → Elfie notifica         │
                    <span class="hl">└─────────────────────────────────────────┘</span></div>

  <h3>Hardware disponible y uso estratégico</h3>
  <div class="hw-grid">
    <div class="hw-card">
      <div class="hw-icon">⬛</div>
      <div class="hw-name">GPU</div>
      <div class="hw-spec">RTX 5060 · 8 GB VRAM</div>
      <div class="hw-note">LLM local (hasta 7B Q4), Whisper large-v3-turbo, XTTS v2 · Deja ~3GB libres para el sistema</div>
    </div>
    <div class="hw-card">
      <div class="hw-icon">🔷</div>
      <div class="hw-name">RAM</div>
      <div class="hw-spec">16 GB DDR4</div>
      <div class="hw-note">Elfie + Ollama + sistema: presupuesto ~6 GB para la app; 10 GB para el SO y otras aplicaciones</div>
    </div>
    <div class="hw-card">
      <div class="hw-icon">🔴</div>
      <div class="hw-name">CPU</div>
      <div class="hw-spec">Ryzen 5 5600G · 6C/12T</div>
      <div class="hw-note">Tauri Rust backend + Piper TTS (CPU) como fallback; Porcupine wake word en CPU dedicado</div>
    </div>
  </div>

  <div class="callout callout-warn">
    <div class="callout-title">Gestión de VRAM (RTX 5060 · 8 GB)</div>
    <p><strong>Presupuesto de VRAM sugerido:</strong> LLM Mistral 7B Q4 ~4.5 GB · Whisper large-v3-turbo ~1.5 GB · XTTS v2 ~2.5 GB.
    No corren todos simultáneamente. El router prioriza: si hay comando en curso, el LLM toma ~5 GB; el STT siempre activo (~1.5 GB);
    el TTS solo se carga al responder (~2.5 GB durante ~2 s). Total peak: ~5 GB. Pico máximo ocasional: ~7.5 GB.</p>
  </div>
</div>

<!-- ═══════════════════════════════════════ 3 · MÓDULOS ═══════════════════════════════════════ -->
<div class="page">
  <div class="section-header">
    <div class="section-num">03</div>
    <div class="section-title">Módulos del Sistema</div>
  </div>

  <h3>Control del Sistema Operativo</h3>
  <p>Implementado en Rust (<code>system_control.rs</code>), expuesto al frontend vía comandos Tauri IPC.</p>
  <table>
    <thead><tr><th>Comando</th><th>Descripción</th><th>Ejemplo de uso por voz</th></tr></thead>
    <tbody>
      <tr><td><code>open_app</code></td><td>Lanza ejecutables por nombre o ruta. Alias configurables en <code>elfie_config</code></td><td>"Elfie, abre Discord"</td></tr>
      <tr><td><code>kill_process</code></td><td>Termina procesos por nombre o PID</td><td>"Elfie, cierra Steam"</td></tr>
      <tr><td><code>list_windows</code></td><td>Lista ventanas abiertas para cambio de foco</td><td>"Elfie, ¿qué tengo abierto?"</td></tr>
      <tr><td><code>set_volume</code></td><td>Volumen maestro del sistema (0-100)</td><td>"Elfie, sube el volumen a 60"</td></tr>
      <tr><td><code>mute_toggle</code></td><td>Silenciar/activar audio</td><td>"Elfie, silencia"</td></tr>
      <tr><td><code>clipboard_read</code></td><td>Lee el portapapeles actual</td><td>"Elfie, ¿qué tengo copiado?"</td></tr>
      <tr><td><code>clipboard_write</code></td><td>Escribe en el portapapeles</td><td>Usado internamente por acciones</td></tr>
      <tr><td><code>open_folder</code></td><td>Abre carpeta en el Explorador de Windows</td><td>"Elfie, abre mis proyectos"</td></tr>
      <tr><td><code>screenshot</code></td><td>Captura de pantalla → guarda en disco o clipboard</td><td>"Elfie, toma una captura"</td></tr>
      <tr><td><code>power_action</code></td><td>Apagar / reiniciar / suspender</td><td>"Elfie, suspende la computadora"</td></tr>
      <tr><td><code>run_routine</code></td><td>Secuencia de acciones predefinida</td><td>"Elfie, modo trabajo"</td></tr>
    </tbody>
  </table>

  <h3>Monitor de Recursos en Tiempo Real</h3>
  <p>Usa la crate <code>sysinfo</code> (CPU/RAM) y <code>nvml-wrapper</code> (GPU NVIDIA) en Rust. Los datos se emiten cada 3 segundos
  al frontend vía eventos Tauri.</p>
  <div class="callout callout-dark">
    <h4>Métricas disponibles</h4>
    <ul>
      <li>CPU: porcentaje de uso por núcleo + total · frecuencia actual · temperatura</li>
      <li>GPU RTX 5060: % de uso · VRAM usada/total · temperatura · potencia consumida · velocidad del ventilador</li>
      <li>RAM: usada / disponible / total (16 GB)</li>
      <li>Disco: espacio libre por partición</li>
      <li>Red: Mbps de bajada y subida en tiempo real</li>
      <li>Procesos: top-10 por consumo de CPU y de RAM</li>
    </ul>
  </div>

  <h3>Personalidad de Elfie</h3>
  <p>La personalidad es configurable y se persiste en la tabla <code>elfie_config</code> de Supabase, sincronizada entre escritorio y web.</p>
  <table>
    <thead><tr><th>Perfil</th><th>Tono</th><th>TTS</th><th>Verbosidad</th></tr></thead>
    <tbody>
      <tr><td><strong>Profesional</strong> (default)</td><td>Directa, eficiente, sin rodeos</td><td>Voz neutra, velocidad 1.0</td><td>Concisa</td></tr>
      <tr><td><strong>Casual</strong></td><td>Informal, puede hacer comentarios breves</td><td>Voz más cálida, velocidad 1.05</td><td>Media</td></tr>
      <tr><td><strong>Silenciosa</strong></td><td>Mínima: solo confirmaciones de 1-2 palabras</td><td>TTS desactivado, solo texto</td><td>Mínima</td></tr>
      <tr><td><strong>Técnica</strong></td><td>Datos concretos, métricas, sin suavizar</td><td>Voz neutra, velocidad 0.95</td><td>Detallada</td></tr>
      <tr><td><strong>Nocturna</strong></td><td>Más suave, volumen reducido automáticamente</td><td>Voz suave, velocidad 0.9</td><td>Mínima</td></tr>
    </tbody>
  </table>

  <h3>Dashboard Sincronizado</h3>
  <div class="callout callout-ok">
    <div class="callout-title">Sincronización bidireccional via Supabase Realtime</div>
    <p>Elfie Desktop se suscribe a los canales Realtime de Supabase (<code>tasks</code>, <code>daily_briefings</code>, <code>reminders</code>, <code>inbox_entries</code>).
    Cualquier cambio desde la web se refleja en el escritorio en &lt;1 segundo, y viceversa. No hay polling ni refrescos manuales.</p>
  </div>
</div>

<!-- ═══════════════════════════════════════ 4 · CAPA DE VOZ ═══════════════════════════════════════ -->
<div class="page">
  <div class="section-header">
    <div class="section-num">04</div>
    <div class="section-title">Capa de Voz</div>
  </div>

  <h3>STT Local — Whisper.cpp</h3>
  <p>Reemplaza <code>webkitSpeechRecognition</code> (dependía de Google, requería navegador abierto). Con Whisper.cpp:</p>
  <ul>
    <li>El audio <strong>nunca sale de la computadora</strong> — privacidad total</li>
    <li>Funciona <strong>sin internet</strong></li>
    <li>Precisión superior en <strong>español mexicano</strong>, especialmente con vocabulario técnico/gym/dieta</li>
    <li>Modelo <code>large-v3-turbo</code>: 1.6 GB VRAM, transcripción en ~300 ms para frases cortas</li>
    <li>Integración en Tauri vía crate <code>whisper-rs</code> o sidecar Python</li>
  </ul>

  <h3>TTS Local (sin costo, aprovecha RTX 5060)</h3>
  <div class="voice-grid">
    <div class="voice-card recommended">
      <div class="voice-name">Kokoro TTS <span class="badge badge-blue">RECOMENDADO</span></div>
      <div class="voice-tag">Local · 82M params · ONNX</div>
      <div class="voice-row"><span>Calidad</span><strong>Excelente</strong></div>
      <div class="voice-row"><span>Latencia</span><strong>&lt;100 ms (GPU)</strong></div>
      <div class="voice-row"><span>VRAM</span><strong>~0.5 GB</strong></div>
      <div class="voice-row"><span>es-MX</span><strong>Sí</strong></div>
      <div class="voice-row"><span>Costo</span><strong>Gratuito</strong></div>
    </div>
    <div class="voice-card">
      <div class="voice-name">XTTS v2 (Coqui)</div>
      <div class="voice-tag">Local · Clonación de voz</div>
      <div class="voice-row"><span>Calidad</span><strong>Muy alta</strong></div>
      <div class="voice-row"><span>Latencia</span><strong>~500 ms (GPU)</strong></div>
      <div class="voice-row"><span>VRAM</span><strong>~2.5 GB</strong></div>
      <div class="voice-row"><span>Clonación</span><strong>Sí, 5 s de referencia</strong></div>
      <div class="voice-row"><span>Costo</span><strong>Gratuito</strong></div>
    </div>
    <div class="voice-card">
      <div class="voice-name">Piper TTS</div>
      <div class="voice-tag">Local · CPU · Ultrarrápido</div>
      <div class="voice-row"><span>Calidad</span><strong>Buena</strong></div>
      <div class="voice-row"><span>Latencia</span><strong>&lt;50 ms (CPU)</strong></div>
      <div class="voice-row"><span>VRAM</span><strong>0 (solo CPU)</strong></div>
      <div class="voice-row"><span>es-MX</span><strong>Modelos disponibles</strong></div>
      <div class="voice-row"><span>Costo</span><strong>Gratuito</strong></div>
    </div>
    <div class="voice-card">
      <div class="voice-name">Fish Speech</div>
      <div class="voice-tag">Local · Estado del arte</div>
      <div class="voice-row"><span>Calidad</span><strong>Estado del arte</strong></div>
      <div class="voice-row"><span>Latencia</span><strong>~200 ms (GPU)</strong></div>
      <div class="voice-row"><span>VRAM</span><strong>~4 GB</strong></div>
      <div class="voice-row"><span>Clonación</span><strong>Sí</strong></div>
      <div class="voice-row"><span>Costo</span><strong>Gratuito</strong></div>
    </div>
  </div>

  <h3>TTS en la Nube (costo variable, máxima calidad)</h3>
  <div class="voice-grid">
    <div class="voice-card cloud">
      <div class="voice-name">Microsoft Edge TTS <span class="badge badge-green">GRATUITO</span></div>
      <div class="voice-tag">Cloud · edge-tts · Sin API key</div>
      <div class="voice-row"><span>Voz es-MX</span><strong>es-MX-DaliaNeural ★</strong></div>
      <div class="voice-row"><span>Latencia</span><strong>~200 ms</strong></div>
      <div class="voice-row"><span>Costo</span><strong>Gratuito (500k chars/mes)</strong></div>
      <div class="voice-row"><span>Nota</span><strong>La voz se llama "Dalia" — encaja perfecto con la wake word</strong></div>
    </div>
    <div class="voice-card cloud">
      <div class="voice-name">ElevenLabs</div>
      <div class="voice-tag">Cloud · Máxima calidad</div>
      <div class="voice-row"><span>Calidad</span><strong>La mejor del mercado</strong></div>
      <div class="voice-row"><span>Latencia</span><strong>~300 ms</strong></div>
      <div class="voice-row"><span>Clonación</span><strong>Sí (plan Creador)</strong></div>
      <div class="voice-row"><span>Costo</span><strong>$5–22/mes según uso</strong></div>
    </div>
    <div class="voice-card cloud">
      <div class="voice-name">OpenAI TTS</div>
      <div class="voice-tag">Cloud · Voces naturales</div>
      <div class="voice-row"><span>Voces</span><strong>alloy, echo, nova, shimmer…</strong></div>
      <div class="voice-row"><span>Latencia</span><strong>~500 ms</strong></div>
      <div class="voice-row"><span>Costo</span><strong>$15/1M caracteres</strong></div>
      <div class="voice-row"><span>es-MX</span><strong>Sí (multilingüe)</strong></div>
    </div>
    <div class="voice-card cloud">
      <div class="voice-name">Azure Cognitive TTS</div>
      <div class="voice-tag">Cloud · Microsoft</div>
      <div class="voice-row"><span>Voces es-MX</span><strong>es-MX-DaliaNeural (Neural)</strong></div>
      <div class="voice-row"><span>Costo</span><strong>~$4/1M chars (Neural)</strong></div>
      <div class="voice-row"><span>SSML</span><strong>Sí — control de tono, pausa, énfasis</strong></div>
      <div class="voice-row"><span>Streaming</span><strong>Sí — respuesta progresiva</strong></div>
    </div>
  </div>

  <h3>Stack de Voz Recomendado</h3>
  <div class="callout callout-dark">
    <h4>Estrategia en capas (prioridad descendente)</h4>
    <p><strong>1 · Kokoro TTS (local, GPU)</strong> — respuestas cotidianas, &lt;100 ms, sin costo</p>
    <p><strong>2 · Piper TTS (local, CPU)</strong> — fallback si la GPU está saturada, &lt;50 ms en CPU</p>
    <p><strong>3 · edge-tts es-MX-DaliaNeural (cloud gratuita)</strong> — si los modelos locales no están cargados</p>
    <p><strong>4 · ElevenLabs / XTTS v2 (opcional)</strong> — voz clonada para momentos de mayor presencia</p>
    <p style="margin-top:8pt;color:#4a90b8;font-size:9pt;">La elección de motor se persiste en <code>elfie_config.voice_engine</code> y es intercambiable en tiempo de ejecución desde el panel de configuración.</p>
  </div>
</div>

<!-- ═══════════════════════════════════════ 5 · IA LOCAL ═══════════════════════════════════════ -->
<div class="page">
  <div class="section-header">
    <div class="section-num">05</div>
    <div class="section-title">IA Local (RTX 5060 · 8 GB VRAM)</div>
  </div>

  <div class="callout callout-info">
    <div class="callout-title">Herramienta: Ollama</div>
    <p>Ollama actúa como runtime local de LLMs. Expone una API REST compatible con OpenAI en <code>localhost:11434</code>,
    por lo que el código del router existente (que ya llama a un endpoint REST) cambia mínimamente para soportar el modo local.</p>
  </div>

  <h3>Modelos para RTX 5060 (8 GB VRAM)</h3>
  <table>
    <thead><tr><th>Modelo</th><th>Cuantización</th><th>VRAM</th><th>Velocidad</th><th>Calidad</th><th>Uso ideal en Elfie</th></tr></thead>
    <tbody>
      <tr><td><strong>Phi-3.5 Mini</strong></td><td>Q4_K_M</td><td>~2.5 GB</td><td>~120 tok/s</td><td>Muy buena</td><td>Router local, comandos rápidos, respuestas simples</td></tr>
      <tr><td><strong>Llama 3.2 3B</strong></td><td>Q8</td><td>~3.5 GB</td><td>~80 tok/s</td><td>Buena</td><td>Respuestas de asistente, conversación casual</td></tr>
      <tr><td><strong>Mistral 7B v0.3</strong></td><td>Q4_K_M</td><td>~4.5 GB</td><td>~50 tok/s</td><td>Excelente</td><td>Inbox, clasificación, análisis de texto</td></tr>
      <tr><td><strong>Llama 3.1 8B</strong></td><td>Q4_K_M</td><td>~5.0 GB</td><td>~40 tok/s</td><td>Excelente</td><td>Conversación profunda, preguntas complejas (intent ask)</td></tr>
      <tr><td><strong>Qwen2.5 7B</strong></td><td>Q4_K_M</td><td>~4.5 GB</td><td>~50 tok/s</td><td>Excelente</td><td>Mejor en español, razonamiento matemático</td></tr>
    </tbody>
  </table>

  <h3>Estrategia Híbrida Local + Nube</h3>
  <div class="arch-block">
<span class="hl">ROUTER DE IA — Decisión de motor</span>

Comando recibido (voz o texto)
        │
        ▼
<span class="ok">¿Patrón local sin LLM?</span>  →  SÍ  →  Resolver en cliente (0 ms, 0 costo)
        │ NO                             (hora, fecha, saludo, navegar...)
        ▼
<span class="ok">¿Ollama disponible?</span>  →  SÍ  →  Phi-3.5 Mini / Mistral 7B local
        │ NO                             (~300–800 ms, $0)
        ▼
<span class="ok">¿Anthropic API disponible?</span>  →  SÍ  →  Claude Haiku 4.5
        │ NO                               (~600 ms, ~$0.001/llamada)
        ▼
Modo degradado: respuesta determinista / manual            (sin IA)</div>

  <h3>Casos de uso por motor</h3>
  <table>
    <thead><tr><th>Intención</th><th>Motor</th><th>Por qué</th></tr></thead>
    <tbody>
      <tr><td>Hora, fecha, saludo</td><td><span class="badge badge-green">Local sin LLM</span></td><td>Cero latencia</td></tr>
      <tr><td>Abrir app, navegar</td><td><span class="badge badge-green">Local sin LLM</span></td><td>Whitelist estática</td></tr>
      <tr><td>Clima (Open-Meteo)</td><td><span class="badge badge-green">Local sin LLM</span></td><td>API gratuita, sin LLM</td></tr>
      <tr><td>Crear tarea / recordatorio</td><td><span class="badge badge-blue">Ollama local</span></td><td>Phi-3.5 Min — privacidad</td></tr>
      <tr><td>Clasificar inbox</td><td><span class="badge badge-blue">Ollama local</span></td><td>Mistral 7B — sin costo recurrente</td></tr>
      <tr><td>Pregunta general (ask)</td><td><span class="badge badge-blue">Ollama local</span></td><td>Llama 3.1 8B — offline</td></tr>
      <tr><td>Briefing diario (complejo)</td><td><span class="badge badge-yellow">Anthropic API</span></td><td>Contexto amplio, mayor calidad</td></tr>
      <tr><td>Insights de 4 semanas</td><td><span class="badge badge-yellow">Anthropic API</span></td><td>Análisis profundo, contexto largo</td></tr>
      <tr><td>Cualquier cosa en modo offline</td><td><span class="badge badge-blue">Ollama local</span></td><td>Fallback completo</td></tr>
    </tbody>
  </table>

  <div class="callout callout-ok">
    <div class="callout-title">Ahorro estimado con IA local</div>
    <p>Actualmente, PRTS web gasta Anthropic API en clasificación de inbox (~5 llamadas/día) + comandos de voz (~10/día) + briefing (1/día).
    Con Elfie Desktop, las clasificaciones e intents simples van a Ollama local. <strong>Estimado: reducción del 70–80% del gasto mensual en API de IA.</strong>
    Solo briefings e insights quedan en Claude API por calidad.</p>
  </div>
</div>

<!-- ═══════════════════════════════════════ 6 · BASE DE DATOS ═══════════════════════════════════════ -->
<div class="page">
  <div class="section-header">
    <div class="section-num">06</div>
    <div class="section-title">Base de Datos Compartida</div>
  </div>

  <p>La base de datos de Supabase existente es la fuente de verdad única para ambas apps. Elfie Desktop se conecta con las
  mismas credenciales (<code>SUPABASE_URL</code> + <code>SUPABASE_ANON_KEY</code>), el mismo RLS, y la misma API cliente JavaScript reutilizada desde PRTS web.</p>

  <h3>Nuevas Tablas (migraciones 0012–0015)</h3>

  <div class="code-block"><span class="cm">-- Migración 0012: Configuración de Elfie y perfiles de voz</span>
<span class="kw">CREATE TABLE</span> elfie_config (
  user_id  <span class="kw">uuid DEFAULT</span> auth.uid() <span class="kw">PRIMARY KEY</span>,
  personality   <span class="kw">text DEFAULT</span> <span class="st">'profesional'</span>,
  voice_engine  <span class="kw">text DEFAULT</span> <span class="st">'kokoro'</span>,   <span class="cm">-- kokoro|piper|xtts|edge|elevenlabs</span>
  voice_name    <span class="kw">text DEFAULT</span> <span class="st">'es-MX-DaliaNeural'</span>,
  voice_speed   <span class="kw">float DEFAULT</span> <span class="num">1.0</span>,
  voice_pitch   <span class="kw">float DEFAULT</span> <span class="num">0.0</span>,
  verbosity     <span class="kw">text DEFAULT</span> <span class="st">'concisa'</span>,  <span class="cm">-- minima|concisa|media|detallada</span>
  tts_enabled   <span class="kw">bool DEFAULT true</span>,
  local_llm_model <span class="kw">text DEFAULT</span> <span class="st">'phi3.5'</span>,
  theme         <span class="kw">text DEFAULT</span> <span class="st">'dark'</span>,
  updated_at    <span class="kw">timestamptz DEFAULT now</span>()
);

<span class="cm">-- Migración 0013: Perfiles de voz personalizados (clonación)</span>
<span class="kw">CREATE TABLE</span> voice_profiles (
  id          <span class="kw">uuid DEFAULT</span> gen_random_uuid() <span class="kw">PRIMARY KEY</span>,
  user_id     <span class="kw">uuid DEFAULT</span> auth.uid(),
  name        <span class="kw">text NOT NULL</span>,
  engine      <span class="kw">text NOT NULL</span>,              <span class="cm">-- xtts|fish|elevenlabs</span>
  reference_audio_url <span class="kw">text</span>,              <span class="cm">-- audio de referencia para clonar</span>
  config      <span class="kw">jsonb</span>,                      <span class="cm">-- parámetros extra del motor</span>
  is_active   <span class="kw">bool DEFAULT false</span>,
  created_at  <span class="kw">timestamptz DEFAULT now</span>()
);

<span class="cm">-- Migración 0014: Log de acciones del sistema operativo</span>
<span class="kw">CREATE TABLE</span> system_actions (
  id          <span class="kw">uuid DEFAULT</span> gen_random_uuid() <span class="kw">PRIMARY KEY</span>,
  user_id     <span class="kw">uuid DEFAULT</span> auth.uid(),
  action_type <span class="kw">text NOT NULL</span>,             <span class="cm">-- open_app|volume|file|routine...</span>
  payload     <span class="kw">jsonb</span>,
  executed_at <span class="kw">timestamptz DEFAULT now</span>()
);

<span class="cm">-- Migración 0015: Métricas del sistema (historial + dashboard)</span>
<span class="kw">CREATE TABLE</span> system_metrics (
  id              <span class="kw">uuid DEFAULT</span> gen_random_uuid() <span class="kw">PRIMARY KEY</span>,
  user_id         <span class="kw">uuid DEFAULT</span> auth.uid(),
  cpu_percent     <span class="kw">float</span>,
  ram_used_gb     <span class="kw">float</span>,
  gpu_percent     <span class="kw">float</span>,
  gpu_vram_used_gb <span class="kw">float</span>,
  gpu_temp_c      <span class="kw">float</span>,
  gpu_power_w     <span class="kw">float</span>,
  recorded_at     <span class="kw">timestamptz DEFAULT now</span>()
);</div>

  <h3>Sincronización en Tiempo Real</h3>
  <table>
    <thead><tr><th>Canal Supabase Realtime</th><th>Dirección</th><th>Qué sincroniza</th></tr></thead>
    <tbody>
      <tr><td><code>tasks</code></td><td>Web ↔ Desktop</td><td>Nueva tarea en web → aparece en Elfie en &lt;1 s</td></tr>
      <tr><td><code>daily_briefings</code></td><td>Web → Desktop</td><td>Briefing pre-generado disponible → Elfie lo muestra</td></tr>
      <tr><td><code>reminders</code></td><td>Web ↔ Desktop</td><td>Recordatorios creados en cualquier cliente</td></tr>
      <tr><td><code>inbox_entries</code></td><td>Web ↔ Desktop</td><td>Capturas procesadas en web o desktop</td></tr>
      <tr><td><code>ai_insights</code></td><td>Web → Desktop</td><td>Insights generados → Elfie notifica nativamente</td></tr>
    </tbody>
  </table>
</div>

<!-- ═══════════════════════════════════════ 7 · FASES ═══════════════════════════════════════ -->
<div class="page">
  <div class="section-header">
    <div class="section-num">07</div>
    <div class="section-title">Fases de Desarrollo</div>
  </div>

  <div class="phase-grid">
    <div class="phase-card">
      <div class="phase-card-head">
        <div class="phase-num">F0</div>
        <div class="phase-name">Setup Base</div>
        <div class="phase-duration">~1 sem</div>
      </div>
      <ul>
        <li>Inicializar proyecto Tauri 2.x</li>
        <li>Cargar frontend PRTS existente en WebView</li>
        <li>Conexión a Supabase (mismas credenciales)</li>
        <li>Autenticación reutilizada de PRTS</li>
        <li>Verificar que los módulos actuales funcionan en el WebView</li>
      </ul>
    </div>
    <div class="phase-card">
      <div class="phase-card-head">
        <div class="phase-num">F1</div>
        <div class="phase-name">Core Desktop</div>
        <div class="phase-duration">~2 sem</div>
      </div>
      <ul>
        <li>Tray icon con menú contextual</li>
        <li>Auto-start en Windows (registro)</li>
        <li>Notificaciones nativas de Windows</li>
        <li>Supabase Realtime (sincronización live)</li>
        <li>Dashboard Elfie en la tray: briefing + tareas del día</li>
      </ul>
    </div>
    <div class="phase-card">
      <div class="phase-card-head">
        <div class="phase-num">F2</div>
        <div class="phase-name">Control del Sistema</div>
        <div class="phase-duration">~2 sem</div>
      </div>
      <ul>
        <li>Launcher de aplicaciones (<code>open_app</code>)</li>
        <li>Control de volumen del sistema</li>
        <li>Monitor CPU/GPU/RAM en tiempo real</li>
        <li>Gestión básica de archivos y carpetas</li>
        <li>Portapapeles (leer/escribir)</li>
        <li>Rutinas de inicio configurables</li>
      </ul>
    </div>
    <div class="phase-card">
      <div class="phase-card-head">
        <div class="phase-num">F3</div>
        <div class="phase-name">Voz Local</div>
        <div class="phase-duration">~2 sem</div>
      </div>
      <ul>
        <li>Whisper.cpp como STT (sin Google)</li>
        <li>Kokoro TTS / Piper TTS integrado</li>
        <li>Wake word con Picovoice Porcupine</li>
        <li>Flujo completo: wake → Whisper → router → TTS</li>
        <li>Indicador visual de estado (escucha/habla)</li>
      </ul>
    </div>
    <div class="phase-card">
      <div class="phase-card-head">
        <div class="phase-num">F4</div>
        <div class="phase-name">IA Local</div>
        <div class="phase-duration">~2–3 sem</div>
      </div>
      <ul>
        <li>Instalar Ollama, descargar modelos base</li>
        <li>Router híbrido: local → Anthropic fallback</li>
        <li>Personalidad de Elfie configurable</li>
        <li>Perfiles de voz (múltiples motores)</li>
        <li>Panel de configuración de personalidad en UI</li>
        <li>Memoria contextual con ChromaDB (RAG)</li>
      </ul>
    </div>
    <div class="phase-card">
      <div class="phase-card-head">
        <div class="phase-num">F5</div>
        <div class="phase-name">Módulos Nuevos</div>
        <div class="phase-duration">~2 sem</div>
      </div>
      <ul>
        <li>Panel de monitor de sistema completo</li>
        <li>Historial de <code>system_metrics</code> en gráficas</li>
        <li>Routine Engine visual (crear secuencias)</li>
        <li>Módulo Alumnos (tabla + UI pendiente)</li>
        <li>Módulo Contenido (planificador de clases/streams)</li>
      </ul>
    </div>
    <div class="phase-card">
      <div class="phase-card-head">
        <div class="phase-num">F6</div>
        <div class="phase-name">Clonación de Voz</div>
        <div class="phase-duration">~1 sem</div>
      </div>
      <ul>
        <li>XTTS v2 integrado como opción de motor</li>
        <li>Interfaz para subir audio de referencia</li>
        <li>Almacenamiento del perfil en <code>voice_profiles</code></li>
        <li>Previsualización antes de activar</li>
      </ul>
    </div>
    <div class="phase-card">
      <div class="phase-card-head">
        <div class="phase-num">F7</div>
        <div class="phase-name">Distribución</div>
        <div class="phase-duration">~1 sem</div>
      </div>
      <ul>
        <li>Installer .msi / .exe para Windows</li>
        <li>Auto-update con Tauri updater</li>
        <li>Firma del ejecutable (opcional)</li>
        <li>Script de configuración inicial (Ollama + modelos)</li>
        <li>Documentación de setup</li>
      </ul>
    </div>
  </div>

  <div class="callout callout-info">
    <div class="callout-title">Tiempo total estimado</div>
    <p>~13–15 semanas de desarrollo a ritmo de proyecto personal. Las Fases 0–3 entregan la app funcional básica en ~7 semanas.
    Las Fases 4–7 añaden la diferenciación real (IA local, personalidad, clonación de voz). Es recomendable hacer uso real después de cada fase antes de avanzar — misma filosofía de PRTS.</p>
  </div>
</div>

<!-- ═══════════════════════════════════════ 8 · SUGERENCIAS ═══════════════════════════════════════ -->
<div class="page">
  <div class="section-header">
    <div class="section-num">08</div>
    <div class="section-title">Sugerencias de Desarrollo y Expansión</div>
  </div>

  <h3>Mejoras Técnicas Internas</h3>
  <div class="sug-grid">
    <div class="sug-card high">
      <div class="sug-title">RAG local con ChromaDB / LanceDB</div>
      <div class="sug-body">Elfie recuerda conversaciones, notas y contexto histórico. Al preguntar algo, recupera información relevante de las últimas semanas antes de llamar al LLM. Sin cloud, sin costo.</div>
    </div>
    <div class="sug-card high">
      <div class="sug-title">Plugin tauri-plugin-global-shortcut</div>
      <div class="sug-body">Atajos globales de teclado (funcionan aunque Elfie esté en segundo plano). Ej: Ctrl+Space abre el input de captura; Alt+E activa escucha de voz.</div>
    </div>
    <div class="sug-card high">
      <div class="sug-title">Offline-first completo</div>
      <div class="sug-body">Elfie funciona sin internet: Ollama local, Whisper local, Kokoro local. Al reconectar, sincroniza con Supabase las acciones acumuladas (cola de operaciones pendientes).</div>
    </div>
    <div class="sug-card high">
      <div class="sug-title">Auto-update silencioso</div>
      <div class="sug-body">Tauri updater apuntando a GitHub Releases. Elfie se actualiza en segundo plano y notifica al reiniciar. Sin intervención manual.</div>
    </div>
    <div class="sug-card med">
      <div class="sug-title">Evals para LLM local</div>
      <div class="sug-body">Extender el sistema de evals existente (ai/evals/) para correr contra Ollama local antes de cambiar de modelo. Mide precisión de clasificación en inbox y comandos.</div>
    </div>
    <div class="sug-card med">
      <div class="sug-title">NVML para métricas GPU reales</div>
      <div class="sug-body">La crate nvml-wrapper de Rust da acceso a VRAM, temperatura, potencia y uso de la RTX 5060 en tiempo real. Mucho más preciso que sysinfo genérico.</div>
    </div>
    <div class="sug-card med">
      <div class="sug-title">Sidecar pattern para Python</div>
      <div class="sug-body">Empaquetar Whisper y TTS como procesos sidecar de Tauri. El usuario no instala Python; el instalador incluye el entorno embebido. Setup de un solo clic.</div>
    </div>
    <div class="sug-card med">
      <div class="sug-title">Panel de costos de IA integrado</div>
      <div class="sug-body">Mostrar en la UI cuánto se gastó en Anthropic API este mes (ya existe ai_calls en Supabase) vs. cuántas llamadas se resolvieron localmente. Decisión informada sobre qué mover a local.</div>
    </div>
  </div>

  <h3>Expansiones de Capacidad</h3>
  <div class="sug-grid">
    <div class="sug-card ext">
      <div class="sug-title">Routine Engine Visual</div>
      <div class="sug-body">"Modo trabajo" = abrir VS Code + Discord + Spotify playlist foco + silenciar notificaciones + poner volumen a 40. Elfie ejecuta la secuencia con un comando. Rutinas guardadas en Supabase.</div>
    </div>
    <div class="sug-card ext">
      <div class="sug-title">Time Tracker automático</div>
      <div class="sug-body">Detectar qué aplicación tiene el foco (GetForegroundWindow en Windows) y registrar tiempo activo por app. Elfie analiza patrones: "pasaste 3 h en VS Code hoy". Sin datos externos.</div>
    </div>
    <div class="sug-card ext">
      <div class="sug-title">Módulo Alumnos completo</div>
      <div class="sug-body">Para Wolves robótica y LevelUp idiomas: registro de asistencia, progreso por alumno, calendario de sesiones, notas de clase. Elfie puede sugerir qué repasar en la próxima sesión.</div>
    </div>
    <div class="sug-card ext">
      <div class="sug-title">Modo Docente con IA</div>
      <div class="sug-body">Al dar clase, Elfie asiste: traducciones instantáneas (LLM local), definiciones, ejemplos generados en tiempo real. "Elfie, ¿cómo explico recursión en inglés?"</div>
    </div>
    <div class="sug-card ext">
      <div class="sug-title">Integración con Obsidian</div>
      <div class="sug-body">Los Apuntes de PRTS sincronizan automáticamente con un vault de Obsidian local. Escribe en PRTS, abre en Obsidian con sus plugins de backlinks y graph view.</div>
    </div>
    <div class="sug-card ext">
      <div class="sug-title">Screenshot + descripción IA</div>
      <div class="sug-body">Elfie puede capturar la pantalla y que el LLM multimodal la describa o extraiga texto/código. Útil para agregar contexto visual al inbox sin teclear.</div>
    </div>
    <div class="sug-card ext">
      <div class="sug-title">Monitor de progreso TecNM</div>
      <div class="sug-body">Módulo Escuela: fechas de exámenes, proyectos, calificaciones. Elfie alerta cuando se acerca un parcial. Integra con los Apuntes existentes por materia.</div>
    </div>
    <div class="sug-card ext">
      <div class="sug-title">Módulo Contenido / Stream</div>
      <div class="sug-body">Planificación de contenido para YouTube/Twitch/Redes. Ideas → guiones → calendario de publicación. Elfie sugiere temas basados en tendencias (intent ask con búsqueda web opcional).</div>
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════ 8b · INTEGRACIONES ═══════════════════════════════════════ -->
<div class="page">
  <div class="section-header">
    <div class="section-num">08</div>
    <div class="section-title">Integraciones Externas y Visión a Largo Plazo</div>
  </div>

  <h3>Integraciones con Apps ya en uso</h3>
  <div class="sug-grid">
    <div class="sug-card med">
      <div class="sug-title">Integración profunda con Discord</div>
      <div class="sug-body">Via Discord RPC + webhook: Elfie puede cambiar el estado "Ahora jugando", enviar mensajes a canales definidos, o alertar cuando llega un mensaje de alguien específico. "Elfie, dile a #wolves que llego en 10 min".</div>
    </div>
    <div class="sug-card med">
      <div class="sug-title">Spotify Web API real</div>
      <div class="sug-body">Cambiar de los presets estáticos actuales a la API real de Spotify: reproducir cualquier playlist/canción por nombre, ver la canción actual, control de reproducción por voz. OAuth de usuario (ya hay client_id en config).</div>
    </div>
    <div class="sug-card med">
      <div class="sug-title">OBS Studio Integration</div>
      <div class="sug-body">Via OBS WebSocket: cambiar escena, iniciar/detener grabación/stream, activar filtros. "Elfie, empieza la grabación", "Elfie, cambia a escena de juego". Útil si hace contenido.</div>
    </div>
    <div class="sug-card med">
      <div class="sug-title">VS Code Extension</div>
      <div class="sug-body">Elfie como extension de VS Code: crear tareas o apuntes desde el editor, "Elfie, agrega a pendientes revisar este bug", abrir archivos de proyectos PRTS por voz.</div>
    </div>
    <div class="sug-card med">
      <div class="sug-title">WhatsApp via wa-automate / Baileys</div>
      <div class="sug-body">Leer el último mensaje de un contacto, responder mensajes predefinidos, o notificar a contactos. Requiere un número/sesión dedicada. "Elfie, ¿tengo mensajes nuevos de mamá?"</div>
    </div>
    <div class="sug-card med">
      <div class="sug-title">Google Calendar bidireccional</div>
      <div class="sug-body">Actualmente PRTS solo escribe a Calendar. Con Elfie Desktop: leer eventos del día desde Calendar y mostrarlos en el briefing, sincronizar ambas vías sin abrir el navegador.</div>
    </div>
  </div>

  <h3>Visión a Largo Plazo — Elfie como Plataforma</h3>
  <div class="callout callout-dark">
    <h4>Elfie como Sistema Nervioso Personal</h4>
    <p>La visión final de Elfie-PRTS Desktop no es solo una app de escritorio mejorada — es un <strong>sistema nervioso personal</strong>:
    toda la información de Sylft (estudios, gym, finanzas, trabajo, proyectos, alumnos) pasa por un único punto de control que
    aprende, conecta y facilita. Elfie actúa en segundo plano: agenda, advierte, recuerda, ejecuta y reporta.</p>
  </div>

  <div class="sug-grid">
    <div class="sug-card hard">
      <div class="sug-title">Elfie Mobile (React Native / Flutter)</div>
      <div class="sug-body">App móvil nativa que comparte la misma base de datos Supabase. Para los días sin computadora: captura por voz en el celular, Elfie clasifica y procesa al llegar al escritorio.</div>
    </div>
    <div class="sug-card hard">
      <div class="sug-title">Fine-tuning de LLM con tus datos</div>
      <div class="sug-body">Con ~6 meses de datos en Supabase (tareas, inbox, gym, dieta), hacer fine-tuning de un modelo pequeño (Phi-3.5, Qwen2.5) para que entienda el vocabulario y contexto personal de Sylft sin prompts largos.</div>
    </div>
    <div class="sug-card hard">
      <div class="sug-title">Companion nativo (Electron companion)</div>
      <div class="sug-body">Proceso de sistema sin ventana que hace el nivel C real: funciona con el navegador cerrado, inicia con Windows, escucha la wake word permanentemente usando Picovoice (WASM on-device).</div>
    </div>
    <div class="sug-card hard">
      <div class="sug-title">API pública de Elfie</div>
      <div class="sug-body">Exponer una API local (localhost:XXXX) para que otras herramientas (scripts, VS Code, Alfred/PowerToys) puedan hablarle a Elfie directamente sin abrir la app.</div>
    </div>
  </div>

  <hr class="divider" style="margin-top:24pt;">
  <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-top:20pt;">
    <div>
      <div style="font-family:'Space Mono',monospace;font-size:8pt;color:#4a90b8;letter-spacing:1px;text-transform:uppercase;">Elfie · PRTS Desktop Edition</div>
      <div style="font-family:'Space Mono',monospace;font-size:8pt;color:#8a9ab0;margin-top:2pt;">Documento de Planificación v1.0 · Junio 2026 · Uso personal exclusivo · Sylft</div>
    </div>
    <div style="font-family:'Playfair Display',Georgia,serif;font-size:28pt;font-weight:900;color:#eef4fa;">Elfie</div>
  </div>
</div>

</body>
</html>"""

import subprocess, sys, os

output_path = "/home/user/mi-app-PRTS/docs/Elfie_PRTS_Desktop_Planificacion_v1.0.pdf"

# Intentar con weasyprint
try:
    from weasyprint import HTML, CSS
    print("Generando PDF con WeasyPrint...")
    HTML(string=HTML_CONTENT, base_url="/").write_pdf(output_path)
    print(f"PDF generado: {output_path}")
    size = os.path.getsize(output_path)
    print(f"Tamaño: {size / 1024:.1f} KB")
except Exception as e:
    print(f"WeasyPrint falló: {e}", file=sys.stderr)
    sys.exit(1)

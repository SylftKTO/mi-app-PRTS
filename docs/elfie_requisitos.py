#!/usr/bin/env python3
"""Genera el documento de requisitos Elfie-PRTS como PDF."""

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: 'Segoe UI', Arial, sans-serif;
  font-size: 10pt; line-height: 1.6; color: #1a1a2e;
}

/* PORTADA */
.cover {
  background: #0d1b2a; color: #fff;
  height: 100vh; display: flex; flex-direction: column;
  justify-content: center; padding: 56pt 60pt;
  page-break-after: always; position: relative;
}
.cover-bar { position:absolute; right:0; top:0; bottom:0; width:5pt; background:#4a90b8; }
.cover-eye { font-family:'Courier New',monospace; font-size:7.5pt;
  letter-spacing:3px; text-transform:uppercase; color:#4a90b8; margin-bottom:18pt; }
.cover-title { font-family:Georgia,serif; font-size:48pt; font-weight:700;
  line-height:1; color:#fff; margin-bottom:4pt; }
.cover-sub { font-family:Georgia,serif; font-size:16pt; color:#4a90b8; margin-bottom:28pt; }
.cover-desc { font-size:10.5pt; color:#8aa8c0; max-width:360pt;
  line-height:1.75; margin-bottom:36pt; }
.cover-chips { display:flex; flex-wrap:wrap; gap:7pt; margin-bottom:36pt; }
.chip { font-family:'Courier New',monospace; font-size:7pt;
  padding:3pt 9pt; border:1pt solid #1e3a52; color:#4a90b8;
  letter-spacing:1px; border-radius:3pt; }
.cover-foot { font-family:'Courier New',monospace; font-size:7pt;
  color:#2e4a60; border-top:1pt solid #1e3a52; padding-top:12pt; letter-spacing:1px; }

/* PÁGINAS */
.page { padding:40pt 56pt; page-break-after:always; }
.page:last-child { page-break-after:avoid; }

.sec-head { display:flex; align-items:center; gap:10pt; margin-bottom:20pt; }
.sec-n { font-family:'Courier New',monospace; font-size:7.5pt;
  background:#eef4fa; color:#4a90b8; padding:3pt 8pt;
  border-radius:3pt; letter-spacing:1px; white-space:nowrap; }
.sec-t { font-family:Georgia,serif; font-size:19pt; font-weight:700; color:#0d1b2a; }

h3 { font-size:11pt; font-weight:700; color:#0d1b2a;
  margin:16pt 0 6pt 0; padding-left:9pt; border-left:3pt solid #4a90b8; }
h4 { font-family:'Courier New',monospace; font-size:8pt; font-weight:700;
  color:#4a90b8; text-transform:uppercase; letter-spacing:1.5px; margin:10pt 0 4pt 0; }
p { margin-bottom:7pt; color:#2c3e50; font-size:9.5pt; }

/* CALLOUTS */
.call { border-radius:5pt; padding:11pt 14pt; margin:10pt 0; }
.call-info { background:#eef4fa; border-left:4pt solid #4a90b8; }
.call-warn { background:#fef9e7; border-left:4pt solid #f39c12; }
.call-ok   { background:#eafaf1; border-left:4pt solid #27ae60; }
.call-dark { background:#0d1b2a; color:#a8c8e0; border-left:4pt solid #4a90b8; }
.call-dark p,.call-dark li { color:#8aa8c0; font-size:9pt; }
.call-dark h4,.call-t-dark { color:#4a90b8; }
.call-t { font-family:'Courier New',monospace; font-size:7.5pt; font-weight:700;
  text-transform:uppercase; letter-spacing:1px; margin-bottom:4pt; color:#4a90b8; }
.call-warn .call-t { color:#c0882a; }
.call-ok   .call-t { color:#1e8449; }

/* TABLAS */
table { width:100%; border-collapse:collapse; margin:9pt 0; font-size:9pt; }
thead tr { background:#0d1b2a; color:#fff; }
thead th { padding:7pt 9pt; text-align:left;
  font-family:'Courier New',monospace; font-size:7pt;
  font-weight:700; letter-spacing:1px; text-transform:uppercase; }
tbody tr:nth-child(even) { background:#f4f7fb; }
tbody tr:nth-child(odd)  { background:#fff; }
tbody td { padding:6pt 9pt; border-bottom:1pt solid #e0e8f0; vertical-align:top; }

.b { display:inline-block; font-family:'Courier New',monospace; font-size:6.5pt;
     padding:1.5pt 5pt; border-radius:3pt; font-weight:700; }
.b-g { background:#d5f5e3; color:#1e8449; }
.b-b { background:#d6eaf8; color:#1a5276; }
.b-y { background:#fdebd0; color:#784212; }
.b-r { background:#fadbd8; color:#78281f; }
.b-p { background:#e8daef; color:#6c3483; }
.b-gray { background:#eaecee; color:#515a5a; }

/* CÓDIGO */
.code { background:#0d1b2a; color:#a8d8f0; font-family:'Courier New',monospace;
  font-size:7.8pt; padding:11pt 14pt; border-radius:5pt;
  margin:7pt 0; line-height:1.7; }
.code .cm  { color:#405060; font-style:italic; }
.code .kw  { color:#4a90b8; }
.code .st  { color:#7ecb7a; }
.code .hl  { color:#c8daea; font-weight:bold; }
code { font-family:'Courier New',monospace; font-size:8pt;
  background:#eef4fa; color:#1a5276; padding:1pt 4pt; border-radius:2pt; }

ul,ol { padding-left:15pt; margin-bottom:7pt; }
li { margin-bottom:3pt; color:#2c3e50; font-size:9.5pt; }
li strong { color:#0d1b2a; }

/* TARJETAS DE REQUISITO */
.req-grid { display:grid; grid-template-columns:1fr 1fr; gap:9pt; margin:10pt 0; }
.req { border:1.5pt solid #dde3ea; border-radius:6pt;
  padding:11pt 13pt; background:#fafcff; }
.req.must { border-left:4pt solid #e74c3c; }
.req.high { border-left:4pt solid #4a90b8; }
.req.opt  { border-left:4pt solid #27ae60; }
.req.cond { border-left:4pt solid #f39c12; }
.req-t { font-weight:700; font-size:10pt; color:#0d1b2a; margin-bottom:3pt; }
.req-b { font-size:8.5pt; color:#4a6280; line-height:1.5; }
.req-tag { font-family:'Courier New',monospace; font-size:6.5pt;
  text-transform:uppercase; letter-spacing:1px; margin-bottom:5pt; color:#8a9ab0; }

/* DISCO / VRAM BARS */
.bar-row { display:flex; align-items:center; gap:8pt; margin:4pt 0; }
.bar-label { font-size:8.5pt; color:#2c3e50; min-width:180pt; }
.bar-track { flex:1; background:#e0e8f0; border-radius:3pt; height:9pt; }
.bar-fill  { height:9pt; border-radius:3pt; }
.bar-val { font-family:'Courier New',monospace; font-size:8pt; color:#4a90b8; min-width:45pt; text-align:right; }

/* FASES */
.fase-row { display:flex; gap:8pt; margin:4pt 0; align-items:flex-start; }
.fase-dot { width:18pt; height:18pt; border-radius:50%; background:#0d1b2a;
  color:#4a90b8; font-family:'Courier New',monospace; font-size:7pt;
  font-weight:700; display:flex; align-items:center; justify-content:center;
  flex-shrink:0; margin-top:1pt; }
.fase-body { font-size:9pt; color:#2c3e50; }
.fase-body strong { color:#0d1b2a; }

.divider { border:none; border-top:1pt solid #dde3ea; margin:12pt 0; }

/* CHECKLIST */
.chk { font-size:9pt; color:#2c3e50; margin:3pt 0; padding-left:4pt; }
.chk::before { content:"☐ "; color:#4a90b8; font-size:9pt; }

@page { margin:0; size:A4; }
</style>
</head>
<body>

<!-- PORTADA -->
<div class="cover">
  <div class="cover-bar"></div>
  <div class="cover-eye">Requisitos de Desarrollo · v1.0 · Junio 2026</div>
  <div class="cover-title">Elfie</div>
  <div class="cover-sub">PRTS Desktop — Lista de Requisitos</div>
  <div class="cover-desc">
    Todo lo que necesitás instalar, descargar, configurar y considerar
    para desarrollar Elfie Desktop. Organizado por categoría, fase
    de uso y prioridad.
  </div>
  <div class="cover-chips">
    <div class="chip">TAURI 2.X</div>
    <div class="chip">RUST + CARGO</div>
    <div class="chip">OLLAMA</div>
    <div class="chip">WHISPER.CPP</div>
    <div class="chip">KOKORO TTS</div>
    <div class="chip">PORCUPINE</div>
    <div class="chip">LANCEDB</div>
    <div class="chip">CUDA 12.X</div>
    <div class="chip">WINDOWS 10/11</div>
  </div>
  <div class="cover-foot">
    PROPIETARIO: SYLFT &nbsp;·&nbsp; IA: ELFIE &nbsp;·&nbsp;
    RTX 5060 · 8 GB VRAM &nbsp;·&nbsp; 16 GB RAM &nbsp;·&nbsp; RYZEN 5 5600G
  </div>
</div>

<!-- ══════════ 1 · RESUMEN EJECUTIVO ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">01</div><div class="sec-t">Resumen Ejecutivo</div></div>

  <div class="call call-info">
    <div class="call-t">Cómo leer este documento</div>
    <p>Los requisitos están marcados por prioridad:
    <span class="b b-r">OBLIGATORIO</span> — sin esto no compila o no funciona ·
    <span class="b b-b">RECOMENDADO</span> — necesario para las funciones principales ·
    <span class="b b-g">OPCIONAL</span> — mejoras o fases avanzadas ·
    <span class="b b-y">CONDICIONAL</span> — solo si se usa esa feature específica.</p>
  </div>

  <h3>Conteo de requisitos</h3>
  <table>
    <thead><tr><th>Categoría</th><th>Items</th><th>Descarga</th><th>Espacio aprox.</th><th>Costo</th></tr></thead>
    <tbody>
      <tr><td>Herramientas de desarrollo (Rust, Node, MSVC)</td><td>4</td><td>Sí</td><td>~10 GB</td><td>Gratuito</td></tr>
      <tr><td>Framework Tauri + plugins + crates Rust</td><td>12</td><td>Cargo</td><td>~2 GB cache</td><td>Gratuito</td></tr>
      <tr><td>IA Local — Ollama + modelos LLM</td><td>5</td><td>Sí</td><td>~13 GB</td><td>Gratuito</td></tr>
      <tr><td>STT — Whisper.cpp + modelo</td><td>2</td><td>Sí</td><td>~1.6 GB</td><td>Gratuito</td></tr>
      <tr><td>TTS — motores de voz</td><td>4</td><td>Sí/pip</td><td>~1 GB</td><td>Gratuito</td></tr>
      <tr><td>Wake word — Picovoice Porcupine</td><td>3</td><td>pip + cuenta</td><td>&lt;50 MB</td><td>Gratuito</td></tr>
      <tr><td>GPU — CUDA + drivers</td><td>3</td><td>Sí</td><td>~4 GB</td><td>Gratuito</td></tr>
      <tr><td>Python + entorno de sidecars</td><td>8 paquetes</td><td>pip</td><td>~3 GB</td><td>Gratuito</td></tr>
      <tr><td>RAG local — LanceDB (Fase 6)</td><td>2</td><td>pip</td><td>~500 MB</td><td>Gratuito</td></tr>
      <tr><td>Cuentas y API Keys</td><td>4</td><td>—</td><td>—</td><td>Mayormente gratuito</td></tr>
      <tr><td><strong>TOTAL MÍNIMO (Fases 0–5)</strong></td><td><strong>—</strong></td><td><strong>—</strong></td><td><strong>~25 GB libres</strong></td><td><strong>$0</strong></td></tr>
    </tbody>
  </table>

  <h3>Espacio en disco — Desglose</h3>
  <div class="bar-row"><div class="bar-label">Modelos Ollama (4 modelos LLM)</div><div class="bar-track"><div class="bar-fill" style="width:65%;background:#4a90b8;"></div></div><div class="bar-val">~13 GB</div></div>
  <div class="bar-row"><div class="bar-label">CUDA Toolkit + cuDNN</div><div class="bar-track"><div class="bar-fill" style="width:17%;background:#4a90b8;"></div></div><div class="bar-val">~3.5 GB</div></div>
  <div class="bar-row"><div class="bar-label">Build Tools MSVC (Rust en Windows)</div><div class="bar-track"><div class="bar-fill" style="width:35%;background:#7ab8d8;"></div></div><div class="bar-val">~7 GB</div></div>
  <div class="bar-row"><div class="bar-label">Whisper large-v3-turbo (modelo STT)</div><div class="bar-track"><div class="bar-fill" style="width:8%;background:#5dbb6d;"></div></div><div class="bar-val">~1.6 GB</div></div>
  <div class="bar-row"><div class="bar-label">TTS models (Kokoro + Piper + XTTS v2)</div><div class="bar-track"><div class="bar-fill" style="width:15%;background:#5dbb6d;"></div></div><div class="bar-val">~3 GB</div></div>
  <div class="bar-row"><div class="bar-label">Cargo cache (crates Rust)</div><div class="bar-track"><div class="bar-fill" style="width:10%;background:#8a9ab0;"></div></div><div class="bar-val">~2 GB</div></div>
  <div class="bar-row"><div class="bar-label">Python + paquetes pip</div><div class="bar-track"><div class="bar-fill" style="width:8%;background:#8a9ab0;"></div></div><div class="bar-val">~1.5 GB</div></div>

  <div class="call call-warn" style="margin-top:12pt">
    <div class="call-t">Recomendación de disco</div>
    <p>Tener al menos <strong>30 GB libres</strong> antes de empezar. Los modelos de Ollama por defecto se guardan en
    <code>C:\Users\Sylft\.ollama\</code> — si el disco C tiene poco espacio, cambiar la ruta con la variable de entorno
    <code>OLLAMA_MODELS=D:\elfie\models</code> antes de instalar Ollama.</p>
  </div>

  <h3>Presupuesto de VRAM (RTX 5060 · 8 GB)</h3>
  <div class="bar-row"><div class="bar-label">Whisper large-v3-turbo (siempre activo)</div><div class="bar-track"><div class="bar-fill" style="width:19%;background:#e74c3c;"></div></div><div class="bar-val">~1.5 GB</div></div>
  <div class="bar-row"><div class="bar-label">LLM Qwen2.5 7B Q4 (al procesar)</div><div class="bar-track"><div class="bar-fill" style="width:56%;background:#4a90b8;"></div></div><div class="bar-val">~4.5 GB</div></div>
  <div class="bar-row"><div class="bar-label">Kokoro TTS (al sintetizar)</div><div class="bar-track"><div class="bar-fill" style="width:6%;background:#5dbb6d;"></div></div><div class="bar-val">~0.5 GB</div></div>
  <div class="bar-row"><div class="bar-label">XTTS v2 (Fase 6 · opcional)</div><div class="bar-track"><div class="bar-fill" style="width:31%;background:#9b59b6;"></div></div><div class="bar-val">~2.5 GB</div></div>
  <div class="bar-row"><div class="bar-label"><strong>Peak máximo (Whisper + LLM + Kokoro)</strong></div><div class="bar-track"><div class="bar-fill" style="width:81%;background:#1a3a50;"></div></div><div class="bar-val"><strong>~6.5 GB</strong></div></div>
</div>

<!-- ══════════ 2 · HERRAMIENTAS DE DESARROLLO ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">02</div><div class="sec-t">Herramientas de Desarrollo Base</div></div>

  <h3>Rust — Lenguaje del backend de Tauri</h3>
  <div class="call call-dark">
    <h4>Instalación</h4>
    <p><strong>URL:</strong> https://rustup.rs — instalador único para Windows</p>
    <p><strong>Instala automáticamente:</strong> rustc · cargo · rustfmt · clippy · rust-analyzer</p>
    <p><strong>Versión mínima:</strong> stable 1.77+ (rustup instala la última stable por defecto)</p>
    <p><strong>Peso:</strong> ~800 MB (toolchain) + ~2 GB cache de crates al compilar Tauri por primera vez</p>
  </div>
  <div class="code">
<span class="cm"># Verificar instalación (en PowerShell, tras reiniciar)</span>
rustc --version    <span class="cm"># rustc 1.xx.0 (xxxxxxx YYYY-MM-DD)</span>
cargo --version    <span class="cm"># cargo 1.xx.0 (xxxxxxx YYYY-MM-DD)</span></div>

  <div class="call call-warn">
    <div class="call-t">Primer build de Tauri</div>
    <p>La primera compilación descarga y compila todas las crates dependencias de Tauri. Tarda <strong>10–20 minutos</strong>
    dependiendo del procesador. Las compilaciones siguientes son incrementales y rápidas (~30 s).</p>
  </div>

  <hr class="divider">
  <h3>Microsoft C++ Build Tools — Obligatorio para compilar Rust en Windows</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>URL</td><td>https://visualstudio.microsoft.com/visual-cpp-build-tools/</td></tr>
      <tr><td>Componente a seleccionar</td><td>"Desarrollo de escritorio con C++" (workload completo)</td></tr>
      <tr><td>Incluye</td><td>MSVC · Windows SDK · CMake · MSBuild · libclang (para whisper-rs)</td></tr>
      <tr><td>Peso</td><td>~7 GB</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-r">OBLIGATORIO</span> — sin esto Rust no compila en Windows</td></tr>
    </tbody>
  </table>

  <hr class="divider">
  <h3>Node.js</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>URL</td><td>https://nodejs.org — versión LTS (22.x recomendada)</td></tr>
      <tr><td>Uso en el proyecto</td><td>Tauri CLI · scripts de package.json · npm</td></tr>
      <tr><td>Peso</td><td>~80 MB</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-r">OBLIGATORIO</span></td></tr>
    </tbody>
  </table>

  <hr class="divider">
  <h3>Tauri CLI</h3>
  <div class="code">
<span class="cm"># Instalar Tauri CLI (elegir una de las dos formas)</span>
npm install -g @tauri-apps/cli@^2     <span class="cm"># vía npm (recomendado)</span>
cargo install tauri-cli               <span class="cm"># vía Cargo (alternativa)</span>

<span class="cm"># Inicializar el proyecto dentro del repo existente</span>
cd mi-app-PRTS
mkdir elfie-desktop && cd elfie-desktop
npx @tauri-apps/cli init              <span class="cm"># sigue el wizard</span></div>

  <hr class="divider">
  <h3>LLVM / Clang — Para compilar whisper-rs</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>Instalación rápida</td><td><code>winget install LLVM.LLVM</code> (desde PowerShell)</td></tr>
      <tr><td>Alternativa</td><td>Incluido en Visual Studio Build Tools si se marca "Clang"</td></tr>
      <tr><td>Necesario para</td><td>La crate <code>whisper-rs</code> requiere libclang en PATH</td></tr>
      <tr><td>Verificar</td><td><code>clang --version</code></td></tr>
      <tr><td>Prioridad</td><td><span class="b b-b">RECOMENDADO</span> (obligatorio en Fase 3)</td></tr>
    </tbody>
  </table>

  <hr class="divider">
  <h3>Extensiones de VS Code recomendadas</h3>
  <table>
    <thead><tr><th>Extensión</th><th>ID</th><th>Función</th></tr></thead>
    <tbody>
      <tr><td>rust-analyzer</td><td>rust-lang.rust-analyzer</td><td>Autocompletado, errores inline en Rust</td></tr>
      <tr><td>Tauri</td><td>tauri-apps.tauri-vscode</td><td>Comandos Tauri integrados en VS Code</td></tr>
      <tr><td>Even Better TOML</td><td>tamasfe.even-better-toml</td><td>Syntax de Cargo.toml</td></tr>
      <tr><td>CodeLLDB</td><td>vadimcn.vscode-lldb</td><td>Debugger para Rust</td></tr>
    </tbody>
  </table>
</div>

<!-- ══════════ 3 · TAURI — PLUGINS Y CRATES ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">03</div><div class="sec-t">Tauri 2.x — Plugins y Crates Rust</div></div>

  <div class="call call-info">
    <div class="call-t">Sin descarga manual</div>
    <p>Todos estos se declaran en <code>Cargo.toml</code> y se descargan automáticamente con <code>cargo build</code>.
    No hay instaladores separados.</p>
  </div>

  <h3>Plugins Tauri 2.x</h3>
  <table>
    <thead><tr><th>Plugin</th><th>Función</th><th>Fase</th><th>Prioridad</th></tr></thead>
    <tbody>
      <tr><td><code>tauri-plugin-global-shortcut</code></td><td>Atajos de teclado globales (Ctrl+Space, Alt+E)</td><td>F1</td><td><span class="b b-r">OBLIGATORIO</span></td></tr>
      <tr><td><code>tauri-plugin-autostart</code></td><td>Auto-inicio con Windows al encender</td><td>F1</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>tauri-plugin-notification</code></td><td>Notificaciones nativas de Windows</td><td>F1</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>tauri-plugin-clipboard-manager</code></td><td>Leer y escribir el portapapeles</td><td>F2</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>tauri-plugin-fs</code></td><td>Acceso al sistema de archivos (abrir carpetas)</td><td>F2</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>tauri-plugin-shell</code></td><td>Ejecutar procesos externos (sidecars Python)</td><td>F3</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>tauri-plugin-sql</code></td><td>SQLite local (si se prefiere sobre LanceDB)</td><td>F6</td><td><span class="b b-g">OPCIONAL</span></td></tr>
      <tr><td><code>tauri-plugin-updater</code></td><td>Auto-actualizaciones (no prioritario)</td><td>—</td><td><span class="b b-gray">DESCARTADO</span></td></tr>
    </tbody>
  </table>

  <h3>Crates Rust (dependencias en Cargo.toml)</h3>
  <table>
    <thead><tr><th>Crate</th><th>Función</th><th>Fase</th><th>Prioridad</th></tr></thead>
    <tbody>
      <tr><td><code>sysinfo</code></td><td>Métricas de CPU y RAM en tiempo real</td><td>F2</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>nvml-wrapper</code></td><td>Métricas GPU NVIDIA (RTX 5060): VRAM, temp, uso</td><td>F2</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>cpal</code></td><td>Captura de audio del micrófono</td><td>F3</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>whisper-rs</code></td><td>Bindings de Whisper.cpp para STT local</td><td>F3</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>reqwest</code></td><td>Cliente HTTP para la API de Ollama (localhost)</td><td>F4</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>tokio</code></td><td>Runtime async para operaciones concurrentes</td><td>F0</td><td><span class="b b-r">OBLIGATORIO</span></td></tr>
      <tr><td><code>serde / serde_json</code></td><td>Serialización JSON (IPC frontend↔backend)</td><td>F0</td><td><span class="b b-r">OBLIGATORIO</span></td></tr>
      <tr><td><code>windows</code></td><td>APIs de Windows para control de volumen y procesos</td><td>F2</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
    </tbody>
  </table>

  <h3>Configuración mínima de Cargo.toml</h3>
  <div class="code">
<span class="hl">[package]</span>
name = <span class="st">"elfie-desktop"</span>
version = <span class="st">"0.1.0"</span>
edition = <span class="st">"2021"</span>

<span class="hl">[dependencies]</span>
tauri        = { version = <span class="st">"2"</span>, features = [<span class="st">"tray-icon"</span>, <span class="st">"image-png"</span>] }
tokio        = { version = <span class="st">"1"</span>, features = [<span class="st">"full"</span>] }
serde        = { version = <span class="st">"1"</span>, features = [<span class="st">"derive"</span>] }
serde_json   = <span class="st">"1"</span>
reqwest      = { version = <span class="st">"0.11"</span>, features = [<span class="st">"json"</span>] }
sysinfo      = <span class="st">"0.30"</span>
nvml-wrapper = <span class="st">"0.10"</span>       <span class="cm"># F2: métricas RTX 5060</span>
cpal         = <span class="st">"0.15"</span>        <span class="cm"># F3: captura de micrófono</span>
whisper-rs   = <span class="st">"0.11"</span>       <span class="cm"># F3: STT local</span>

<span class="hl">[target.'cfg(windows)'.dependencies]</span>
windows = { version = <span class="st">"0.52"</span>, features = [<span class="st">"Win32_UI_WindowsAndMessaging"</span>,
            <span class="st">"Win32_Media_Audio"</span>, <span class="st">"Win32_System_ProcessStatus"</span>] }</div>
</div>

<!-- ══════════ 4 · IA LOCAL ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">04</div><div class="sec-t">IA Local — Ollama y Modelos LLM</div></div>

  <h3>Ollama — Runtime de LLMs</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>URL de descarga</td><td>https://ollama.ai/download (instalador Windows)</td></tr>
      <tr><td>Peso del instalador</td><td>~100 MB</td></tr>
      <tr><td>Qué instala</td><td>Servidor Ollama · CLI · runtime de modelos · API en localhost:11434</td></tr>
      <tr><td>Requisito de GPU</td><td>CUDA 12.x instalado previamente (sección 07)</td></tr>
      <tr><td>Directorio de modelos</td><td><code>C:\Users\Sylft\.ollama\models\</code> (configurable)</td></tr>
      <tr><td>Cambiar directorio</td><td>Variable de entorno: <code>OLLAMA_MODELS=D:\elfie\models</code></td></tr>
      <tr><td>Prioridad</td><td><span class="b b-b">RECOMENDADO</span> (necesario en Fase 4)</td></tr>
    </tbody>
  </table>

  <h3>Modelos LLM a descargar</h3>
  <table>
    <thead><tr><th>Modelo</th><th>Comando</th><th>Disco</th><th>VRAM</th><th>Velocidad</th><th>Uso principal</th><th>Fase</th></tr></thead>
    <tbody>
      <tr><td><strong>Phi-3.5 Mini Q4</strong></td><td><code>ollama pull phi3.5</code></td><td>~2.2 GB</td><td>~2.5 GB</td><td>~120 tok/s</td><td>Router · comandos rápidos</td><td>F4</td></tr>
      <tr><td><strong>Qwen2.5 7B Q4</strong></td><td><code>ollama pull qwen2.5:7b</code></td><td>~4.7 GB</td><td>~4.5 GB</td><td>~50 tok/s</td><td>Inbox · clasificación · es-MX</td><td>F4</td></tr>
      <tr><td><strong>Llama 3.1 8B Q4</strong></td><td><code>ollama pull llama3.1:8b</code></td><td>~4.9 GB</td><td>~5.0 GB</td><td>~40 tok/s</td><td>Conversación profunda · ask</td><td>F4</td></tr>
      <tr><td><strong>nomic-embed-text</strong></td><td><code>ollama pull nomic-embed-text</code></td><td>~274 MB</td><td>~270 MB</td><td>—</td><td>Embeddings para RAG (Apuntes)</td><td>F6</td></tr>
    </tbody>
  </table>

  <div class="call call-warn">
    <div class="call-t">Estrategia de descarga recomendada</div>
    <p><strong>Fases 0–3:</strong> No descargar nada aún. Ollama solo se necesita en Fase 4.<br>
    <strong>Inicio Fase 4:</strong> Descargar primero <code>phi3.5</code> (más pequeño, para validar que Ollama funciona con la RTX 5060).<br>
    <strong>Después:</strong> Descargar <code>qwen2.5:7b</code> para inbox y clasificación.<br>
    <strong>Solo si se necesita:</strong> <code>llama3.1:8b</code> para preguntas complejas.<br>
    <strong>Fase 6 únicamente:</strong> <code>nomic-embed-text</code> para los embeddings del RAG.</p>
  </div>

  <div class="code">
<span class="cm"># Verificar que Ollama usa la GPU (tras instalación)</span>
ollama run phi3.5 "hola"
<span class="cm"># En la respuesta debe aparecer: "using GPU" o similar</span>
<span class="cm"># Si dice "using CPU" → revisar drivers CUDA (sección 07)</span>

<span class="cm"># Ver modelos instalados</span>
ollama list

<span class="cm"># API REST (para Tauri)</span>
curl http://localhost:11434/api/generate -d '{
  "model": "phi3.5",
  "prompt": "hola",
  "stream": false
}'</div>
</div>

<!-- ══════════ 5 · STT ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">05</div><div class="sec-t">STT — Whisper.cpp (Reconocimiento de Voz Local)</div></div>

  <div class="call call-ok">
    <div class="call-t">Qué reemplaza</div>
    <p>Whisper.cpp reemplaza <code>webkitSpeechRecognition</code> que actualmente envía el audio a los servidores de Google.
    Con Whisper, el audio nunca sale de la computadora, funciona sin internet y tiene mayor precisión en español mexicano.</p>
  </div>

  <h3>Opción A — whisper-rs (Rust nativo, recomendado)</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>Crate</td><td><code>whisper-rs = "0.11"</code> en Cargo.toml</td></tr>
      <tr><td>Prerequisito</td><td>LLVM/Clang en PATH (<code>winget install LLVM.LLVM</code>)</td></tr>
      <tr><td>Prerequisito</td><td>CUDA Toolkit instalado para aceleración GPU</td></tr>
      <tr><td>Ventaja</td><td>Integración directa en Rust, sin proceso Python separado</td></tr>
      <tr><td>Desventaja</td><td>Compilación más compleja en Windows</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-b">RECOMENDADO</span> para Fase 3</td></tr>
    </tbody>
  </table>

  <h3>Opción B — faster-whisper (Python sidecar, más simple para empezar)</h3>
  <div class="code">
pip install faster-whisper    <span class="cm"># implementación optimizada con CTranslate2</span>
pip install pyaudio           <span class="cm"># captura de micrófono en Python</span></div>

  <h3>Modelo de Whisper a descargar</h3>
  <table>
    <thead><tr><th>Modelo</th><th>Calidad</th><th>VRAM</th><th>Disco</th><th>Latencia (frase ~5 s)</th><th>Recomendación</th></tr></thead>
    <tbody>
      <tr><td><strong>large-v3-turbo</strong></td><td>Excelente</td><td>~1.5 GB</td><td>~1.6 GB</td><td>~300 ms (GPU)</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td>medium</td><td>Muy buena</td><td>~1.5 GB</td><td>~1.5 GB</td><td>~400 ms</td><td>Alternativa si large-v3-turbo falla</td></tr>
      <tr><td>small</td><td>Buena</td><td>~0.5 GB</td><td>~500 MB</td><td>~150 ms</td><td>Solo si la VRAM escasea mucho</td></tr>
    </tbody>
  </table>

  <div class="call call-dark">
    <h4>Descarga del modelo (para whisper-rs)</h4>
    <p>Los modelos en formato ggml se descargan de Hugging Face:</p>
    <p>https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin</p>
    <p>Guardar en: <code>elfie-desktop/models/whisper/ggml-large-v3-turbo.bin</code></p>
    <p>Con faster-whisper (Python), el modelo se descarga automáticamente al primer uso.</p>
  </div>
</div>

<!-- ══════════ 6 · TTS ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">06</div><div class="sec-t">TTS — Motores de Voz de Elfie</div></div>

  <h3>Kokoro TTS — Motor primario (local, GPU)</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>Instalación</td><td><code>pip install kokoro-onnx onnxruntime-gpu</code></td></tr>
      <tr><td>Modelos</td><td>Se descargan automáticamente al primer uso (~300 MB)</td></tr>
      <tr><td>VRAM al ejecutar</td><td>~0.5 GB</td></tr>
      <tr><td>Latencia</td><td>&lt;100 ms en GPU</td></tr>
      <tr><td>Voz es-MX</td><td>Disponible</td></tr>
      <tr><td>Clonación de voz</td><td>No</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-b">RECOMENDADO</span> — motor principal</td></tr>
    </tbody>
  </table>

  <h3>Piper TTS — Fallback CPU</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>Instalación</td><td>Binario precompilado para Windows</td></tr>
      <tr><td>URL</td><td>https://github.com/rhasspy/piper/releases — <code>piper_windows_amd64.zip</code></td></tr>
      <tr><td>Modelos de voz es-MX</td><td>Descargar <code>.onnx</code> + <code>.json</code> del repositorio de modelos de Piper</td></tr>
      <tr><td>VRAM al ejecutar</td><td>0 — corre solo en CPU</td></tr>
      <tr><td>Latencia</td><td>&lt;50 ms en CPU</td></tr>
      <tr><td>Uso</td><td>Cuando la GPU está ocupada con el LLM</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-b">RECOMENDADO</span> — fallback</td></tr>
    </tbody>
  </table>

  <h3>edge-tts — Fallback Cloud Gratuito</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>Instalación</td><td><code>pip install edge-tts</code></td></tr>
      <tr><td>Uso</td><td>Sin modelos locales — llama a Microsoft en la nube</td></tr>
      <tr><td>API key</td><td>No requiere</td></tr>
      <tr><td>Voz es-MX recomendada</td><td><code>es-MX-DaliaNeural</code> (misma wake word)</td></tr>
      <tr><td>Costo</td><td>Gratuito (500k caracteres/mes con cuenta Microsoft, ilimitado sin cuenta)</td></tr>
      <tr><td>Latencia</td><td>~200 ms (requiere internet)</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-b">RECOMENDADO</span> — fallback cloud</td></tr>
    </tbody>
  </table>

  <h3>XTTS v2 (Coqui) — Clonación de voz (Fase 6)</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>Instalación</td><td><code>pip install TTS</code></td></tr>
      <tr><td>Modelos</td><td>Se descargan al primer uso (~2 GB)</td></tr>
      <tr><td>VRAM al ejecutar</td><td>~2.5 GB</td></tr>
      <tr><td>Capacidad especial</td><td>Clonar cualquier voz con 5 segundos de audio de referencia</td></tr>
      <tr><td>Uso en Elfie</td><td>Personalizar la voz de Elfie grabando una voz de referencia</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-g">OPCIONAL</span> — Fase 6</td></tr>
    </tbody>
  </table>

  <div class="call call-info">
    <div class="call-t">Estrategia en capas — orden de prioridad</div>
    <p><strong>1 · Kokoro</strong> (local GPU) → respuestas cotidianas, &lt;100 ms, $0<br>
    <strong>2 · Piper</strong> (local CPU) → si GPU saturada con LLM, &lt;50 ms, $0<br>
    <strong>3 · edge-tts DaliaNeural</strong> → si modelos no están cargados, ~200 ms, $0<br>
    <strong>4 · XTTS v2</strong> (Fase 6) → voz clonada para identidad de Elfie</p>
  </div>
</div>

<!-- ══════════ 7 · WAKE WORD ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">07</div><div class="sec-t">Wake Word — Picovoice Porcupine</div></div>

  <div class="call call-ok">
    <div class="call-t">Qué reemplaza</div>
    <p>Reemplaza <code>webkitSpeechRecognition</code> continuo en el navegador. Porcupine detecta la palabra clave
    directamente en el dispositivo (on-device), sin enviar audio a ningún servidor. Funciona con PRTS cerrado,
    consume menos del 3% de CPU y es el único componente que requiere una cuenta externa.</p>
  </div>

  <h3>Cuenta Picovoice (AccessKey)</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>URL de registro</td><td>https://console.picovoice.ai</td></tr>
      <tr><td>Plan necesario</td><td>Free (gratuito, suficiente para uso personal)</td></tr>
      <tr><td>Qué incluye el plan Free</td><td>AccessKey · hasta 3 palabras clave custom · uso personal</td></tr>
      <tr><td>Lo que se obtiene</td><td>AccessKey (string) que va en el código — no es una API key cloud, autoriza el SDK local</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-b">RECOMENDADO</span> (necesario en Fase 3)</td></tr>
    </tbody>
  </table>

  <h3>Modelo de palabra clave "Dalia"</h3>
  <div class="call call-warn">
    <div class="call-t">Paso crítico — entrenar el modelo custom</div>
    <p>"Dalia" no existe en los presets estándar de Porcupine (que son en inglés). Hay que entrenar un modelo custom:</p>
  </div>
  <ol style="margin:8pt 0 8pt 15pt;">
    <li style="margin-bottom:5pt">Ir a <strong>console.picovoice.ai → Porcupine → Train Keyword</strong></li>
    <li style="margin-bottom:5pt">Escribir la palabra: <strong>"Dalia"</strong> (o "hey Dalia" para mayor precisión)</li>
    <li style="margin-bottom:5pt">Seleccionar idioma: <strong>Español</strong></li>
    <li style="margin-bottom:5pt">Descargar el archivo <code>.ppn</code> generado</li>
    <li style="margin-bottom:5pt">Guardar en <code>elfie-desktop/models/porcupine/dalia_es.ppn</code></li>
  </ol>

  <h3>SDK de Porcupine</h3>
  <table>
    <thead><tr><th>Método</th><th>Instalación</th><th>Ventaja</th><th>Recomendado</th></tr></thead>
    <tbody>
      <tr><td>Python sidecar</td><td><code>pip install pvporcupine</code></td><td>Más simple, documentación amplia</td><td><span class="b b-g">SÍ</span> para empezar</td></tr>
      <tr><td>Rust nativo</td><td><code>pv-porcupine</code> en Cargo.toml</td><td>Integración directa, sin Python</td><td>Fases avanzadas</td></tr>
    </tbody>
  </table>

  <div class="code">
<span class="cm"># Python sidecar — ejemplo de uso</span>
<span class="kw">import</span> pvporcupine, pyaudio, struct

porcupine = pvporcupine.create(
    access_key=<span class="st">"TU_ACCESS_KEY_AQUI"</span>,
    keyword_paths=[<span class="st">"models/porcupine/dalia_es.ppn"</span>]
)
<span class="cm"># al detectar "Dalia" → emite evento al frontend de Tauri</span></div>
</div>

<!-- ══════════ 8 · GPU / CUDA ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">08</div><div class="sec-t">GPU — CUDA, cuDNN y Drivers NVIDIA</div></div>

  <div class="call call-warn">
    <div class="call-t">Verificar primero — RTX 5060 en Windows 10</div>
    <p>La RTX 5060 (arquitectura Blackwell, 2025) es posterior al fin de soporte de Windows 10 (octubre 2025).
    Antes de instalar CUDA, verificar que NVIDIA ofrece drivers para RTX 5060 en Windows 10.
    Si no los hay, la solución es actualizar a Windows 11 antes de Fase 3.</p>
  </div>

  <h3>Drivers NVIDIA</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>URL</td><td>https://www.nvidia.com/drivers</td></tr>
      <tr><td>Seleccionar</td><td>GeForce RTX 5060 · Windows 10/11 64-bit · Game Ready Driver</td></tr>
      <tr><td>Verificar en PowerShell</td><td><code>nvidia-smi</code> — debe mostrar la RTX 5060 con su VRAM</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-r">OBLIGATORIO</span> — prerequisito de todo lo demás</td></tr>
    </tbody>
  </table>

  <h3>CUDA Toolkit</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>URL</td><td>https://developer.nvidia.com/cuda-downloads</td></tr>
      <tr><td>Versión</td><td>CUDA 12.x (la más reciente compatible con tu driver)</td></tr>
      <tr><td>Tipo de instalador</td><td>Local (exe) — más confiable en Windows</td></tr>
      <tr><td>Peso</td><td>~3–4 GB</td></tr>
      <tr><td>Verificar</td><td><code>nvcc --version</code> en PowerShell</td></tr>
      <tr><td>Necesario para</td><td>Ollama GPU · faster-whisper · kokoro-onnx GPU · XTTS v2</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-b">RECOMENDADO</span> (sin CUDA todo corre en CPU, mucho más lento)</td></tr>
    </tbody>
  </table>

  <h3>cuDNN</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>URL</td><td>https://developer.nvidia.com/cudnn</td></tr>
      <tr><td>Requiere</td><td>Cuenta NVIDIA Developer (gratuita)</td></tr>
      <tr><td>Instalación</td><td>Copiar archivos DLL/lib/include a la carpeta de CUDA — no tiene instalador</td></tr>
      <tr><td>Versión</td><td>cuDNN 9.x compatible con CUDA 12.x</td></tr>
      <tr><td>Necesario para</td><td>Kokoro TTS · XTTS v2 (los modelos TTS se benefician de cuDNN)</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-g">OPCIONAL</span> — mejora rendimiento de TTS, no es bloqueante</td></tr>
    </tbody>
  </table>

  <div class="code">
<span class="cm"># Verificación completa del entorno GPU (PowerShell)</span>
nvidia-smi                    <span class="cm"># driver + VRAM disponible</span>
nvcc --version                <span class="cm"># CUDA instalado</span>
python -c <span class="st">"import torch; print(torch.cuda.is_available())"</span>  <span class="cm"># True si PyTorch detecta CUDA</span>
ollama run phi3.5 "test"      <span class="cm"># verificar que Ollama usa GPU</span></div>
</div>

<!-- ══════════ 9 · PYTHON ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">09</div><div class="sec-t">Python — Entorno de Sidecars</div></div>

  <div class="call call-info">
    <div class="call-t">Rol de Python en Elfie Desktop</div>
    <p>Python no es el lenguaje principal — ese es Rust. Python actúa como "sidecar": procesos separados que Tauri
    lanza y controla para los componentes de IA que aún no tienen bindings estables en Rust
    (Porcupine, Kokoro TTS, faster-whisper). A largo plazo se pueden migrar a Rust puro.</p>
  </div>

  <h3>Python base</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>URL</td><td>https://python.org/downloads</td></tr>
      <tr><td>Versión recomendada</td><td>Python 3.11 (mayor compatibilidad con TTS · Coqui aún no soporta 3.12 completamente)</td></tr>
      <tr><td>Opciones al instalar</td><td><strong>Marcar "Add Python to PATH"</strong> — sin esto nada funciona desde PowerShell</td></tr>
      <tr><td>Verificar</td><td><code>python --version</code> · <code>pip --version</code></td></tr>
      <tr><td>Prioridad</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
    </tbody>
  </table>

  <h3>Paquetes pip — Instalación completa por fases</h3>
  <div class="code">
<span class="cm"># FASE 3 — STT + Wake Word</span>
pip install faster-whisper pyaudio pvporcupine

<span class="cm"># FASE 3 — TTS primario y fallbacks</span>
pip install kokoro-onnx onnxruntime-gpu edge-tts

<span class="cm"># FASE 3 — Piper (binario separado, ver sección 06)</span>
<span class="cm"># Solo pip install piper-tts si se quiere desde Python</span>
pip install piper-tts

<span class="cm"># FASE 6 — RAG Local</span>
pip install lancedb sentence-transformers

<span class="cm"># FASE 6 — Clonación de voz (XTTS v2)</span>
pip install TTS    <span class="cm"># paquete de Coqui AI (~2 GB modelos al primer uso)</span>

<span class="cm"># UTILIDADES GENERALES</span>
pip install numpy scipy soundfile</div>

  <h3>Tabla completa de paquetes pip</h3>
  <table>
    <thead><tr><th>Paquete</th><th>Función</th><th>Fase</th><th>Prioridad</th></tr></thead>
    <tbody>
      <tr><td><code>faster-whisper</code></td><td>STT — transcripción de voz local</td><td>F3</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>pyaudio</code></td><td>Captura de micrófono en Python</td><td>F3</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>pvporcupine</code></td><td>Wake word Porcupine SDK</td><td>F3</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>kokoro-onnx</code></td><td>TTS primario Kokoro</td><td>F3</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>onnxruntime-gpu</code></td><td>Runtime ONNX con aceleración GPU</td><td>F3</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>edge-tts</code></td><td>TTS cloud gratuito (DaliaNeural)</td><td>F3</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>numpy · scipy · soundfile</code></td><td>Utilidades de audio</td><td>F3</td><td><span class="b b-b">RECOMENDADO</span></td></tr>
      <tr><td><code>lancedb</code></td><td>Vector store para RAG local</td><td>F6</td><td><span class="b b-g">OPCIONAL</span></td></tr>
      <tr><td><code>sentence-transformers</code></td><td>Embeddings alternativos a Ollama</td><td>F6</td><td><span class="b b-g">OPCIONAL</span></td></tr>
      <tr><td><code>TTS</code> (Coqui)</td><td>XTTS v2 — clonación de voz</td><td>F6</td><td><span class="b b-g">OPCIONAL</span></td></tr>
    </tbody>
  </table>

  <div class="call call-warn">
    <div class="call-t">Entorno virtual recomendado</div>
    <p>Crear un <code>venv</code> dedicado para los sidecars de Elfie para evitar conflictos con otros proyectos Python:</p>
  </div>
  <div class="code">
python -m venv elfie-desktop\venv
.\elfie-desktop\venv\Scripts\activate
pip install faster-whisper pyaudio pvporcupine kokoro-onnx onnxruntime-gpu edge-tts numpy scipy soundfile</div>
</div>

<!-- ══════════ 10 · RAG ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">10</div><div class="sec-t">RAG Local — LanceDB (Fase 6)</div></div>

  <div class="call call-info">
    <div class="call-t">Alcance definido</div>
    <p>RAG solo se usa para el módulo <strong>Apuntes</strong>. El resto de los módulos (tareas, gym, finanzas, dieta)
    son datos estructurados que el LLM consulta directamente vía SQL. RAG no aporta nada sobre ellos.</p>
  </div>

  <h3>LanceDB</h3>
  <table>
    <thead><tr><th>Dato</th><th>Valor</th></tr></thead>
    <tbody>
      <tr><td>Instalación Python</td><td><code>pip install lancedb</code></td></tr>
      <tr><td>Crate Rust</td><td><code>lancedb = "0.9"</code> (alternativa nativa)</td></tr>
      <tr><td>Tipo</td><td>Vector store embebido — como SQLite pero para vectores semánticos</td></tr>
      <tr><td>Almacenamiento</td><td>En disco local: <code>elfie-desktop/db/apuntes.lance/</code></td></tr>
      <tr><td>Sin servidor</td><td>No requiere Docker, proceso separado ni configuración</td></tr>
      <tr><td>Privacidad</td><td>Las notas nunca salen de la computadora</td></tr>
      <tr><td>Prioridad</td><td><span class="b b-g">OPCIONAL</span> — solo Fase 6</td></tr>
    </tbody>
  </table>

  <h3>Motor de embeddings</h3>
  <table>
    <thead><tr><th>Opción</th><th>Instalación</th><th>Ventaja</th><th>VRAM</th></tr></thead>
    <tbody>
      <tr><td><strong>nomic-embed-text via Ollama</strong></td><td><code>ollama pull nomic-embed-text</code></td><td>Ya en el stack de Ollama, sin paquete extra</td><td>~270 MB</td></tr>
      <tr><td>sentence-transformers</td><td><code>pip install sentence-transformers</code></td><td>Más opciones de modelos multilingüe</td><td>~500 MB</td></tr>
    </tbody>
  </table>
</div>

<!-- ══════════ 11 · SUPABASE ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">11</div><div class="sec-t">Supabase — Migraciones Nuevas</div></div>

  <h3>CLI de Supabase</h3>
  <div class="code">
<span class="cm"># Verificar que está instalado</span>
supabase --version

<span class="cm"># Si no está instalado (Windows, con scoop)</span>
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase</div>

  <h3>Nuevas migraciones a crear y aplicar</h3>
  <div class="code">
<span class="cm"># Crear las migraciones (en orden)</span>
supabase migration new elfie_config        <span class="cm"># tabla configuración de personalidad y voz</span>
supabase migration new voice_profiles      <span class="cm"># perfiles de voz clonados</span>
supabase migration new system_actions      <span class="cm"># log de acciones del SO</span>
supabase migration new system_metrics      <span class="cm"># historial CPU/GPU/RAM</span>
supabase migration new routines            <span class="cm"># Routine Engine Visual</span>

<span class="cm"># Aplicar a la BD de producción</span>
supabase db push</div>

  <table>
    <thead><tr><th>Migración</th><th>Tabla</th><th>Fase</th><th>Descripción</th></tr></thead>
    <tbody>
      <tr><td>0012_elfie_config</td><td><code>elfie_config</code></td><td>F4</td><td>Personalidad, motor de voz, modelo LLM local</td></tr>
      <tr><td>0013_voice_profiles</td><td><code>voice_profiles</code></td><td>F6</td><td>Perfiles de voz clonados (XTTS v2)</td></tr>
      <tr><td>0014_system_actions</td><td><code>system_actions</code></td><td>F2</td><td>Log de acciones del SO (abrir apps, volumen...)</td></tr>
      <tr><td>0015_system_metrics</td><td><code>system_metrics</code></td><td>F2</td><td>Historial de métricas para gráficas</td></tr>
      <tr><td>0016_routines</td><td><code>routines</code></td><td>F5</td><td>Rutinas configurables del Routine Engine</td></tr>
    </tbody>
  </table>
</div>

<!-- ══════════ 12 · CUENTAS Y KEYS ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">12</div><div class="sec-t">Cuentas y API Keys</div></div>

  <table>
    <thead><tr><th>Servicio</th><th>Para qué</th><th>Estado</th><th>Costo</th><th>Acción requerida</th></tr></thead>
    <tbody>
      <tr><td><strong>Anthropic</strong></td><td>Claude API (briefing, insights)</td><td><span class="b b-g">YA CONFIGURADO</span></td><td>Ya pagado</td><td>Ninguna</td></tr>
      <tr><td><strong>Supabase</strong></td><td>Base de datos compartida</td><td><span class="b b-g">YA CONFIGURADO</span></td><td>Plan gratuito</td><td>Ninguna</td></tr>
      <tr><td><strong>Google Cloud</strong></td><td>Google Calendar (recordatorios)</td><td><span class="b b-g">YA CONFIGURADO</span></td><td>Gratuito</td><td>Agregar localhost + URL Tauri a orígenes autorizados</td></tr>
      <tr><td><strong>Picovoice Console</strong></td><td>AccessKey para Porcupine wake word</td><td><span class="b b-r">PENDIENTE</span></td><td>Gratuito</td><td>Registrarse en console.picovoice.ai · entrenar modelo "Dalia"</td></tr>
      <tr><td><strong>NVIDIA Developer</strong></td><td>Descargar cuDNN</td><td><span class="b b-y">PENDIENTE</span></td><td>Gratuito</td><td>Registrarse en developer.nvidia.com</td></tr>
      <tr><td><strong>ElevenLabs</strong></td><td>TTS premium (voz clonada cloud)</td><td><span class="b b-g">OPCIONAL</span></td><td>$5–22/mes</td><td>Solo si se quiere TTS cloud de alta calidad</td></tr>
      <tr><td><strong>Hugging Face</strong></td><td>Descargar modelo Whisper ggml</td><td><span class="b b-g">SIN CUENTA</span></td><td>Gratuito</td><td>Descarga directa sin registro</td></tr>
    </tbody>
  </table>

  <div class="call call-warn">
    <div class="call-t">Google Cloud — actualizar orígenes autorizados</div>
    <p>El ID de cliente OAuth actual (<code>config.js</code>) tiene autorizados <code>https://tu-app.vercel.app</code>
    y <code>http://localhost:3210</code>. Tauri expone el WebView en un origen diferente (<code>tauri://localhost</code>).
    Agregar <code>tauri://localhost</code> a los orígenes JS autorizados en Google Cloud Console para que
    el módulo de Recordatorios siga funcionando en el desktop.</p>
  </div>
</div>

<!-- ══════════ 13 · CONSIDERACIONES ══════════ -->
<div class="page">
  <div class="sec-head"><div class="sec-n">13</div><div class="sec-t">Consideraciones Extras y Posibles Problemas</div></div>

  <h3>Windows Defender / Antivirus</h3>
  <div class="call call-warn">
    <div class="call-t">Falsos positivos esperados</div>
    <p>Ollama, los ejecutables de Tauri compilados localmente y los binarios de Piper/Porcupine pueden ser marcados
    como amenaza por Windows Defender al primer uso. Solución: agregar las carpetas del proyecto a las
    exclusiones de Defender antes de compilar.</p>
  </div>
  <div class="code">
<span class="cm"># PowerShell (como Administrador) — agregar exclusiones a Defender</span>
Add-MpPreference -ExclusionPath "C:\Users\Sylft\Desktop\Projects\mi-app-PRTS"
Add-MpPreference -ExclusionPath "C:\Users\Sylft\.ollama"
Add-MpPreference -ExclusionPath "C:\Users\Sylft\.cargo"</div>

  <h3>Puerto 11434 (Ollama)</h3>
  <p>Ollama corre en <code>localhost:11434</code>. Verificar que ningún otro proceso usa ese puerto.
  No requiere reglas de firewall externas — solo comunicación local entre Tauri y Ollama.</p>

  <h3>Micrófono en segundo plano (Porcupine)</h3>
  <p>Cuando la escucha continua está activa, Windows mostrará el ícono de micrófono en la barra de tareas
  permanentemente — mismo comportamiento que el <code>wakeword.js</code> actual en el navegador.
  Es el comportamiento esperado y correcto.</p>

  <h3>Primer build de Tauri — Tiempo estimado</h3>
  <table>
    <thead><tr><th>Operación</th><th>Primera vez</th><th>Siguientes</th></tr></thead>
    <tbody>
      <tr><td><code>cargo build</code> (debug)</td><td>10–20 min (descarga + compila crates)</td><td>~30 s (incremental)</td></tr>
      <tr><td><code>cargo build --release</code></td><td>20–40 min</td><td>~2–5 min</td></tr>
      <tr><td><code>npm run tauri dev</code></td><td>15–25 min</td><td>~1 min</td></tr>
    </tbody>
  </table>

  <h3>Checklist de Instalación por Fase</h3>
  <h4>Fase 0–1 (Setup + Core Desktop)</h4>
  <div class="chk">Rust (rustup.rs)</div>
  <div class="chk">Node.js LTS</div>
  <div class="chk">Microsoft C++ Build Tools</div>
  <div class="chk">Tauri CLI (<code>npm install -g @tauri-apps/cli@^2</code>)</div>
  <div class="chk">VS Code + extensiones (rust-analyzer, Tauri)</div>
  <div class="chk">Drivers NVIDIA (verificar soporte RTX 5060 en Windows 10)</div>

  <h4>Fase 2 (Control del Sistema)</h4>
  <div class="chk">nvml-wrapper en Cargo.toml</div>
  <div class="chk">sysinfo en Cargo.toml</div>
  <div class="chk">windows crate en Cargo.toml</div>

  <h4>Fase 3 (Voz Local)</h4>
  <div class="chk">CUDA Toolkit 12.x</div>
  <div class="chk">LLVM/Clang (<code>winget install LLVM.LLVM</code>)</div>
  <div class="chk">Python 3.11</div>
  <div class="chk">pip: faster-whisper · pyaudio · pvporcupine · kokoro-onnx · onnxruntime-gpu · edge-tts</div>
  <div class="chk">Modelo Whisper ggml-large-v3-turbo.bin descargado</div>
  <div class="chk">Cuenta Picovoice + AccessKey + modelo "Dalia" .ppn</div>
  <div class="chk">tauri://localhost agregado a orígenes Google Cloud</div>

  <h4>Fase 4 (IA Local)</h4>
  <div class="chk">Ollama instalado y verificado con GPU</div>
  <div class="chk"><code>ollama pull phi3.5</code> (primero, para validar)</div>
  <div class="chk"><code>ollama pull qwen2.5:7b</code></div>

  <h4>Fase 6 (RAG + Clonación de voz)</h4>
  <div class="chk">pip: lancedb · sentence-transformers</div>
  <div class="chk"><code>ollama pull nomic-embed-text</code></div>
  <div class="chk">pip: TTS (Coqui, para XTTS v2)</div>
  <div class="chk">cuDNN instalado y configurado</div>

  <hr class="divider" style="margin-top:18pt">
  <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:14pt">
    <div>
      <div style="font-family:'Courier New',monospace;font-size:7.5pt;color:#4a90b8;letter-spacing:1px;text-transform:uppercase;">Elfie · PRTS Desktop Edition — Lista de Requisitos v1.0</div>
      <div style="font-family:'Courier New',monospace;font-size:7pt;color:#8a9ab0;margin-top:2pt;">Junio 2026 · Uso personal exclusivo · Sylft</div>
    </div>
    <div style="font-family:Georgia,serif;font-size:28pt;font-weight:700;color:#eef4fa;">Elfie</div>
  </div>
</div>

</body>
</html>"""

import os, sys

html_content = HTML
out = "/home/user/mi-app-PRTS/docs/Elfie_PRTS_Requisitos_v1.0.pdf"

try:
    from weasyprint import HTML
    print("Generando PDF...")
    HTML(string=html_content, base_url="/").write_pdf(out)
    print(f"OK → {out}  ({os.path.getsize(out)/1024:.0f} KB)")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr); sys.exit(1)

// app/elfie/monitor.js — Panel de monitor completo (Fase 5).
// Live (CPU/RAM/GPU/VRAM/temp/power/disco) + gráfica de historial (Chart.js) +
// top procesos. Historial en memoria (últimos N samples); persistencia best-effort
// a system_metrics cada ~60s. Solo Tauri (usa elfie:metrics y get_processes).
(function () {
  "use strict";
  const T = window.__TAURI__;
  if (!T) return;
  const invoke = T.core.invoke;
  const listen = T.event.listen;

  const HIST = 60; // ~3 min a 3s
  const hist = { lab: [], cpu: [], gpu: [], ram: [] };
  let chart = null,
    open = false,
    procTimer = null,
    persistN = 0,
    last = null;

  function pushHist(m) {
    hist.lab.push("");
    hist.cpu.push(+(m.cpu_percent || 0).toFixed(1));
    hist.gpu.push(m.gpu_percent != null ? m.gpu_percent : null);
    hist.ram.push(m.ram_total_gb ? +((m.ram_used_gb / m.ram_total_gb) * 100).toFixed(1) : 0);
    ["lab", "cpu", "gpu", "ram"].forEach((k) => { if (hist[k].length > HIST) hist[k].shift(); });
  }

  function persist(m) {
    if (!window.sb) return;
    const cfg = window.ElfieConfig && window.ElfieConfig.data.features;
    if (cfg && cfg.monitor === false) return; // monitor desactivado → no persistir

    window.sb
      .from("system_metrics")
      .insert({
        cpu_percent: m.cpu_percent,
        ram_used_gb: m.ram_used_gb,
        gpu_percent: m.gpu_percent,
        gpu_vram_used_gb: m.gpu_vram_used_gb,
        gpu_temp_c: m.gpu_temp_c,
        gpu_power_w: m.gpu_power_w,
      })
      .then(() => {}, () => {});
  }

  listen("elfie:metrics", (e) => {
    const m = e.payload;
    last = m;
    pushHist(m);
    if (open) {
      updateLive(m);
      if (chart) { chart.data.labels = hist.lab; chart.update("none"); }
    }
    if (++persistN >= 20) { persistN = 0; persist(m); } // ~cada 60s
  });

  const h = (tag, css, props) => {
    const el = document.createElement(tag);
    if (css) el.style.cssText = css;
    Object.assign(el, props || {});
    return el;
  };
  const pct = (v) => Math.max(0, Math.min(100, Math.round(v || 0)));

  function statRow(label, value, p) {
    const row = h("div", "display:flex;align-items:center;gap:10px;margin:5px 0;font:12px/1.4 ui-monospace,monospace");
    const hue = p < 60 ? 335 : p < 85 ? 20 : 0;
    row.append(
      h("span", "width:52px;opacity:.7;text-transform:uppercase;font-size:10px;letter-spacing:.06em", { textContent: label }),
      (() => {
        const track = h("span", "flex:1;height:7px;border-radius:4px;background:rgba(185,150,168,.16);overflow:hidden");
        track.appendChild(h("span", `display:block;height:100%;width:${pct(p)}%;background:hsl(${hue} 70% 55%)`));
        return track;
      })(),
      h("span", "min-width:96px;text-align:right;opacity:.9", { textContent: value })
    );
    return row;
  }

  function updateLive(m) {
    const box = document.getElementById("mon-live");
    if (!box) return;
    box.innerHTML = "";
    box.appendChild(statRow("CPU", `${(m.cpu_percent || 0).toFixed(0)} %`, m.cpu_percent));
    const ramP = m.ram_total_gb ? (m.ram_used_gb / m.ram_total_gb) * 100 : 0;
    box.appendChild(statRow("RAM", `${(m.ram_used_gb || 0).toFixed(1)} / ${(m.ram_total_gb || 0).toFixed(0)} GB`, ramP));
    if (m.gpu_percent != null) {
      box.appendChild(statRow("GPU", `${m.gpu_percent} %`, m.gpu_percent));
      const vP = m.gpu_vram_total_gb ? (m.gpu_vram_used_gb / m.gpu_vram_total_gb) * 100 : 0;
      box.appendChild(statRow("VRAM", `${(m.gpu_vram_used_gb || 0).toFixed(1)} / ${(m.gpu_vram_total_gb || 0).toFixed(0)} GB`, vP));
      const extra = [];
      if (m.gpu_temp_c != null) extra.push(`${m.gpu_temp_c}°C`);
      if (m.gpu_power_w != null) extra.push(`${m.gpu_power_w.toFixed(0)} W`);
      if (extra.length) box.appendChild(h("div", "text-align:right;opacity:.55;font:11px ui-monospace,monospace", { textContent: extra.join("  ·  ") }));
    } else {
      box.appendChild(h("div", "opacity:.45;font:11px ui-monospace,monospace", { textContent: "GPU: NVML no disponible" }));
    }
    if (m.disk_total_gb != null) {
      const used = m.disk_total_gb - m.disk_free_gb;
      box.appendChild(statRow("Disco C", `${m.disk_free_gb.toFixed(0)} GB libres`, (used / m.disk_total_gb) * 100));
    }
  }

  async function refreshProcs() {
    const tbody = document.getElementById("mon-procs");
    if (!tbody) return;
    try {
      const procs = await invoke("get_processes");
      tbody.innerHTML = "";
      procs.forEach((p) => {
        const tr = h("tr", "border-top:1px solid rgba(185,150,168,.1)");
        const td = (t, css) => h("td", "padding:4px 6px;" + (css || ""), { textContent: t });
        tr.append(
          td(p.name, "max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"),
          td(`${p.cpu.toFixed(0)}%`, "text-align:right;opacity:.85"),
          td(`${p.mem_mb.toFixed(0)} MB`, "text-align:right;opacity:.7")
        );
        tbody.appendChild(tr);
      });
    } catch (_) {}
  }

  function buildChart() {
    const cv = document.getElementById("mon-chart");
    if (!cv || !window.Chart) return;
    chart = new window.Chart(cv.getContext("2d"), {
      type: "line",
      data: {
        labels: hist.lab,
        datasets: [
          { label: "CPU", data: hist.cpu, borderColor: "#E68AA2", borderWidth: 1.5, pointRadius: 0, tension: 0.3 },
          { label: "GPU", data: hist.gpu, borderColor: "#E0626C", borderWidth: 1.5, pointRadius: 0, tension: 0.3 },
          { label: "RAM", data: hist.ram, borderColor: "#ADA3AA", borderWidth: 1.5, pointRadius: 0, tension: 0.3 },
        ],
      },
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { min: 0, max: 100, ticks: { color: "#ADA3AA", font: { size: 9 } }, grid: { color: "rgba(185,150,168,.1)" } }, x: { display: false } },
        plugins: { legend: { labels: { color: "#ECE8EA", font: { size: 10 }, boxWidth: 12 } } },
      },
    });
  }

  function openMonitor() {
    let modal = document.getElementById("monitor-modal");
    if (modal) { modal.style.display = "flex"; open = true; if (last) updateLive(last); refreshProcs(); procTimer = setInterval(refreshProcs, 3000); return; }
    modal = h("div", "position:fixed;inset:0;z-index:10000;display:flex;align-items:center;justify-content:center;background:rgba(6,10,18,.6);backdrop-filter:blur(3px)");
    modal.id = "monitor-modal";
    modal.addEventListener("click", (e) => { if (e.target === modal) closeMonitor(); });
    const card = h("div", "width:min(620px,94vw);max-height:88vh;overflow:auto;background:#161416;color:#ECE8EA;border:1px solid rgba(185,150,168,.25);border-radius:14px;padding:18px 20px;box-shadow:0 20px 60px rgba(0,0,0,.5)");
    const head = h("div", "display:flex;justify-content:space-between;align-items:center;margin-bottom:12px");
    head.append(
      h("div", "font-family:Georgia,serif;font-size:18px", { textContent: "Monitor del sistema" }),
      h("button", "background:transparent;color:#ADA3AA;border:none;font-size:20px;cursor:pointer", { textContent: "×", onclick: closeMonitor })
    );
    card.appendChild(head);
    card.appendChild(h("div", "", { id: "mon-live" }));
    const chartWrap = h("div", "height:160px;margin:14px 0 6px");
    chartWrap.appendChild(h("canvas", "", { id: "mon-chart" }));
    card.appendChild(chartWrap);
    card.appendChild(h("div", "font:10px ui-monospace,monospace;text-transform:uppercase;letter-spacing:.08em;opacity:.6;margin:8px 0 4px", { textContent: "Top procesos" }));
    const table = h("table", "width:100%;border-collapse:collapse;font:12px ui-monospace,monospace");
    const thead = h("thead");
    const htr = h("tr", "opacity:.5;text-align:left;font-size:10px");
    htr.append(h("th", "padding:2px 6px", { textContent: "PROCESO" }), h("th", "padding:2px 6px;text-align:right", { textContent: "CPU" }), h("th", "padding:2px 6px;text-align:right", { textContent: "MEM" }));
    thead.appendChild(htr);
    table.appendChild(thead);
    table.appendChild(h("tbody", "", { id: "mon-procs" }));
    card.appendChild(table);
    modal.appendChild(card);
    document.body.appendChild(modal);
    open = true;
    buildChart();
    if (last) updateLive(last);
    refreshProcs();
    procTimer = setInterval(refreshProcs, 3000);
  }

  function closeMonitor() {
    const modal = document.getElementById("monitor-modal");
    if (modal) modal.style.display = "none";
    open = false;
    if (procTimer) { clearInterval(procTimer); procTimer = null; }
  }

  window.elfieMonitor = { open: openMonitor, close: closeMonitor };
})();

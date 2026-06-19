// monitor.rs — Métricas del sistema (CPU/RAM vía sysinfo, GPU RTX 5060 vía NVML).
// Emite "elfie:metrics" cada 3 s al frontend; get_metrics() da una lectura puntual.
use nvml_wrapper::{enum_wrappers::device::TemperatureSensor, Nvml};
use serde::Serialize;
use std::time::Duration;
use sysinfo::System;
use tauri::{AppHandle, Emitter};

#[derive(Serialize, Clone, Default)]
pub struct Metrics {
    pub cpu_percent: f32,
    pub ram_used_gb: f32,
    pub ram_total_gb: f32,
    pub gpu_percent: Option<u32>,
    pub gpu_vram_used_gb: Option<f32>,
    pub gpu_vram_total_gb: Option<f32>,
    pub gpu_temp_c: Option<u32>,
    pub gpu_power_w: Option<f32>,
    pub disk_free_gb: Option<f32>,
    pub disk_total_gb: Option<f32>,
}

#[derive(Serialize, Clone)]
pub struct ProcInfo {
    pub pid: u32,
    pub name: String,
    pub cpu: f32,
    pub mem_mb: f32,
}

fn gb(bytes: u64) -> f32 {
    (bytes as f64 / 1_073_741_824.0) as f32
}

/// Lee la GPU 0 si NVML inicializó (degrada a None si no hay driver/tarjeta).
fn read_gpu(nvml: &Option<Nvml>, m: &mut Metrics) {
    let Some(nvml) = nvml else { return };
    let Ok(dev) = nvml.device_by_index(0) else { return };
    if let Ok(u) = dev.utilization_rates() {
        m.gpu_percent = Some(u.gpu);
    }
    if let Ok(mem) = dev.memory_info() {
        m.gpu_vram_used_gb = Some(gb(mem.used));
        m.gpu_vram_total_gb = Some(gb(mem.total));
    }
    if let Ok(t) = dev.temperature(TemperatureSensor::Gpu) {
        m.gpu_temp_c = Some(t);
    }
    if let Ok(p) = dev.power_usage() {
        m.gpu_power_w = Some(p as f32 / 1000.0);
    }
}

fn read_disk(m: &mut Metrics) {
    let disks = sysinfo::Disks::new_with_refreshed_list();
    for d in &disks {
        if d.mount_point().to_string_lossy().starts_with("C:") {
            m.disk_free_gb = Some(gb(d.available_space()));
            m.disk_total_gb = Some(gb(d.total_space()));
            return;
        }
    }
    if let Some(d) = disks.iter().next() {
        m.disk_free_gb = Some(gb(d.available_space()));
        m.disk_total_gb = Some(gb(d.total_space()));
    }
}

fn snapshot(sys: &System, nvml: &Option<Nvml>) -> Metrics {
    let mut m = Metrics {
        cpu_percent: sys.global_cpu_usage(),
        ram_used_gb: gb(sys.used_memory()),
        ram_total_gb: gb(sys.total_memory()),
        ..Default::default()
    };
    read_gpu(nvml, &mut m);
    read_disk(&mut m);
    m
}

/// Top procesos por CPU (bajo demanda; no en el emisor de 3 s para no cargar el hilo).
#[tauri::command]
pub fn get_processes() -> Vec<ProcInfo> {
    use sysinfo::ProcessesToUpdate;
    let mut sys = System::new();
    sys.refresh_processes(ProcessesToUpdate::All, true);
    std::thread::sleep(sysinfo::MINIMUM_CPU_UPDATE_INTERVAL);
    sys.refresh_processes(ProcessesToUpdate::All, true);
    let mut v: Vec<ProcInfo> = sys
        .processes()
        .iter()
        .map(|(pid, p)| ProcInfo {
            pid: pid.as_u32(),
            name: p.name().to_string_lossy().to_string(),
            cpu: p.cpu_usage(),
            mem_mb: (p.memory() as f64 / 1_048_576.0) as f32,
        })
        .collect();
    v.sort_by(|a, b| b.cpu.partial_cmp(&a.cpu).unwrap_or(std::cmp::Ordering::Equal));
    v.truncate(8);
    v
}

/// Lectura puntual (para el dashboard al abrir, sin esperar al tick de 3 s).
#[tauri::command]
pub fn get_metrics() -> Metrics {
    let mut sys = System::new_all();
    sys.refresh_cpu_usage();
    std::thread::sleep(sysinfo::MINIMUM_CPU_UPDATE_INTERVAL);
    sys.refresh_cpu_usage();
    sys.refresh_memory();
    let nvml = Nvml::init().ok();
    snapshot(&sys, &nvml)
}

/// Hilo en segundo plano: emite métricas cada 3 s mientras la app vive.
pub fn start(app: AppHandle) {
    std::thread::spawn(move || {
        let mut sys = System::new_all();
        let nvml = Nvml::init().ok();
        loop {
            sys.refresh_cpu_usage();
            std::thread::sleep(Duration::from_secs(3));
            sys.refresh_cpu_usage();
            sys.refresh_memory();
            let _ = app.emit("elfie:metrics", snapshot(&sys, &nvml));
        }
    });
}

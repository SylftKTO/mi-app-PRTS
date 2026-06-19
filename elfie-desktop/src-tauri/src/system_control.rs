// system_control.rs — Control nativo del SO (Fase 2). Sin volumen/screenshot aún (2b/2c).
use arboard::Clipboard;
use std::process::Command;

/// Alias → ejecutable/protocolo. El frontend (LAUNCHERS) ya tiene su mapa; aquí
/// cubrimos lo común para "Elfie, abre X". Si no está, se intenta el nombre tal cual.
fn resolve_app(name: &str) -> String {
    match name.trim().to_lowercase().as_str() {
        "discord" => "discord:".into(),
        "spotify" => "spotify:".into(),
        "steam" => "steam:".into(),
        "whatsapp" => "whatsapp:".into(),
        "vscode" | "vs code" | "code" => "code".into(),
        "explorer" | "explorador" | "archivos" => "explorer".into(),
        "navegador" | "chrome" => "chrome".into(),
        "edge" => "msedge".into(),
        other => other.into(),
    }
}

/// Lanza una app por nombre/alias o protocolo. Usa `start` para resolver vía
/// App Paths del registro y manejadores de protocolo (discord:, spotify:...).
#[tauri::command]
pub fn open_app(name: String) -> Result<(), String> {
    let target = resolve_app(&name);
    Command::new("cmd")
        .args(["/C", "start", "", &target])
        .spawn()
        .map(|_| ())
        .map_err(|e| e.to_string())
}

/// Termina procesos por nombre de imagen (sin extensión). "Elfie, cierra Steam".
#[tauri::command]
pub fn kill_process(name: String) -> Result<(), String> {
    let image = if name.to_lowercase().ends_with(".exe") {
        name
    } else {
        format!("{name}.exe")
    };
    let out = Command::new("taskkill")
        .args(["/IM", &image, "/F"])
        .output()
        .map_err(|e| e.to_string())?;
    if out.status.success() {
        Ok(())
    } else {
        Err(String::from_utf8_lossy(&out.stderr).trim().to_string())
    }
}

/// Abre una carpeta en el Explorador de Windows.
#[tauri::command]
pub fn open_folder(path: String) -> Result<(), String> {
    // explorer.exe devuelve códigos != 0 incluso al abrir bien → ignoramos el status.
    Command::new("explorer")
        .arg(&path)
        .spawn()
        .map(|_| ())
        .map_err(|e| e.to_string())
}

/// Apagar / reiniciar / suspender. "Elfie, suspende la computadora".
#[tauri::command]
pub fn power_action(action: String) -> Result<(), String> {
    let mut cmd = match action.trim().to_lowercase().as_str() {
        "shutdown" | "apagar" => {
            let mut c = Command::new("shutdown");
            c.args(["/s", "/t", "0"]);
            c
        }
        "restart" | "reiniciar" => {
            let mut c = Command::new("shutdown");
            c.args(["/r", "/t", "0"]);
            c
        }
        "suspend" | "suspender" | "dormir" => {
            let mut c = Command::new("rundll32");
            c.args(["powrprof.dll,SetSuspendState", "0,1,0"]);
            c
        }
        other => return Err(format!("acción de energía desconocida: {other}")),
    };
    cmd.spawn().map(|_| ()).map_err(|e| e.to_string())
}

// --- Volumen maestro del sistema (Fase 2b · Windows Core Audio) ---
#[cfg(windows)]
mod audio_win {
    use windows::core::Result;
    use windows::Win32::Media::Audio::Endpoints::IAudioEndpointVolume;
    use windows::Win32::Media::Audio::{
        eConsole, eRender, IMMDeviceEnumerator, MMDeviceEnumerator,
    };
    use windows::Win32::System::Com::{
        CoCreateInstance, CoInitializeEx, CoUninitialize, CLSCTX_ALL, COINIT_APARTMENTTHREADED,
    };

    /// Garantiza CoUninitialize al salir del scope (incluso ante error).
    struct ComGuard;
    impl Drop for ComGuard {
        fn drop(&mut self) {
            unsafe { CoUninitialize() }
        }
    }

    unsafe fn endpoint() -> Result<IAudioEndpointVolume> {
        let enumerator: IMMDeviceEnumerator =
            CoCreateInstance(&MMDeviceEnumerator, None, CLSCTX_ALL)?;
        let device = enumerator.GetDefaultAudioEndpoint(eRender, eConsole)?;
        device.Activate(CLSCTX_ALL, None)
    }

    pub fn set_volume(level: u8) -> Result<()> {
        unsafe {
            CoInitializeEx(None, COINIT_APARTMENTTHREADED).ok()?;
            let v = endpoint()?;
            let _g = ComGuard;
            v.SetMasterVolumeLevelScalar((level.min(100) as f32) / 100.0, std::ptr::null())
        }
    }

    pub fn get_volume() -> Result<u8> {
        unsafe {
            CoInitializeEx(None, COINIT_APARTMENTTHREADED).ok()?;
            let v = endpoint()?;
            let _g = ComGuard;
            Ok((v.GetMasterVolumeLevelScalar()? * 100.0).round() as u8)
        }
    }

    pub fn toggle_mute() -> Result<bool> {
        unsafe {
            CoInitializeEx(None, COINIT_APARTMENTTHREADED).ok()?;
            let v = endpoint()?;
            let _g = ComGuard;
            let next = !v.GetMute()?.as_bool();
            v.SetMute(next, std::ptr::null())?;
            Ok(next)
        }
    }
}

/// Volumen maestro 0–100. "Elfie, sube el volumen a 60".
#[tauri::command]
pub fn set_volume(level: u8) -> Result<(), String> {
    #[cfg(windows)]
    {
        audio_win::set_volume(level).map_err(|e| e.to_string())
    }
    #[cfg(not(windows))]
    {
        let _ = level;
        Err("control de volumen solo en Windows".into())
    }
}

/// Volumen actual 0–100.
#[tauri::command]
pub fn get_volume() -> Result<u8, String> {
    #[cfg(windows)]
    {
        audio_win::get_volume().map_err(|e| e.to_string())
    }
    #[cfg(not(windows))]
    {
        Err("control de volumen solo en Windows".into())
    }
}

/// Silenciar/activar. Devuelve el nuevo estado (true = silenciado). "Elfie, silencia".
#[tauri::command]
pub fn mute_toggle() -> Result<bool, String> {
    #[cfg(windows)]
    {
        audio_win::toggle_mute().map_err(|e| e.to_string())
    }
    #[cfg(not(windows))]
    {
        Err("control de volumen solo en Windows".into())
    }
}

/// Captura del monitor primario → PNG en %USERPROFILE%\Pictures\Elfie\.
/// Si to_clipboard, además copia la imagen al portapapeles. Devuelve la ruta del archivo.
#[tauri::command]
pub fn screenshot(to_clipboard: bool) -> Result<String, String> {
    use xcap::Monitor;

    let monitors = Monitor::all().map_err(|e| e.to_string())?;
    let monitor = monitors
        .iter()
        .find(|m| m.is_primary().unwrap_or(false))
        .or_else(|| monitors.first())
        .ok_or("no se encontró ningún monitor")?;
    let img = monitor.capture_image().map_err(|e| e.to_string())?;

    let base = std::env::var("USERPROFILE").map_err(|e| e.to_string())?;
    let dir = std::path::Path::new(&base).join("Pictures").join("Elfie");
    std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    let ms = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    let path = dir.join(format!("elfie-{ms}.png"));
    img.save(&path).map_err(|e| e.to_string())?;

    if to_clipboard {
        use std::borrow::Cow;
        let (w, h) = (img.width() as usize, img.height() as usize);
        let data = arboard::ImageData {
            width: w,
            height: h,
            bytes: Cow::from(img.into_raw()),
        };
        Clipboard::new()
            .and_then(|mut c| c.set_image(data))
            .map_err(|e| e.to_string())?;
    }

    Ok(path.to_string_lossy().into_owned())
}

#[tauri::command]
pub fn clipboard_read() -> Result<String, String> {
    Clipboard::new()
        .and_then(|mut c| c.get_text())
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn clipboard_write(text: String) -> Result<(), String> {
    Clipboard::new()
        .and_then(|mut c| c.set_text(text))
        .map_err(|e| e.to_string())
}

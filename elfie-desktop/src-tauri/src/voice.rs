// voice.rs — Ciclo de vida del sidecar de voz (Python: faster-whisper + Kokoro).
// Lo lanza al arrancar y lo mata al salir. El WebView le habla por HTTP localhost.
use std::process::{Child, Command};
use std::sync::Mutex;

/// Estado gestionado por Tauri: el proceso hijo del sidecar.
pub struct Sidecar(pub Mutex<Option<Child>>);

/// Lanza el sidecar usando el Python del venv dedicado (venv-voice).
pub fn spawn() -> Option<Child> {
    // CARGO_MANIFEST_DIR = .../elfie-desktop/src-tauri  →  raíz = .../elfie-desktop
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).parent()?;
    let py = root.join("venv-voice").join("Scripts").join("python.exe");
    let script = root.join("sidecars").join("voice_server.py");

    if !py.exists() || !script.exists() {
        eprintln!(
            "[elfie] sidecar de voz no encontrado (py={}, script={})",
            py.display(),
            script.display()
        );
        return None;
    }

    match Command::new(&py).arg(&script).spawn() {
        Ok(child) => {
            println!("[elfie] sidecar de voz lanzado (pid {})", child.id());
            Some(child)
        }
        Err(e) => {
            eprintln!("[elfie] no se pudo lanzar el sidecar de voz: {e}");
            None
        }
    }
}

/// Mata el sidecar si sigue vivo (llamado al salir la app).
pub fn kill(state: &Sidecar) {
    if let Ok(mut guard) = state.0.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
        }
    }
}

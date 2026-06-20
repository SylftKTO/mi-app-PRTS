use tauri::{
    menu::{Menu, MenuItem, PredefinedMenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Emitter, Manager, WindowEvent,
};
use tauri_plugin_notification::NotificationExt;

mod monitor;
mod system_control;
mod voice;

/// Notificación nativa de Windows disparada desde el frontend (Realtime, recordatorios).
#[tauri::command]
fn elfie_notify(app: tauri::AppHandle, title: String, body: String) -> Result<(), String> {
    app.notification()
        .builder()
        .title(title)
        .body(body)
        .show()
        .map_err(|e| e.to_string())
}

/// Muestra y enfoca la ventana principal; si está oculta, la revela.
fn show_main(app: &tauri::AppHandle) {
    if let Some(win) = app.get_webview_window("main") {
        let _ = win.show();
        let _ = win.unminimize();
        let _ = win.set_focus();
    }
}

/// Alterna visibilidad de la ventana principal (toggle desde el tray).
fn toggle_main(app: &tauri::AppHandle) {
    if let Some(win) = app.get_webview_window("main") {
        match win.is_visible() {
            Ok(true) => {
                let _ = win.hide();
            }
            _ => show_main(app),
        }
    }
}

/// Alterna pantalla completa de la ventana principal. Devuelve el nuevo estado.
fn fullscreen_toggle(app: &tauri::AppHandle) -> bool {
    if let Some(win) = app.get_webview_window("main") {
        let now = win.is_fullscreen().unwrap_or(false);
        let _ = win.set_fullscreen(!now);
        let _ = win.set_focus();
        // Notifica al frontend el nuevo estado para mantener sincronizados
        // todos los puntos de entrada (F11, Escape, ítem del tray).
        let _ = app.emit("elfie:fullscreen", !now);
        !now
    } else {
        false
    }
}

/// Comando expuesto al frontend (F11 / menú del tray) para pantalla completa.
#[tauri::command]
fn toggle_fullscreen(app: tauri::AppHandle) -> bool {
    fullscreen_toggle(&app)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default();

    // Atajos globales (solo escritorio): Ctrl+Space = captura, Alt+E = voz,
    // Ctrl+Shift+R = rutina rápida. Emiten eventos que el frontend escucha.
    #[cfg(desktop)]
    {
        use tauri_plugin_global_shortcut::{Code, Modifiers, Shortcut, ShortcutState};

        let sc_capture = Shortcut::new(Some(Modifiers::CONTROL), Code::Space);
        let sc_voice = Shortcut::new(Some(Modifiers::ALT), Code::KeyE);
        let sc_routine =
            Shortcut::new(Some(Modifiers::CONTROL | Modifiers::SHIFT), Code::KeyR);

        builder = builder.plugin(
            tauri_plugin_global_shortcut::Builder::new()
                .with_shortcuts([sc_capture, sc_voice, sc_routine])
                .expect("atajos globales válidos")
                .with_handler(move |app, shortcut, event| {
                    let pressed = event.state() == ShortcutState::Pressed;
                    if shortcut == &sc_voice {
                        // Push-to-talk: mantener Alt+E graba; soltar transcribe.
                        if pressed {
                            let _ = app.emit("elfie:start-voice", ());
                        } else {
                            let _ = app.emit("elfie:stop-voice", ());
                        }
                        return;
                    }
                    if !pressed {
                        return;
                    }
                    if shortcut == &sc_capture {
                        show_main(app);
                        let _ = app.emit("elfie:open-capture", ());
                    } else if shortcut == &sc_routine {
                        let _ = app.emit("elfie:run-routine", ());
                    }
                })
                .build(),
        );
    }

    // Autostart con Windows (LaunchAgent en macOS). Solo escritorio.
    #[cfg(desktop)]
    {
        builder = builder.plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            None,
        ));
    }

    builder
        .plugin(tauri_plugin_notification::init())
        .invoke_handler(tauri::generate_handler![
            elfie_notify,
            toggle_fullscreen,
            monitor::get_metrics,
            monitor::get_processes,
            system_control::open_app,
            system_control::kill_process,
            system_control::open_folder,
            system_control::power_action,
            system_control::set_volume,
            system_control::get_volume,
            system_control::mute_toggle,
            system_control::screenshot,
            system_control::clipboard_read,
            system_control::clipboard_write,
            system_control::foreground_app,
        ])
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            // Registrar auto-inicio con Windows (idempotente).
            #[cfg(desktop)]
            {
                use tauri_plugin_autostart::ManagerExt;
                let mgr = app.autolaunch();
                if let Ok(false) = mgr.is_enabled() {
                    let _ = mgr.enable();
                }
            }

            // --- Tray icon + menú contextual ---
            let mi_show = MenuItem::with_id(app, "show", "Mostrar / Ocultar Elfie", true, None::<&str>)?;
            let mi_capture =
                MenuItem::with_id(app, "capture", "Captura rápida  ·  Ctrl+Space", true, None::<&str>)?;
            let mi_fullscreen =
                MenuItem::with_id(app, "fullscreen", "Pantalla completa  ·  F11", true, None::<&str>)?;
            let sep = PredefinedMenuItem::separator(app)?;
            let mi_quit = MenuItem::with_id(app, "quit", "Salir", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&mi_show, &mi_capture, &mi_fullscreen, &sep, &mi_quit])?;

            let _tray = TrayIconBuilder::with_id("elfie-tray")
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("Elfie · PRTS")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => toggle_main(app),
                    "capture" => {
                        show_main(app);
                        let _ = app.emit("elfie:open-capture", ());
                    }
                    "fullscreen" => {
                        fullscreen_toggle(app);
                    }
                    "quit" => app.exit(0),
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    // Clic izquierdo en el icono → mostrar/ocultar
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        toggle_main(tray.app_handle());
                    }
                })
                .build(app)?;

            // Monitor de recursos: emite "elfie:metrics" cada 3 s.
            monitor::start(app.handle().clone());

            // Sidecar de voz (faster-whisper + Kokoro): lanzar y gestionar su ciclo de vida.
            app.manage(voice::Sidecar(std::sync::Mutex::new(voice::spawn())));

            Ok(())
        })
        // Cerrar la ventana la oculta al tray en vez de salir (asistente siempre activo).
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                if window.label() == "main" {
                    api.prevent_close();
                    let _ = window.hide();
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            // Al salir de verdad, matar el sidecar de voz.
            if let tauri::RunEvent::Exit = event {
                if let Some(state) = app_handle.try_state::<voice::Sidecar>() {
                    voice::kill(&state);
                }
            }
        });
}

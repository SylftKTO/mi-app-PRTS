#!/usr/bin/env python3
# voice_server.py — Sidecar de voz de Elfie (Fase 3).
# STT con faster-whisper (local) + TTS con Kokoro (GPU, local).
# Servidor HTTP mínimo en localhost; el WebView de Tauri le habla por fetch.
#
# Diseño:
#  - El micrófono lo captura sounddevice (OS directo, sin permiso del WebView).
#  - Push-to-talk: /stt/start abre el stream, /stt/stop transcribe y devuelve texto.
#  - Whisper carga al arrancar; Kokoro carga perezoso (STT sirve aunque falte TTS).
#  - Degradación total: si algo falla, responde JSON con error y el cliente cae a manual.
import json
import os
import queue
import re
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
import sounddevice as sd

import rag  # RAG local de Apuntes (Fase 6): embeddings + LanceDB
import chat  # Chat conversacional con memoria (Fase 7.1)
import orchestrator  # Árbitro de GPU/VRAM (Fase 8.2)

HOST = "127.0.0.1"
PORT = int(os.environ.get("ELFIE_VOICE_PORT", "7331"))
SAMPLE_RATE = 16000
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# Coordinación de un solo micrófono entre push-to-talk, wake word y TTS.
_ptt_active = threading.Event()    # push-to-talk tiene el micrófono
_tts_active = threading.Event()    # Elfie está hablando (no escuchar → evita feedback)
_wake_enabled = threading.Event()  # wake word encendida (opt-in, apagada por defecto)
_wake_queue = queue.Queue()        # comandos transcritos tras detectar "Elfie"

# ---------------------------------------------------------------- STT (Whisper)
_whisper = None
_whisper_err = None


def add_cuda_dll_dirs():
    """CTranslate2 (faster-whisper) busca cublas64_12.dll / cudnn de CUDA 12.
    Con CUDA 13 en el sistema no están; si se instalaron los paquetes pip
    nvidia-cublas-cu12 / nvidia-cudnn-cu12, sus DLLs viven en site-packages.
    Las exponemos vía os.add_dll_directory para habilitar GPU."""
    try:
        import importlib.util

        spec = importlib.util.find_spec("nvidia")
        if not spec or not spec.submodule_search_locations:
            return
        nvidia_root = list(spec.submodule_search_locations)[0]
        for sub in sorted(os.listdir(nvidia_root)):
            bin_dir = os.path.join(nvidia_root, sub, "bin")
            if os.path.isdir(bin_dir):
                os.add_dll_directory(bin_dir)
                # CTranslate2 carga cublas con LoadLibrary plano (ignora add_dll_directory);
                # anteponer al PATH sí lo cubre.
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
                print(f"[voz] CUDA DLLs: {sub}/bin", flush=True)
    except Exception as e:
        print(f"[voz] add_cuda_dll_dirs: {e}", flush=True)


def load_whisper():
    global _whisper, _whisper_err
    if _whisper is not None or _whisper_err is not None:
        return
    try:
        add_cuda_dll_dirs()  # DLLs de CUDA 12 desde paquetes pip nvidia-* si existen
        from faster_whisper import WhisperModel

        # Modelo: env ELFIE_WHISPER_MODEL (nombre o ruta). Si no, usa la carpeta local
        # ./models/whisper-large-v3-turbo si tiene model.bin; si tampoco, descarga por nombre.
        local_dir = os.path.join(MODELS_DIR, "whisper-large-v3-turbo")
        env_model = os.environ.get("ELFIE_WHISPER_MODEL")
        if env_model:
            model_ref = env_model
        elif os.path.exists(os.path.join(local_dir, "model.bin")):
            model_ref = local_dir
        else:
            model_ref = "large-v3-turbo"  # descarga automática (HF)
        print(f"[voz] modelo Whisper: {model_ref}", flush=True)

        # Intenta GPU (float16) y la VALIDA con un warm-up; si el encode falla
        # (p. ej. falta cublas64_12.dll porque hay CUDA 13), cae a CPU int8.
        warm = np.zeros(SAMPLE_RATE, dtype=np.float32)
        try:
            m = WhisperModel(model_ref, device="cuda", compute_type="float16")
            list(m.transcribe(warm, language="es")[0])  # fuerza la carga real de CUDA
            _whisper = m
            print("[voz] Whisper en GPU (float16)", flush=True)
        except Exception as e:
            print(f"[voz] GPU no usable para Whisper ({e}); CPU int8", flush=True)
            _whisper = WhisperModel(model_ref, device="cpu", compute_type="int8")
            list(_whisper.transcribe(warm, language="es")[0])
            print("[voz] Whisper en CPU (int8)", flush=True)
    except Exception as e:
        _whisper_err = str(e)
        print(f"[voz] ERROR cargando Whisper: {e}", flush=True)


# Estado de grabación push-to-talk
_rec_lock = threading.Lock()
_rec_stream = None
_rec_frames = []


def transcribe_audio(audio):
    """Transcribe un array float32 mono 16k con Whisper (es). Devuelve texto."""
    if audio is None or audio.size < SAMPLE_RATE // 4:  # < 0.25 s
        return ""
    load_whisper()
    if _whisper is None:
        return ""
    segments, _info = _whisper.transcribe(
        audio.astype(np.float32),
        language="es",
        beam_size=1,
        vad_filter=True,
        condition_on_previous_text=False,  # sin arrastre de contexto → menos alucinación, más rápido
    )
    return "".join(s.text for s in segments).strip()


def rec_start():
    global _rec_stream, _rec_frames
    _ptt_active.set()  # quita el mic a la wake word mientras grabamos
    time.sleep(0.15)   # deja que la escucha continua libere el dispositivo
    with _rec_lock:
        if _rec_stream is not None:
            return
        _rec_frames = []

        def cb(indata, frames, time_info, status):
            _rec_frames.append(indata.copy())

        _rec_stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=cb
        )
        _rec_stream.start()


def rec_stop_and_transcribe():
    global _rec_stream, _rec_frames
    with _rec_lock:
        if _rec_stream is None:
            _ptt_active.clear()
            return {"text": "", "error": "no estaba grabando"}
        _rec_stream.stop()
        _rec_stream.close()
        _rec_stream = None
        frames = _rec_frames
        _rec_frames = []
    _ptt_active.clear()  # devuelve el mic a la wake word

    if not frames:
        return {"text": ""}
    audio = np.concatenate(frames, axis=0).flatten()
    return {"text": transcribe_audio(audio)}


# ---------------------------------------------------------------- TTS (Kokoro)
_kokoro = None
_kokoro_err = None
KOKORO_VOICE = os.environ.get("ELFIE_KOKORO_VOICE", "ef_dora")  # voz española
KOKORO_FILES = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}


def ensure_kokoro_files():
    paths = {}
    for name, url in KOKORO_FILES.items():
        dest = os.path.join(MODELS_DIR, name)
        if not os.path.exists(dest):
            print(f"[voz] descargando {name} …", flush=True)
            urllib.request.urlretrieve(url, dest)
        paths[name] = dest
    return paths


def load_kokoro():
    global _kokoro, _kokoro_err
    if _kokoro is not None or _kokoro_err is not None:
        return
    try:
        from kokoro_onnx import Kokoro

        files = ensure_kokoro_files()
        _kokoro = Kokoro(files["kokoro-v1.0.onnx"], files["voices-v1.0.bin"])
        print("[voz] Kokoro cargado", flush=True)
    except Exception as e:
        _kokoro_err = str(e)
        print(f"[voz] ERROR cargando Kokoro: {e}", flush=True)


def speak(text, voice=None, speed=1.0):
    load_kokoro()
    if _kokoro is None:
        return {"ok": False, "error": _kokoro_err or "kokoro no cargó"}
    try:
        speed = float(speed)
    except (TypeError, ValueError):
        speed = 1.0
    speed = min(max(speed, 0.5), 2.0)
    samples, sr = _kokoro.create(text, voice=voice or KOKORO_VOICE, speed=speed, lang="es")
    _play(samples, sr)
    return {"ok": True}


def _play(samples, sr):
    """Reproduce audio pausando la escucha continua (anti-feedback) en un solo sitio."""
    _tts_active.set()
    try:
        sd.play(samples, sr)
        sd.wait()
    finally:
        _tts_active.clear()


# ---------------------------------------------------------------- TTS (XTTS v2, voz clonada)
# XTTS corre en un venv AISLADO (venv-xtts) como microservicio (xtts_server.py) para no
# romper el numpy 2 que usan Whisper/Kokoro. Se lanza perezosamente al primer uso.
XTTS_PORT = int(os.environ.get("ELFIE_XTTS_PORT", "7332"))
XTTS_URL = f"http://127.0.0.1:{XTTS_PORT}"
_xtts_proc = None
_xtts_lock = threading.Lock()


def _xtts_python():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # elfie-desktop/
    return os.path.join(base, "venv-xtts", "Scripts", "python.exe")


def ensure_xtts():
    """Arranca el microservicio XTTS la primera vez (si el venv aislado existe)."""
    global _xtts_proc
    import requests

    try:
        requests.get(XTTS_URL + "/health", timeout=1)
        return True
    except Exception:
        pass
    with _xtts_lock:
        if _xtts_proc and _xtts_proc.poll() is None:
            pass
        else:
            py = _xtts_python()
            if not os.path.exists(py):
                return False
            import subprocess

            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xtts_server.py")
            _xtts_proc = subprocess.Popen([py, script], cwd=os.path.dirname(script))
            print(f"[voz] XTTS microservicio lanzado (pid {_xtts_proc.pid})", flush=True)
            # Registra a XTTS como dueño pesado de la GPU (no descarga Ollama: coexisten).
            try:
                orchestrator.claim("xtts")
            except Exception:
                pass
    for _ in range(60):  # espera a que el HTTP levante (no a que cargue el modelo)
        try:
            requests.get(XTTS_URL + "/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def speak_xtts(text, speaker_wav, speed=1.0):
    import requests

    if not ensure_xtts():
        return {"ok": False, "error": "XTTS no disponible (¿falta venv-xtts?)"}
    r = requests.post(
        XTTS_URL + "/synth",
        json={"text": text, "speaker_wav": speaker_wav, "language": "es", "speed": speed},
        timeout=180,
    )
    j = r.json()
    if not j.get("ok"):
        return j
    import soundfile as sf

    samples, sr = sf.read(j["wav"], dtype="float32")
    _play(samples, sr)
    return {"ok": True, "engine": "xtts"}


# ---------------------------------------------------------------- TTS (Piper, voz ligera)
# Piper corre en CPU (onnxruntime), arranque casi instantáneo, ~0 GPU. Ideal para
# confirmaciones cortas de la mascota (Fase 9.1). Carga perezosa; si falta el modelo
# o el paquete, degrada a Kokoro vía speak_dispatch (degradación total).
_piper = None
_piper_err = None
PIPER_MODEL = os.environ.get("ELFIE_PIPER_MODEL", "")  # ruta al .onnx (voz es_MX)


def load_piper():
    global _piper, _piper_err
    if _piper is not None or _piper_err is not None:
        return _piper
    try:
        from piper import PiperVoice
    except Exception:
        try:
            from piper.voice import PiperVoice  # variantes de versión del paquete
        except Exception as e:
            _piper_err = f"piper no instalado ({e})"
            print(f"[voz] {_piper_err}", flush=True)
            return None
    model = PIPER_MODEL
    if not model:
        base = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "piper"
        )
        if os.path.isdir(base):
            for f in sorted(os.listdir(base)):
                if f.endswith(".onnx"):
                    model = os.path.join(base, f)
                    break
    if not model or not os.path.exists(model):
        _piper_err = "falta modelo Piper (.onnx): define ELFIE_PIPER_MODEL o pon uno en models/piper/"
        print(f"[voz] {_piper_err}", flush=True)
        return None
    try:
        cfg = model + ".json"
        _piper = PiperVoice.load(model, config_path=cfg) if os.path.exists(cfg) else PiperVoice.load(model)
        print("[voz] Piper cargado", flush=True)
    except Exception as e:
        _piper_err = str(e)
        print(f"[voz] ERROR cargando Piper: {e}", flush=True)
    return _piper


def speak_piper(text, speed=1.0):
    v = load_piper()
    if v is None:
        return {"ok": False, "error": _piper_err or "piper no disponible"}
    import wave
    import tempfile
    import soundfile as sf

    try:
        sp = min(max(float(speed or 1.0), 0.5), 2.0)
    except (TypeError, ValueError):
        sp = 1.0
    length_scale = 1.0 / sp  # más rápido = length_scale menor
    tmp = os.path.join(tempfile.gettempdir(), "elfie_piper.wav")
    try:
        with wave.open(tmp, "wb") as wf:
            try:
                v.synthesize(text, wf, length_scale=length_scale)
            except TypeError:
                v.synthesize(text, wf)  # versiones sin length_scale
        samples, sr = sf.read(tmp, dtype="float32")
        _play(samples, sr)
        return {"ok": True, "engine": "piper"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def speak_dispatch(text, voice, speed, engine, speaker_wav):
    """Elige motor: xtts (voz clonada) o piper (ligera); fallback a Kokoro si falla."""
    if engine == "xtts" and speaker_wav:
        r = speak_xtts(text, speaker_wav, speed)
        if r.get("ok"):
            return r
        print(f"[voz] XTTS falló, caigo a Kokoro: {r.get('error')}", flush=True)
    elif engine == "piper":
        r = speak_piper(text, speed)
        if r.get("ok"):
            return r
        print(f"[voz] Piper falló, caigo a Kokoro: {r.get('error')}", flush=True)
    return speak(text, voice, speed)


def record_reference(seconds=8, name="elfie_voice"):
    """Graba ~N s del micrófono como audio de referencia para clonar voz (XTTS)."""
    try:
        seconds = min(max(int(seconds or 8), 3), 20)
    except (TypeError, ValueError):
        seconds = 8
    voices_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "voices")
    os.makedirs(voices_dir, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", name or "elfie_voice")[:40] or "elfie_voice"
    path = os.path.join(voices_dir, safe + ".wav")
    _ptt_active.set()  # toma el micrófono (pausa la wake word)
    try:
        audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
    finally:
        _ptt_active.clear()
    import soundfile as sf

    sf.write(path, audio, SAMPLE_RATE)
    return {"ok": True, "path": path, "seconds": seconds}


# ---------------------------------------------------------------- Wake word (Vosk)
# Detector "suave" on-device. Palabra: "Elfie" (pronunciada 'elfi'). Sin enviar audio
# a nadie. Opt-in (apagada por defecto). Reemplazable por openWakeWord en el futuro.
_vosk_model = None
_vosk_err = None
# El modelo español de Vosk transcribe "Elfie" como "el fin" / "el fi" / "el fichaje".
# "Dalia" es la segunda palabra clave (alias de la wake word web). Vosk en es la oye
# limpia ("dalia"/"dalía") o como "talía"/"valía"/"daría" → cubrimos los mis-hears.
WAKE_RE = re.compile(r"(\bel\s?fi|\b[dtv]al[ií]a\b|\bdar[ií]a\b)", re.IGNORECASE)
WAKE_DEBUG = os.environ.get("ELFIE_WAKE_DEBUG", "0") == "1"  # loguea lo que oye Vosk


def load_vosk():
    global _vosk_model, _vosk_err
    if _vosk_model is not None or _vosk_err is not None:
        return
    try:
        from vosk import Model, SetLogLevel

        SetLogLevel(-1)
        _vosk_model = Model(os.path.join(MODELS_DIR, "vosk-es"))
        print("[voz] Vosk cargado (wake word 'Elfie')", flush=True)
    except Exception as e:
        _vosk_err = str(e)
        print(f"[voz] ERROR Vosk: {e}", flush=True)


def _rms(frame):
    return float(np.sqrt(np.mean(np.square(frame)))) if frame.size else 0.0


# Limpia restos de la wake word al inicio del comando transcrito por Whisper.
_WAKE_STRIP = re.compile(
    r"^\W*(el\s*fin|elfie?|elfi|fin|dal[ií]a|tal[ií]a|val[ií]a|dar[ií]a)\b[\s,.:;]*",
    re.IGNORECASE,
)

# ---------------------------------------------------------------- Wake word REAL on-device (Porcupine)
# Detector dedicado (no STT general): mucho más preciso y ligero que Vosk, 100% on-device.
# Palabra personalizada «Dalia» = archivo .ppn generado gratis en console.picovoice.ai.
# Si falta la AccessKey o el .ppn, se cae automáticamente al detector Vosk (degradación total).
PICOVOICE_KEY = os.environ.get("ELFIE_PICOVOICE_KEY", "")
PORCUPINE_PPN = os.environ.get(
    "ELFIE_PORCUPINE_PPN", os.path.join(MODELS_DIR, "porcupine", "dalia.ppn")
)
PORCUPINE_SENS = float(os.environ.get("ELFIE_PORCUPINE_SENS", "0.6"))  # 0..1 (más alto = más sensible)
_porcupine = None
_porcupine_tried = False


def load_porcupine():
    """Crea el detector Porcupine si hay AccessKey + .ppn de 'Dalia'. Si no, None (→ Vosk)."""
    global _porcupine, _porcupine_tried
    if _porcupine_tried:
        return _porcupine
    _porcupine_tried = True
    key = PICOVOICE_KEY
    if not key:  # alternativa amigable: archivo local junto al .ppn (gitignored)
        keyfile = os.path.join(MODELS_DIR, "porcupine", "accesskey.txt")
        if os.path.exists(keyfile):
            try:
                key = open(keyfile, encoding="utf-8").read().strip()
            except Exception:
                key = ""
    if not key or not os.path.exists(PORCUPINE_PPN):
        return None
    try:
        import pvporcupine

        kwargs = {
            "access_key": key,
            "keyword_paths": [PORCUPINE_PPN],
            "sensitivities": [PORCUPINE_SENS],
        }
        model = os.environ.get("ELFIE_PORCUPINE_MODEL")  # .pv en español (opcional)
        if model and os.path.exists(model):
            kwargs["model_path"] = model
        _porcupine = pvporcupine.create(**kwargs)
        print("[voz] Porcupine cargado (wake word on-device 'Dalia')", flush=True)
    except Exception as e:
        print(f"[voz] Porcupine no disponible ({e}); uso Vosk", flush=True)
        _porcupine = None
    return _porcupine


def _capture_after_wake():
    """Tras detectar la wake word, graba el comando (float32) hasta ~1 s de silencio
    y lo transcribe con Whisper. Stream propio (un pequeño hueco tras la palabra es ok)."""
    BLOCK = 4000
    BLOCK_S = BLOCK / SAMPLE_RATE
    THRESH, SILENCE_END, MAX_CMD = 0.015, 1.0, 6.0
    frames, spoke, silence = [], False, 0.0
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=BLOCK) as st:
        while not _ptt_active.is_set() and not _tts_active.is_set():
            data, _ = st.read(BLOCK)
            f = data.flatten().copy()
            frames.append(f)
            if _rms(f) > THRESH:
                spoke, silence = True, 0.0
            elif spoke:
                silence += BLOCK_S
            if (spoke and silence >= SILENCE_END) or (len(frames) * BLOCK_S >= MAX_CMD):
                break
    return transcribe_audio(np.concatenate(frames)) if spoke else ""


def wake_loop_porcupine(pp):
    """Escucha continua con Porcupine: detecta 'Dalia' → captura el comando → Whisper → cola."""
    fl, sr = pp.frame_length, pp.sample_rate
    while True:
        if not _wake_enabled.is_set() or _ptt_active.is_set() or _tts_active.is_set():
            time.sleep(0.15)
            continue
        try:
            with sd.InputStream(samplerate=sr, channels=1, dtype="int16", blocksize=fl) as st:
                while (
                    _wake_enabled.is_set()
                    and not _ptt_active.is_set()
                    and not _tts_active.is_set()
                ):
                    data, _ = st.read(fl)
                    if pp.process(data.flatten()) >= 0:
                        print("[voz] wake (Porcupine) 'Dalia' detectada", flush=True)
                        break
            if not _wake_enabled.is_set():
                continue
            text = _WAKE_STRIP.sub("", _capture_after_wake().strip()).strip()
            if text:
                print(f"[voz] wake comando: {text!r}", flush=True)
                _wake_queue.put(text)
        except Exception as e:
            print(f"[voz] porcupine loop error: {e}", flush=True)
            time.sleep(0.5)


def wake_loop():
    """Dispatcher: usa Porcupine (on-device real) si está configurado; si no, Vosk."""
    pp = load_porcupine()
    if pp is not None:
        wake_loop_porcupine(pp)
    else:
        wake_loop_vosk()


def wake_loop_vosk():
    """Escucha continua con UN solo stream (sin reabrir → sin recortar el comando):
    Vosk detecta 'Elfie' → se acumula el audio siguiente hasta ~1 s de silencio →
    Whisper transcribe → cola. Descarta si no hubo voz real (evita alucinaciones)."""
    load_vosk()
    if _vosk_model is None:
        return
    from vosk import KaldiRecognizer

    BLOCK = 4000           # 0.25 s
    BLOCK_S = BLOCK / SAMPLE_RATE
    THRESH = 0.015         # umbral de voz (RMS)
    SILENCE_END = 1.0      # fin de comando tras 1 s de silencio
    MAX_CMD = 6.0          # tope de comando

    while True:
        if not _wake_enabled.is_set() or _ptt_active.is_set() or _tts_active.is_set():
            time.sleep(0.15)
            continue
        last_dbg = ""
        try:
            rec = KaldiRecognizer(_vosk_model, SAMPLE_RATE)
            state = "listen"
            cmd_frames, spoke, silence, preroll = [], False, 0.0, None
            with sd.InputStream(
                samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=BLOCK
            ) as st:
                while (
                    _wake_enabled.is_set()
                    and not _ptt_active.is_set()
                    and not _tts_active.is_set()
                ):
                    data, _ = st.read(BLOCK)
                    f = data.flatten().copy()

                    if state == "listen":
                        pcm = (np.clip(f, -1, 1) * 32767).astype(np.int16).tobytes()
                        if rec.AcceptWaveform(pcm):
                            txt = json.loads(rec.Result()).get("text", "")
                        else:
                            txt = json.loads(rec.PartialResult()).get("partial", "")
                        if WAKE_DEBUG and txt and txt != last_dbg:
                            last_dbg = txt
                            print(f"[voz] vosk oye: {txt!r}", flush=True)
                        if WAKE_RE.search(txt):
                            print("[voz] wake detectada (Elfie/Dalia)", flush=True)
                            state = "capture"
                            cmd_frames = [preroll] if preroll is not None else []
                            spoke, silence = False, 0.0
                        else:
                            preroll = f  # 0.25 s de pre-roll contra recorte
                    else:  # capture: mismo stream, sin gap
                        cmd_frames.append(f)
                        if _rms(f) > THRESH:
                            spoke, silence = True, 0.0
                        elif spoke:
                            silence += BLOCK_S
                        if (spoke and silence >= SILENCE_END) or (
                            len(cmd_frames) * BLOCK_S >= MAX_CMD
                        ):
                            break

            if state == "capture" and spoke:
                text = transcribe_audio(np.concatenate(cmd_frames))
                text = _WAKE_STRIP.sub("", text).strip()
                if text:
                    print(f"[voz] wake comando: {text!r}", flush=True)
                    _wake_queue.put(text)
        except Exception as e:
            print(f"[voz] wake_loop error: {e}", flush=True)
            time.sleep(0.5)


# ---------------------------------------------------------------- Router LLM (Ollama local)
# Mismo vocabulario cerrado que la Edge Function command.v4. Ollama resuelve local ($0);
# si falla o devuelve unknown, el cliente cae a Anthropic (interpret-command).
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
LLM_MODEL = os.environ.get("ELFIE_LLM_MODEL", "qwen2.5:7b")

LLM_SYSTEM = """Eres Elfie, el asistente por voz de Sylft. Recibes una transcripción y devuelves UNA intención del vocabulario cerrado.

Responde SOLO con un objeto JSON válido, sin markdown ni texto extra:
{"intent":"open|navigate|summary|create_task|log_weight|log_set|weather|ask|unknown","params":{},"speak":"respuesta breve en español","confidence":0.0}

Vocabulario (params por intent):
- open:        {"target":"spotify","deep_link":"spotify:..."}   (solo Spotify)
- navigate:    {"view":"dashboard|tareas|semana|proyectos|gym|dieta|apuntes"}
- summary:     {"scope":"dia|tareas|gym"}
- create_task: {"title":str,"origin":"escuela|wolves|levelup|personal","priority":"alta|media|baja","deadline":"YYYY-MM-DD"|null}
- log_weight:  {"weight_kg":num,"date":"YYYY-MM-DD"}
- log_set:     {"exercise":str,"weight_kg":num,"reps":int}
- weather:     {"location":str|null}
- ask:         {}   (la respuesta va en "speak")
- unknown:     {}

Reglas:
- Español de México. "speak" es una sola frase corta, sin emojis.
- "pon música" / "música para estudiar" → open spotify (deep_link "spotify:preset:estudio|foco|entreno" o "spotify:").
- "¿qué tal el clima?" → weather.
- "press banca 80 por 8" → log_set (exercise sin verbos, weight_kg, reps).
- ask → preguntas cotidianas/conocimiento (cálculos, conversiones, definiciones, datos): pon la RESPUESTA breve en "speak".
- NO uses ask para notas/recordatorios/tareas (eso es create_task o unknown). unknown solo si es ininteligible."""


_NAV_VIEWS = {"dashboard", "tareas", "semana", "proyectos", "gym", "dieta", "apuntes"}
_SCOPES = {"dia", "tareas", "gym"}


def llm_validate(d):
    """Valida la intención del LLM local contra el esquema cerrado. Si no cumple,
    devuelve unknown → el cliente cae a Anthropic. Evita ejecutar params basura."""
    if not isinstance(d, dict):
        return {"intent": "unknown"}
    it = d.get("intent")
    p = d.get("params") or {}
    ok = False
    if it == "open":
        if not p.get("deep_link"):
            p["deep_link"] = "spotify:"
        p.setdefault("target", "spotify")
        ok = True
    elif it == "navigate":
        ok = p.get("view") in _NAV_VIEWS
    elif it == "summary":
        ok = p.get("scope") in _SCOPES
    elif it == "create_task":
        ok = bool(p.get("title"))
    elif it == "log_weight":
        ok = isinstance(p.get("weight_kg"), (int, float))
    elif it == "log_set":
        ok = bool(p.get("exercise")) and isinstance(
            p.get("weight_kg"), (int, float)
        ) and isinstance(p.get("reps"), int)
    elif it == "weather":
        ok = True
    elif it == "ask":
        ok = bool((d.get("speak") or "").strip())
    if not ok:
        return {"intent": "unknown"}
    return {
        "intent": it,
        "params": p,
        "speak": d.get("speak", ""),
        "confidence": d.get("confidence", 0.7),
    }


def set_model(m):
    global LLM_MODEL
    if m:
        LLM_MODEL = m
    return LLM_MODEL


def llm_interpret(text, fecha, tone=""):
    import requests

    user = (
        f"Fecha de hoy (America/Mexico_City): {fecha}\n"
        f'Comando del usuario:\n"""{text}"""\n\nResponde solo el JSON.'
    )
    system = LLM_SYSTEM + (f"\nTono de la respuesta 'speak': {tone}." if tone else "")
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": LLM_MODEL,
            "prompt": system + "\n\n" + user,
            "stream": False,
            "format": "json",
            "keep_alive": "10m",  # mantiene el modelo en VRAM entre comandos (sin recargas)
            "options": {"temperature": 0.2, "num_predict": 200},
        },
        timeout=30,
    )
    r.raise_for_status()
    return llm_validate(json.loads(r.json().get("response", "{}")))


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # Preflight CORS del WebView (POST application/json).
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def log_message(self, *_):
        pass  # silencio

    def do_GET(self):
        if self.path == "/health":
            self._send(
                {
                    "ok": True,
                    "whisper": _whisper is not None,
                    "wake": _wake_enabled.is_set(),
                    "wake_engine": "porcupine" if _porcupine is not None else "vosk",
                    "model": LLM_MODEL,
                    "piper": _piper is not None,
                }
            )
        elif self.path == "/wake/next":
            # Long-poll: espera el próximo comando tras "Elfie" (o timeout).
            try:
                txt = _wake_queue.get(timeout=20)
                self._send({"text": txt})
            except queue.Empty:
                self._send({"timeout": True})
        elif self.path == "/rag/status":
            self._send(rag.status())
        elif self.path == "/chat/status":
            self._send(chat.status())
        elif self.path == "/chat/memories":
            self._send(chat.mem_list())
        elif self.path == "/orchestrator/status":
            self._send(orchestrator.status())
        elif self.path == "/voice/xtts/health":
            import requests
            try:
                self._send(requests.get(XTTS_URL + "/health", timeout=2).json())
            except Exception:
                self._send({"ok": False, "ready": False, "error": "xtts no iniciado"})
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        try:
            if self.path == "/stt/start":
                rec_start()
                self._send({"ok": True})
            elif self.path == "/stt/stop":
                self._send(rec_stop_and_transcribe())
            elif self.path == "/tts":
                b = self._body()
                self._send(speak_dispatch(
                    b.get("text", ""), b.get("voice"), b.get("speed", 1.0),
                    b.get("engine"), b.get("speaker_wav"),
                ))
            elif self.path == "/voice/record":
                b = self._body()
                self._send(record_reference(b.get("seconds", 8), b.get("name", "elfie_voice")))
            elif self.path == "/wake/enable":
                _wake_enabled.set()
                self._send({"ok": True, "wake": True})
            elif self.path == "/wake/disable":
                _wake_enabled.clear()
                self._send({"ok": True, "wake": False})
            elif self.path == "/interpret":
                b = self._body()
                self._send(
                    llm_interpret(b.get("text", ""), b.get("fecha", ""), b.get("tone", ""))
                )
            elif self.path == "/config":
                b = self._body()
                self._send({"ok": True, "model": set_model(b.get("model"))})
            elif self.path == "/rag/index":
                b = self._body()
                self._send(rag.index_note(b.get("note") or b))
            elif self.path == "/rag/index_batch":
                b = self._body()
                self._send(rag.index_batch(b.get("notes") or []))
            elif self.path == "/rag/query":
                b = self._body()
                self._send(rag.query(b.get("q", ""), b.get("k", 3)))
            elif self.path == "/rag/answer":
                b = self._body()
                self._send(rag.answer(b.get("q", ""), b.get("k", 3), b.get("model")))
            elif self.path == "/rag/delete":
                b = self._body()
                self._send(rag.delete(b.get("id")))
            elif self.path == "/chat/send":
                b = self._body()
                self._send(chat.reply(b.get("history") or [], b.get("tone", ""), b.get("model")))
            elif self.path == "/chat/remember":
                b = self._body()
                self._send(chat.remember(b.get("text", ""), b.get("kind", "hecho")))
            elif self.path == "/chat/recall":
                b = self._body()
                self._send(chat.recall(b.get("q", ""), b.get("k", 4)))
            elif self.path == "/chat/forget":
                b = self._body()
                self._send(chat.forget(b.get("id")))
            elif self.path == "/chat/extract":
                b = self._body()
                self._send(chat.auto_extract(b.get("history") or [], b.get("model")))
            elif self.path == "/orchestrator/claim":
                b = self._body()
                self._send(orchestrator.claim(b.get("owner", "?"), b.get("need_mb"), bool(b.get("free_ollama"))))
            elif self.path == "/orchestrator/release":
                b = self._body()
                self._send(orchestrator.release(b.get("owner", "?")))
            elif self.path == "/orchestrator/unload_ollama":
                self._send(orchestrator.unload_ollama())
            else:
                self._send({"error": "not found"}, 404)
        except Exception as e:
            import traceback

            traceback.print_exc()
            self._send({"error": str(e)}, 500)


def main():
    print(f"[voz] sidecar Elfie en http://{HOST}:{PORT}", flush=True)
    # Precarga Whisper en un hilo para que el primer comando no espere la carga.
    threading.Thread(target=load_whisper, daemon=True).start()
    # Hilo de escucha continua (wake word); arranca apagado hasta /wake/enable.
    threading.Thread(target=wake_loop, daemon=True).start()
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()

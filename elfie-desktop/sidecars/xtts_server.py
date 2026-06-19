#!/usr/bin/env python3
# xtts_server.py — Microservicio XTTS v2 (Fase 6) en venv aislado (venv-xtts).
# Coqui XTTS v2 clona una voz a partir de ~6 s de audio de referencia. Corre en su
# PROPIO venv (torch + coqui-tts) para NO tocar el stack Whisper/Kokoro (numpy 2) que
# ya funciona. voice_server.py lo lanza perezosamente, le pide /synth y reproduce el
# WAV resultante (así el anti-feedback de la wake word vive en un solo proceso).
#
# Licencia XTTS v2: Coqui Public Model License (CPML) — uso NO comercial. Aquí es
# uso personal de Sylft; COQUI_TOS_AGREED evita el prompt interactivo.
import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ.setdefault("COQUI_TOS_AGREED", "1")

HOST = "127.0.0.1"
PORT = int(os.environ.get("ELFIE_XTTS_PORT", "7332"))
MODEL = os.environ.get("ELFIE_XTTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
OUT_DIR = os.path.join(tempfile.gettempdir(), "elfie_xtts")
os.makedirs(OUT_DIR, exist_ok=True)

_tts = None
_err = None
_device = "cpu"
_lock = threading.Lock()        # serializa las síntesis (una a la vez)
_load_lock = threading.Lock()   # evita cargar el modelo dos veces (precarga + 1er synth)
_seq = 0


def load():
    global _tts, _err, _device
    if _tts is not None or _err is not None:
        return
    with _load_lock:
        if _tts is not None or _err is not None:
            return
        _load_impl()


def _load_impl():
    global _tts, _err, _device
    try:
        import torch
        import torchaudio
        import soundfile as _sf

        # torchaudio 2.11 solo carga audio vía torchcodec (requiere FFmpeg en el SO).
        # XTTS solo usa torchaudio.load para leer el WAV de referencia → lo redirigimos
        # a soundfile (libsndfile, ya instalado), evitando la dependencia de FFmpeg.
        def _ta_load(path, *a, **k):
            data, sr = _sf.read(str(path), dtype="float32", always_2d=True)
            return torch.from_numpy(data.T.copy()), sr

        torchaudio.load = _ta_load

        from TTS.api import TTS

        _device = "cuda" if torch.cuda.is_available() else "cpu"
        _tts = TTS(MODEL).to(_device)
        print(f"[xtts] modelo cargado en {_device}", flush=True)
    except Exception as e:
        _err = str(e)
        print(f"[xtts] ERROR cargando XTTS: {e}", flush=True)


def synth(text, speaker_wav, language="es", speed=1.0):
    load()
    if _tts is None:
        return {"ok": False, "error": _err or "xtts no cargó"}
    if not text or not text.strip():
        return {"ok": False, "error": "texto vacio"}
    if not speaker_wav or not os.path.exists(speaker_wav):
        return {"ok": False, "error": "falta audio de referencia (speaker_wav)"}
    global _seq
    try:
        sp = min(max(float(speed), 0.5), 2.0)
    except (TypeError, ValueError):
        sp = 1.0
    with _lock:
        _seq = (_seq + 1) % 1000
        out = os.path.join(OUT_DIR, f"xtts_{_seq}.wav")
        _tts.tts_to_file(
            text=text, speaker_wav=speaker_wav, language=language,
            file_path=out, speed=sp,
        )
    return {"ok": True, "wav": out}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send({"ok": True, "ready": _tts is not None, "device": _device, "error": _err})
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0) or 0)
            b = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            if self.path == "/synth":
                self._send(synth(
                    b.get("text", ""), b.get("speaker_wav", ""),
                    b.get("language", "es"), b.get("speed", 1.0),
                ))
            else:
                self._send({"error": "not found"}, 404)
        except Exception as e:
            import traceback

            traceback.print_exc()
            self._send({"error": str(e)}, 500)


def main():
    print(f"[xtts] microservicio en http://{HOST}:{PORT} (XTTS carga al primer uso)", flush=True)
    threading.Thread(target=load, daemon=True).start()
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# orchestrator.py — Árbitro de GPU/VRAM de Elfie (Fase 8.2).
# Los 8 GB de VRAM son compartidos (Whisper + Kokoro + Ollama + XTTS + imágenes no
# caben todos calientes). Este módulo da el MECANISMO de bajo nivel:
#   - semáforo de "dueño pesado" de la GPU (un generador de imágenes a la vez),
#   - descargar Ollama bajo demanda para liberar VRAM (clave para la Fase 7.2),
#   - lectura de VRAM vía nvidia-smi (sin dependencias nuevas).
# La POLÍTICA (cuándo cambiar de modo por carga/juego) vive en el frontend
# (desktop.js), que ya recibe métricas de monitor.rs. Degradación total: si algo
# falla, devuelve {ok:false} y el llamador sigue su camino.
#
# Nota de diseño: qwen (~4.5 GB) + XTTS (~2.4 GB) + Whisper SÍ caben (~6.4/8 GB),
# así que XTTS NO descarga Ollama. Descargar Ollama se reserva para imágenes
# (Illustrious ~7 GB), que no coexisten con el LLM.
import os
import subprocess
import threading
import time

OLLAMA = os.environ.get("ELFIE_OLLAMA", "http://127.0.0.1:11434")
LLM_MODEL = os.environ.get("ELFIE_LLM_MODEL", "qwen2.5:7b")
# VRAM libre mínima (MB) que debe quedar antes de lanzar una tarea pesada.
VRAM_FREE_MIN_MB = int(os.environ.get("ELFIE_VRAM_FREE_MIN", "1500"))

_lock = threading.Lock()
_owner = None              # None | "xtts" | "image" | "llm"
_owner_since = 0.0


def gpu_vram():
    """VRAM (MB) vía nvidia-smi. {used,total,free} o error si no hay NVIDIA."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,memory.free",
             "--format=csv,noheader,nounits"],
            text=True, timeout=4,
        )
        used, total, free = (int(x.strip()) for x in out.strip().splitlines()[0].split(","))
        return {"used_mb": used, "total_mb": total, "free_mb": free}
    except Exception as e:
        return {"used_mb": None, "total_mb": None, "free_mb": None, "error": str(e)}


def unload_ollama(model=None):
    """Descarga el modelo de Ollama de la VRAM. Intenta `ollama stop`, luego keep_alive=0."""
    model = model or LLM_MODEL
    try:
        subprocess.run(["ollama", "stop", model], timeout=10, capture_output=True)
        return {"ok": True, "method": "stop"}
    except Exception:
        pass
    try:
        import requests
        requests.post(OLLAMA + "/api/generate",
                      json={"model": model, "keep_alive": 0, "prompt": ""}, timeout=10)
        return {"ok": True, "method": "keep_alive0"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def free_for(owner, need_mb=None):
    """Asegura VRAM para una tarea pesada: si falta, descarga Ollama. Devuelve si liberó."""
    need = need_mb or VRAM_FREE_MIN_MB
    v = gpu_vram()
    freed = False
    if v.get("free_mb") is not None and v["free_mb"] < need:
        unload_ollama()
        freed = True
        time.sleep(1.0)
    return {"ok": True, "freed_ollama": freed, "vram": gpu_vram()}


def claim(owner, need_mb=None, free_ollama=False):
    """Reclama la GPU para una tarea pesada. free_ollama=True descarga el LLM antes
    (úsalo para imágenes; XTTS no lo necesita porque coexiste con qwen)."""
    global _owner, _owner_since
    res = {"ok": True}
    if free_ollama:
        res["free"] = free_for(owner, need_mb)
    with _lock:
        res["prev"] = _owner
        _owner = owner
        _owner_since = time.time()
    res["owner"] = owner
    return res


def release(owner):
    global _owner
    with _lock:
        if _owner == owner:
            _owner = None
    return {"ok": True, "owner": _owner}


def status():
    return {
        "ok": True,
        "gpu_owner": _owner,
        "owner_secs": round(time.time() - _owner_since, 1) if _owner else 0,
        "vram": gpu_vram(),
        "vram_free_min_mb": VRAM_FREE_MIN_MB,
    }

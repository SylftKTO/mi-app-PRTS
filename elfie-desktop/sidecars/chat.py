#!/usr/bin/env python3
# chat.py — Chat conversacional de Elfie (Fase 7.1).
# Conversación multi-turno con el LLM local (Ollama qwen2.5) + personalidad + memoria.
#
# Dos capas de memoria:
#   - Corto plazo: el historial de turnos lo manda el cliente en cada /chat/send
#     (también lo persiste en Supabase). Aquí solo se usan los últimos N turnos.
#   - Largo plazo: hechos durables ("Sylft entrena pierna los lunes") embebidos con
#     bge-m3 en LanceDB (tabla 'memoria', misma DB que el RAG de apuntes). Antes de
#     responder se recuperan los k recuerdos más relevantes y se inyectan al prompt.
#
# Privacidad total: nada sale de la máquina. Degradación: si Ollama/LanceDB fallan,
# los endpoints responden {ok:false} y el cliente cae a manual (o a la API Anthropic).
import json
import os
import threading
import time

import rag  # reutiliza _embed (bge-m3) y la conexión LanceDB (mismo DB_DIR)

_OLLAMA = os.environ.get("ELFIE_OLLAMA", "http://127.0.0.1:11434")
OLLAMA_CHAT_URL = _OLLAMA + "/api/chat"
CHAT_MODEL = os.environ.get("ELFIE_LLM_MODEL", "qwen2.5:7b")

MEM_TABLE = "memoria"
MAX_TURNS = 10          # turnos de historial que se mandan al modelo
RECALL_K = 4            # recuerdos de largo plazo inyectados por respuesta

_mem_lock = threading.Lock()
_mem_tbl = None
_mem_err = None


# ---------------------------------------------------------------- Memoria (LanceDB)
def _mem_connect():
    """Abre/crea la tabla de memoria en la misma DB del RAG. Degrada con _mem_err."""
    global _mem_tbl, _mem_err
    if _mem_tbl is not None or _mem_err is not None:
        return
    try:
        import lancedb
        os.makedirs(rag.DB_DIR, exist_ok=True)
        db = lancedb.connect(rag.DB_DIR)
        if MEM_TABLE in db.table_names():
            _mem_tbl = db.open_table(MEM_TABLE)
        else:
            _mem_tbl = None  # se crea en el primer remember()
        globals()["_mem_db"] = db
    except Exception as e:
        _mem_err = str(e)


def remember(text, kind="hecho"):
    """Guarda un hecho durable: lo embebe y lo añade al vector store."""
    _mem_connect()
    if _mem_err:
        return {"ok": False, "error": _mem_err}
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "texto vacio"}
    vec = rag._embed(text)
    row = {"id": str(int(time.time() * 1000)), "text": text, "kind": kind or "hecho", "vector": vec}
    global _mem_tbl
    with _mem_lock:
        if _mem_tbl is None:
            _mem_tbl = _mem_db.create_table(MEM_TABLE, data=[row])
        else:
            _mem_tbl.add([row])
    return {"ok": True, "id": row["id"]}


def recall(q, k=RECALL_K):
    """Recupera los k recuerdos más cercanos a la consulta (similitud coseno)."""
    _mem_connect()
    if _mem_err or _mem_tbl is None:
        return {"ok": True, "results": []}
    try:
        vec = rag._embed(q)
        rows = _mem_tbl.search(vec).metric("cosine").limit(int(k or RECALL_K)).to_list()
    except Exception as e:
        return {"ok": False, "error": str(e), "results": []}
    out = []
    for r in rows:
        dist = float(r.get("_distance", 0.0))
        score = round(max(0.0, 1.0 - dist), 3)
        if score >= 0.45:  # filtra ruido: solo recuerdos realmente relevantes
            out.append({"id": r.get("id"), "text": r.get("text"), "score": score})
    return {"ok": True, "results": out}


def forget(mid):
    _mem_connect()
    if _mem_err or _mem_tbl is None:
        return {"ok": True}
    try:
        with _mem_lock:
            _mem_tbl.delete(f"id = '{str(mid)}'")
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True}


def mem_list(limit=100):
    _mem_connect()
    if _mem_err or _mem_tbl is None:
        return {"ok": True, "results": []}
    try:
        rows = _mem_tbl.to_pandas().to_dict("records")
        rows.sort(key=lambda r: r.get("id", ""), reverse=True)
        out = [{"id": r.get("id"), "text": r.get("text"), "kind": r.get("kind", "hecho")}
               for r in rows[: int(limit)]]
        return {"ok": True, "results": out}
    except Exception as e:
        return {"ok": False, "error": str(e), "results": []}


# ---------------------------------------------------------------- Chat (Ollama)
_BASE_SYSTEM = (
    "Eres Elfie (también respondes a 'Dalia'), la asistente personal de Sylft: estudiante "
    "del TecNM Celaya, instructor en Wolves (robótica) y LevelUp (idiomas), y atleta de gym. "
    "Hablas español de México, natural y cercano. Respuestas conversacionales y útiles, no "
    "robóticas. Si no sabes algo, dilo con honestidad. No inventes datos personales de Sylft: "
    "usa solo lo que esté en RECUERDOS o en la conversación."
)


def _build_messages(history, tone):
    """Arma la lista de mensajes para /api/chat: system (+recuerdos) + últimos turnos."""
    system = _BASE_SYSTEM
    if tone:
        system += f"\nTono: {tone}."

    # Recupera memoria de largo plazo relevante al último mensaje del usuario.
    last_user = ""
    for m in reversed(history or []):
        if m.get("role") == "user":
            last_user = m.get("content", "")
            break
    recuerdos = []
    if last_user:
        rc = recall(last_user)
        recuerdos = rc.get("results", []) if rc.get("ok") else []
    if recuerdos:
        bloque = "\n".join(f"- {r['text']}" for r in recuerdos)
        system += f"\n\nRECUERDOS sobre Sylft (úsalos si vienen al caso):\n{bloque}"

    msgs = [{"role": "system", "content": system}]
    for m in (history or [])[-MAX_TURNS:]:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content})
    return msgs, recuerdos


def reply(history, tone="", model=None):
    """Genera la respuesta de Elfie dado el historial de la conversación."""
    import requests

    msgs, recuerdos = _build_messages(history, tone)
    try:
        r = requests.post(
            OLLAMA_CHAT_URL,
            json={
                "model": model or CHAT_MODEL,
                "messages": msgs,
                "stream": False,
                "keep_alive": "10m",
                "options": {"temperature": 0.7, "num_predict": 400},
            },
            timeout=90,
        )
        r.raise_for_status()
        text = (r.json().get("message", {}).get("content") or "").strip()
        if not text:
            raise RuntimeError("respuesta vacía")
    except Exception as e:
        return {"ok": False, "error": str(e), "reply": ""}
    return {"ok": True, "reply": text, "used_memories": recuerdos}


def status():
    _mem_connect()
    cnt = 0
    try:
        if _mem_tbl is not None:
            cnt = _mem_tbl.count_rows()
    except Exception:
        pass
    return {
        "ok": _mem_err is None,
        "ready": True,
        "model": CHAT_MODEL,
        "memories": cnt,
        "error": _mem_err,
    }

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


DEDUP_SCORE = 0.88   # si ya existe un recuerdo casi idéntico, no duplicar


def remember(text, kind="hecho"):
    """Guarda un hecho durable: lo embebe y lo añade al vector store.
    Deduplica: si ya hay un recuerdo casi idéntico (coseno ≥ DEDUP_SCORE) no lo repite."""
    _mem_connect()
    if _mem_err:
        return {"ok": False, "error": _mem_err}
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "texto vacio"}
    vec = rag._embed(text)
    global _mem_tbl
    with _mem_lock:
        if _mem_tbl is None:
            row = {"id": str(int(time.time() * 1000)), "text": text, "kind": kind or "hecho", "vector": vec}
            _mem_tbl = _mem_db.create_table(MEM_TABLE, data=[row])
            return {"ok": True, "id": row["id"]}
        # dedup contra el más cercano existente
        try:
            top = _mem_tbl.search(vec).metric("cosine").limit(1).to_list()
            if top:
                score = 1.0 - float(top[0].get("_distance", 1.0))
                if score >= DEDUP_SCORE:
                    return {"ok": True, "id": top[0].get("id"), "duplicate": True}
        except Exception:
            pass
        row = {"id": str(int(time.time() * 1000)), "text": text, "kind": kind or "hecho", "vector": vec}
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


# Memoria EXPLÍCITA: "recuerda que…", "acuérdate de…", "no olvides que…", etc.
import re as _re

_MEM_CMD_RE = _re.compile(
    r"^\s*(?:elfie|dalia)?[,\s]*"
    r"(?:recu[eé]rda(?:me|te)?|acu[eé]rdate|ten en cuenta|toma nota|ap[uú]nta(?:me)?|guarda|no (?:te )?olvides)"
    r"\s+(?:de\s+|que\s+|lo siguiente:?\s*)*(.+)$",
    _re.IGNORECASE,
)


def detect_explicit_memory(text):
    """Si el mensaje pide recordar algo, devuelve el hecho (sin el verbo); si no, None."""
    m = _MEM_CMD_RE.match((text or "").strip())
    if not m:
        return None
    fact = m.group(1).strip().rstrip(" .!¡¿?")
    return fact if len(fact) >= 3 else None


def _last_user(history):
    for m in reversed(history or []):
        if m.get("role") == "user":
            return m.get("content", "") or ""
    return ""


def reply(history, tone="", model=None):
    """Genera la respuesta de Elfie dado el historial de la conversación.
    Si el último mensaje pide recordar algo explícitamente, lo guarda primero
    (deduplicado) y se lo indica al modelo para que lo confirme con naturalidad."""
    import requests

    stored = None
    fact = detect_explicit_memory(_last_user(history))
    if fact:
        rr = remember(fact)
        if rr.get("ok"):
            stored = fact

    msgs, recuerdos = _build_messages(history, tone)
    if stored:
        msgs[0]["content"] += (
            f"\n\nNota: el usuario te pidió recordar «{stored}» y ya lo guardaste "
            "en tu memoria de largo plazo. Confírmalo de forma breve y natural."
        )
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
    return {"ok": True, "reply": text, "used_memories": recuerdos, "stored_memory": stored}


_EXTRACT_PROMPT = (
    "Del siguiente diálogo, extrae SOLO hechos durables y personales sobre el usuario que "
    "valga la pena recordar a largo plazo (preferencias, datos personales, rutinas, relaciones, "
    "metas, decisiones). Ignora lo trivial, efímero, las preguntas y lo ya obvio. Devuelve un "
    "hecho por línea, en tercera persona y conciso. Si no hay nada que valga la pena, responde "
    "EXACTAMENTE: NONE. Máximo 3.\n\nDIÁLOGO:\n"
)


def auto_extract(history, model=None):
    """Pasada ligera que detecta hechos durables del diálogo y los guarda (deduplicados).
    Pensada para llamarse en segundo plano desde el cliente, sin frenar la respuesta."""
    import requests

    convo = "\n".join(
        f"{'Usuario' if m.get('role') == 'user' else 'Elfie'}: {(m.get('content') or '').strip()}"
        for m in (history or [])[-6:]
        if (m.get("content") or "").strip()
    )
    if not convo.strip():
        return {"ok": True, "stored": []}
    try:
        r = requests.post(
            rag.OLLAMA_GEN_URL,
            json={
                "model": model or CHAT_MODEL,
                "prompt": _EXTRACT_PROMPT + convo + "\n\nHECHOS:",
                "stream": False,
                "keep_alive": "10m",
                "options": {"temperature": 0.1, "num_predict": 160},
            },
            timeout=60,
        )
        r.raise_for_status()
        out = (r.json().get("response") or "").strip()
    except Exception as e:
        return {"ok": False, "error": str(e), "stored": []}
    if not out or out.strip().upper().startswith("NONE"):
        return {"ok": True, "stored": []}
    stored = []
    for line in out.splitlines():
        f = line.strip().lstrip("-*•0123456789. ").strip().rstrip(" .")
        if len(f) < 6 or f.upper() == "NONE":
            continue
        rr = remember(f)
        if rr.get("ok") and not rr.get("duplicate"):
            stored.append(f)
        if len(stored) >= 3:
            break
    return {"ok": True, "stored": stored}


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

#!/usr/bin/env python3
# rag.py — RAG local de Apuntes para Elfie (Fase 6).
# Embeddings con nomic-embed-text (Ollama) + vector store LanceDB en disco.
# Privacidad total: las notas nunca salen de la máquina. Degradación: si LanceDB
# u Ollama fallan, los endpoints responden {ok:false,error} y el cliente cae a manual.
import os
import threading

_OLLAMA = os.environ.get("ELFIE_OLLAMA", "http://127.0.0.1:11434")
OLLAMA_EMBED_URL = _OLLAMA + "/api/embeddings"
OLLAMA_GEN_URL = _OLLAMA + "/api/generate"
# bge-m3 (multilingüe) rankea español mucho mejor que nomic-embed-text. 1024-dim.
EMBED_MODEL = os.environ.get("ELFIE_EMBED_MODEL", "bge-m3")
ANSWER_MODEL = os.environ.get("ELFIE_LLM_MODEL", "qwen2.5:7b")

# elfie-desktop/db/  (un nivel arriba de sidecars/); configurable para pruebas
DB_DIR = os.environ.get(
    "ELFIE_RAG_DB",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db"),
)
TABLE = "apuntes"

_lock = threading.Lock()
_db = None
_tbl = None
_err = None


def _connect():
    """Conexión perezosa a LanceDB. Si falta el paquete, deja _err y degrada."""
    global _db, _tbl, _err
    if _db is not None or _err is not None:
        return
    try:
        import lancedb
        os.makedirs(DB_DIR, exist_ok=True)
        _db = lancedb.connect(DB_DIR)
        if TABLE in _db.table_names():
            _tbl = _db.open_table(TABLE)
    except Exception as e:
        _err = str(e)


def _embed(text, prefix="search_document: "):
    """Embedding vía Ollama. Los prefijos de tarea son de nomic; bge-m3 no los usa."""
    import requests

    if not EMBED_MODEL.startswith("nomic"):
        prefix = ""
    t = (prefix + (text or "").strip())[:8000]
    r = requests.post(OLLAMA_EMBED_URL, json={"model": EMBED_MODEL, "prompt": t}, timeout=30)
    r.raise_for_status()
    j = r.json()
    v = j.get("embedding") or (j.get("embeddings") or [None])[0]
    if not v:
        raise RuntimeError("Ollama no devolvió embedding (¿modelo nomic-embed-text?)")
    return v


def _note_text(n):
    """Texto que se incrusta: campos con significado de la nota."""
    parts = [
        n.get("subject", ""), n.get("topic", ""), n.get("key_concepts", ""),
        n.get("summary", ""), n.get("connections", ""), n.get("doubts", ""),
    ]
    return "\n".join(p for p in parts if p and p.strip())


def _preview(n):
    return (n.get("summary") or n.get("key_concepts") or n.get("topic") or "").strip()[:400]


def index_note(n):
    """Incrusta y hace upsert (delete + add) de una nota."""
    _connect()
    if _err:
        return {"ok": False, "error": _err}
    nid = n.get("id")
    if not nid:
        return {"ok": False, "error": "nota sin id"}
    text = _note_text(n)
    if not text.strip():
        delete(nid)  # nota vaciada → quitar del índice
        return {"ok": True, "skipped": "vacia", "id": str(nid)}
    vec = _embed(text)
    row = {
        "id": str(nid),
        "subject": n.get("subject", "") or "",
        "topic": n.get("topic", "") or "",
        "text": _preview(n),
        "vector": vec,
    }
    global _tbl
    with _lock:
        if _tbl is None:
            _tbl = _db.create_table(TABLE, data=[row])
        else:
            try:
                _tbl.delete(f"id = '{str(nid)}'")
            except Exception:
                pass
            _tbl.add([row])
    return {"ok": True, "id": str(nid)}


def index_batch(notes):
    """Reindexa una lista completa (backfill desde el frontend)."""
    ok = 0
    errs = []
    for n in notes or []:
        try:
            r = index_note(n)
            if r.get("ok"):
                ok += 1
            elif r.get("error"):
                errs.append(r["error"])
        except Exception as e:
            errs.append(str(e))
    return {"ok": True, "indexed": ok, "total": len(notes or []), "errors": errs[:5]}


def delete(nid):
    _connect()
    if _err or _tbl is None:
        return {"ok": True}
    try:
        with _lock:
            _tbl.delete(f"id = '{str(nid)}'")
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True}


def query(q, k=3):
    """Top-k apuntes más cercanos a la consulta."""
    _connect()
    if _err:
        return {"ok": False, "error": _err, "results": []}
    if _tbl is None:
        return {"ok": True, "results": []}
    vec = _embed(q, prefix="search_query: ")
    # Coseno: los embeddings de nomic no están normalizados → L2 rankea por magnitud,
    # no por significado. Con métrica coseno, score = 1 - distancia (similitud).
    rows = _tbl.search(vec).metric("cosine").limit(int(k or 3)).to_list()
    out = []
    for r in rows:
        dist = float(r.get("_distance", 0.0))
        out.append({
            "id": r.get("id"),
            "subject": r.get("subject"),
            "topic": r.get("topic"),
            "text": r.get("text"),
            "score": round(max(0.0, 1.0 - dist), 3),
        })
    return {"ok": True, "results": out}


def answer(q, k=3, model=None):
    """Recupera contexto y deja que el LLM local responda basándose SOLO en los apuntes."""
    res = query(q, k)
    if not res.get("ok"):
        return {"ok": False, "error": res.get("error"), "speak": "", "results": []}
    hits = res["results"]
    if not hits:
        return {"ok": True, "speak": "No encontré nada en tus apuntes sobre eso.", "results": []}
    import requests

    contexto = "\n\n".join(f"[{h['subject']} · {h['topic']}] {h['text']}" for h in hits)
    prompt = (
        "Eres Elfie, asistente de Sylft. Responde la pregunta usando SOLO estos apuntes. "
        "Si no alcanzan, dilo con honestidad. Responde breve y en español (1-3 frases).\n\n"
        f"APUNTES:\n{contexto}\n\nPREGUNTA: {q}\n\nRESPUESTA:"
    )
    try:
        r = requests.post(
            OLLAMA_GEN_URL,
            json={
                "model": model or ANSWER_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "10m",
                "options": {"temperature": 0.2, "num_predict": 220},
            },
            timeout=60,
        )
        r.raise_for_status()
        ans = (r.json().get("response") or "").strip()
        if not ans:
            raise RuntimeError("respuesta vacía")
    except Exception:
        # degradación: si el LLM falla, devuelve los apuntes crudos
        crudo = "; ".join(h["text"] for h in hits if h["text"])[:300]
        ans = "Según tus apuntes: " + crudo
    return {"ok": True, "speak": ans, "results": hits}


def status():
    _connect()
    if _err:
        return {"ok": False, "error": _err, "ready": False, "count": 0}
    cnt = 0
    try:
        if _tbl is not None:
            cnt = _tbl.count_rows()
    except Exception:
        pass
    return {"ok": True, "ready": True, "count": cnt, "db": DB_DIR, "embed_model": EMBED_MODEL}

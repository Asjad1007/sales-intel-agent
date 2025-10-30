import os, json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from src.util.io import db
from src.util.log import info

MODEL = None
INDEX_PATH = "data/vectors/events.faiss"
META_PATH  = "data/vectors/events_meta.json"

def _model():
    global MODEL
    if MODEL is None:
        MODEL = SentenceTransformer("intfloat/e5-small-v2")
    return MODEL

def ensure_index():
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT event_id, company_id, title, raw_text, url FROM events")
    rows = cur.fetchall()
    texts, meta = [], []
    for eid, cid, title, raw, url in rows:
        t = (title or "") + " " + (raw or "")
        if not t.strip(): continue
        texts.append(t[:500])
        meta.append({"event_id": eid, "company_id": cid, "url": url, "title": title})
    if not texts:
        info("No events to index."); return
    embs = _model().encode(texts, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embs.shape[1])
    index.add(np.array(embs).astype("float32"))
    os.makedirs("data/vectors", exist_ok=True)
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH,"w") as f: json.dump(meta, f)
    info(f"Indexed {len(texts)} events.")

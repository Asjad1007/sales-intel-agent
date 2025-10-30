import faiss
import numpy as np
from collections import defaultdict
from sentence_transformers import SentenceTransformer

from src.util.io import db
from src.util.log import info

import json as jsonlib  # avoid shadowing

INDEX_PATH = "data/vectors/events.faiss"
META_PATH  = "data/vectors/events_meta.json"

def gather_context(top_n: int = 10):
    # pick top accounts by today's score
    conn = db(); cur = conn.cursor()
    cur.execute("SELECT company_id, score FROM account_scores_daily ORDER BY score DESC")
    top = [r[0] for r in cur.fetchall()[:top_n]]
    if not top:
        info("No top companies yet."); return

    # load meta/index
    with open(META_PATH, "r", encoding="utf-8") as f:
        meta = jsonlib.load(f)
    index = faiss.read_index(INDEX_PATH)
    model = SentenceTransformer("intfloat/e5-small-v2")

    contexts = defaultdict(list)
    for cid in top:
        # generic intent query; you can personalize later
        q = "recent buying signals: funding, hiring, leadership, compliance, tech changes"
        qv = model.encode([q], normalize_embeddings=True).astype("float32")
        D, I = index.search(qv, 16)
        picks = []
        for i in I[0]:
            if i == -1: 
                continue
            if meta[i].get("company_id") == cid:
                picks.append(meta[i])
            if len(picks) >= 5:
                break
        contexts[cid] = picks

    # save for draft step
    import os
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/contexts.json", "w", encoding="utf-8") as f:
        jsonlib.dump(contexts, f, indent=2)
    info(f"Gathered context for {len(contexts)} companies.")

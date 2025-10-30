import json, re
from datetime import datetime, timezone
from src.util.io import db
from src.util.log import info

COMPLIANCE = re.compile(r"\b(SOC2|HIPAA|GDPR|ISO 27001)\b", re.I)
LEADERSHIP = re.compile(r"\b(VP|Head of|Chief|CISO|CTO|CMO)\b", re.I)
FUNDING = re.compile(r"\b(raises|Series\s+[A-E]|seed funding|funding round)\b", re.I)

def annotate_events():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT event_id, event_type, title, raw_text FROM events")
    rows = cur.fetchall()
    for eid, et, title, raw in rows:
        text = (title or "") + " " + (raw or "")
        feats = {
            "funding_recent": bool(FUNDING.search(text)) if et=="rss" else False,
            "role_vp_hire": bool(LEADERSHIP.search(text)) if et in ("rss","job") else False,
            "compliance_keywords": bool(COMPLIANCE.search(text)),
            "hiring_token": True if et=="job" else False
        }
        cur.execute("UPDATE events SET features_json=? WHERE event_id=?", (json.dumps(feats), eid))
    conn.commit()
    info("Feature extraction complete.")

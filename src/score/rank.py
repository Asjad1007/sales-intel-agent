import json, math, datetime, yaml
from collections import defaultdict
from dateutil import parser as dparser
from src.util.io import db
from src.util.log import info

def _age_days(ts):
    if not ts: return 365
    try:
        dt = dparser.parse(ts)
    except Exception:
        return 365
    return max(0, (datetime.datetime.utcnow() - dt.replace(tzinfo=None)).days)

def daily_scores(rules_path: str):
    with open(rules_path,"r") as f:
        rules = yaml.safe_load(f)
    W = rules["weights"]; HL = rules["decay"]["half_life_days"]
    k = math.log(2) / max(HL,1)

    conn = db(); cur = conn.cursor()
    cur.execute("SELECT company_id, event_time, features_json FROM events")
    scores = defaultdict(float); reasons = defaultdict(list)
    for cid, ts, feats_json in cur.fetchall():
        feats = json.loads(feats_json or "{}")
        age = _age_days(ts)
        decay = math.exp(-k * age)
        for key, val in feats.items():
            if not val: continue
            w = W.get(key, 0)
            if w != 0:
                s = w * decay
                scores[cid] += s
                reasons[cid].append({"feature": key, "age_days": age, "gain": round(s,2)})
    today = datetime.datetime.utcnow().date().isoformat()
    for cid, sc in scores.items():
        cur.execute("""INSERT OR REPLACE INTO account_scores_daily (company_id, date, score, reasons_json)
                       VALUES (?,?,?,?)""", (cid, today, sc, json.dumps(reasons[cid])))
    conn.commit()
    info("Scoring complete.")

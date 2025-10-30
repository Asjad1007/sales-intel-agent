import os, feedparser, httpx
from dateutil import parser as dparser
from src.util.io import read_yaml, db, sha1
from src.util.log import info

def ingest_rss(companies_yaml: str):
    cfg = read_yaml(companies_yaml)
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT domain, company_id FROM companies")
    existing = {r[0]: r[1] for r in cur.fetchall()}
    for c in cfg["companies"]:
        if c["domain"] not in existing:
            cur.execute("INSERT INTO companies(name,domain,icp_tags) VALUES(?,?,?)",
                        (c["name"], c["domain"], ",".join(c.get("icp_tags",[]))))
            conn.commit()
    cur.execute("SELECT domain, company_id FROM companies")
    existing = {r[0]: r[1] for r in cur.fetchall()}

    for comp in cfg["companies"]:
        cid = existing[comp["domain"]]
        for url in comp.get("sources",{}).get("rss",[]):
            feed = feedparser.parse(url)
            for e in feed.entries[:50]:
                title = getattr(e, "title", "") or ""
                link = getattr(e, "link", "") or ""
                summary = getattr(e, "summary", "") or ""
                published = getattr(e, "published", "") or getattr(e, "updated", "")
                try:
                    ts = dparser.parse(published).isoformat()
                except Exception:
                    ts = None
                event_id = sha1(f"{cid}|rss|{link}")
                cur.execute("""INSERT OR IGNORE INTO events
                  (event_id, company_id, source, event_type, event_time, url, title, raw_text, features_json)
                  VALUES(?,?,?,?,?,?,?,?,?)""",
                  (event_id, cid, url, "rss", ts, link, title, summary, "{}"))
    conn.commit()
    info("RSS ingestion complete.")

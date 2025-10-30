import httpx, re
from bs4 import BeautifulSoup
from src.util.io import read_yaml, db, sha1
from src.util.log import info

def _parse_jobs(url: str):
    try:
        r = httpx.get(url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        titles = [a.get_text(strip=True) for a in soup.find_all(["a","div"]) if "job" in a.get("href","") or "job" in a.get("class",[]).__str__().lower()]
        if not titles:
            titles = [t.get_text(strip=True) for t in soup.find_all(["h3","h4","a"])][:50]
        return [(url, t) for t in titles[:50]]
    except Exception:
        return []

def ingest_jobs(companies_yaml: str):
    cfg = read_yaml(companies_yaml)
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT domain, company_id FROM companies")
    dom2id = {r[0]: r[1] for r in cur.fetchall()}
    for comp in cfg["companies"]:
        cid = dom2id[comp["domain"]]
        for url in comp.get("sources",{}).get("jobs",[]):
            for src, title in _parse_jobs(url):
                event_id = sha1(f"{cid}|job|{src}|{title}")
                cur.execute("""INSERT OR IGNORE INTO events
                  (event_id, company_id, source, event_type, event_time, url, title, raw_text, features_json)
                  VALUES(?,?,?,?,?,?,?,?,?)""",
                  (event_id, cid, src, "job", None, src, title, "", "{}"))
    conn.commit()
    info("Jobs ingestion complete.")

import os, json, time
from src.util.io import db
from src.util.log import info

def _dry_send(subj, body, to_email="test@example.com"):
    print("---- DRY RUN EMAIL ----")
    print("TO:", to_email)
    print("SUBJECT:", subj)
    print(body)
    print("-----------------------")

def send_batch(provider: str = "dryrun", only_approved: bool = True):
    conn = db(); cur = conn.cursor()
    q = "SELECT draft_id, subject, body FROM drafts WHERE status=?"
    cur.execute(q, ("approved",) if only_approved else ("queued",))
    rows = cur.fetchall()
    for did, subj, body in rows:
        if provider == "dryrun":
            _dry_send(subj, body)
        else:
            # TODO: implement SendGrid/Gmail here
            _dry_send("[would send] " + subj, body)
        cur.execute("UPDATE drafts SET status='sent' WHERE draft_id=?", (did,))
        conn.commit()
        time.sleep(1)
    info(f"Sent {len(rows)} emails (provider={provider}).")

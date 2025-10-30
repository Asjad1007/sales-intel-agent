from src.util.io import db
def set_status(draft_id: str, status: str = "approved"):
    conn = db(); cur = conn.cursor()
    cur.execute("UPDATE drafts SET status=? WHERE draft_id=?", (status, draft_id))
    conn.commit()
    print(f"Draft {draft_id} → {status}")

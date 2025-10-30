import os, json, sqlite3, yaml, hashlib
from datetime import datetime

DB_PATH = "db/salesintel.db"

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def read_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()

def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def read_json(path):
    with open(path, "r") as f:
        return json.load(f)

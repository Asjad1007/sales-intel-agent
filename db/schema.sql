CREATE TABLE IF NOT EXISTS companies (
  company_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  domain TEXT UNIQUE NOT NULL,
  icp_tags TEXT
);
CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  company_id INTEGER NOT NULL,
  source TEXT,
  event_type TEXT,
  event_time TEXT,
  url TEXT,
  title TEXT,
  raw_text TEXT,
  features_json TEXT,
  FOREIGN KEY(company_id) REFERENCES companies(company_id)
);
CREATE TABLE IF NOT EXISTS account_scores_daily (
  company_id INTEGER,
  date TEXT,
  score REAL,
  reasons_json TEXT,
  PRIMARY KEY (company_id, date)
);
CREATE TABLE IF NOT EXISTS drafts (
  draft_id TEXT PRIMARY KEY,
  company_id INTEGER,
  created_at TEXT,
  persona TEXT,
  variant INTEGER,
  subject TEXT,
  body TEXT,
  evidence_json TEXT,
  status TEXT,
  metrics_json TEXT,
  FOREIGN KEY(company_id) REFERENCES companies(company_id)
);
CREATE INDEX IF NOT EXISTS idx_events_company_time ON events(company_id, event_time);

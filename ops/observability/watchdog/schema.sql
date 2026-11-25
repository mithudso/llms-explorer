CREATE TABLE IF NOT EXISTS checks (
  name TEXT NOT NULL,
  minute INTEGER NOT NULL,
  checked_at INTEGER NOT NULL,
  success INTEGER NOT NULL CHECK(success IN (0,1)),
  status INTEGER NOT NULL,
  duration REAL NOT NULL,
  phase TEXT NOT NULL,
  PRIMARY KEY(name,minute)
);
CREATE INDEX IF NOT EXISTS checks_retention ON checks(checked_at);
CREATE TABLE IF NOT EXISTS alert_state (
  name TEXT PRIMARY KEY,
  firing INTEGER NOT NULL CHECK(firing IN (0,1)),
  changed_at INTEGER NOT NULL,
  notified_at INTEGER NOT NULL
);

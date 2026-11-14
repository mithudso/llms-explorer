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

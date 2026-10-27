-- SQLite schema for the mechanical watch (ops/backoffice/watch). One file, WAL mode.
-- Times are UTC. first_seen has seconds ("2026-10-27T12:34:56Z"); published has minutes
-- ("2026-10-27T12:34Z") exactly as newsroom/watch_feeds.py writes them, or '' when the
-- source gives none. Compare each column only with a value of its own shape.

CREATE TABLE IF NOT EXISTS meta (
  key   TEXT PRIMARY KEY,
  value TEXT
);

-- One row per configured source (synced from sources.yaml and the imported lists at every run).
CREATE TABLE IF NOT EXISTS sources (
  id                   TEXT PRIMARY KEY,           -- slug of the name plus a short hash of the URL
  name                 TEXT NOT NULL,              -- as the news desk reads it ("PlayStation Blog")
  kind                 TEXT NOT NULL,              -- official | outlet | gnews | youtube | x | page
  url                  TEXT NOT NULL,
  interval_min         INTEGER NOT NULL,
  breaking             INTEGER NOT NULL DEFAULT 0, -- 1: new items are handed over at once
  enabled              INTEGER NOT NULL DEFAULT 1,
  origin               TEXT NOT NULL DEFAULT '',   -- watch_feeds | watch_pages | config
  etag                 TEXT,
  last_modified        TEXT,
  last_poll_at         TEXT,
  last_ok_at           TEXT,
  last_error           TEXT,
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  next_due_at          TEXT,
  baselined            INTEGER NOT NULL DEFAULT 0  -- 0 until the first successful poll
);

CREATE TABLE IF NOT EXISTS items (
  id           INTEGER PRIMARY KEY,
  source_id    TEXT NOT NULL REFERENCES sources(id),
  source       TEXT NOT NULL,                      -- display name of the source (or of the Steam/X account)
  kind         TEXT NOT NULL,
  title        TEXT NOT NULL,
  url          TEXT NOT NULL,
  url_key      TEXT NOT NULL,                      -- url without fragment, tracking parameters, trailing slash
  published    TEXT NOT NULL DEFAULT '',
  first_seen   TEXT NOT NULL,
  summary      TEXT NOT NULL DEFAULT '',           -- first 400 characters of the item's own text, tags removed
  media        TEXT NOT NULL DEFAULT '[]',         -- JSON: [{"type": "image"|"video"|"audio", "url": "..."}]
  breaking     INTEGER NOT NULL DEFAULT 0,         -- the source was marked breaking when the item arrived
  baseline     INTEGER NOT NULL DEFAULT 0,         -- first poll of a source: recorded, never handed over
  junk         INTEGER NOT NULL DEFAULT 0,         -- guides, deals, puzzles (outlets) or an ignore match
  breaking_seq INTEGER,                            -- handoff in which it went out as breaking (0: dropped as old)
  digest_seq   INTEGER                             -- handoff of the hourly digest that carried it (0: too old to report)
);
CREATE UNIQUE INDEX IF NOT EXISTS items_source_url   ON items(source_id, url_key);
CREATE UNIQUE INDEX IF NOT EXISTS items_source_title ON items(source_id, title);
CREATE INDEX IF NOT EXISTS items_first_seen ON items(first_seen);
CREATE INDEX IF NOT EXISTS items_pending_digest   ON items(digest_seq)   WHERE digest_seq IS NULL;
CREATE INDEX IF NOT EXISTS items_pending_breaking ON items(breaking_seq) WHERE breaking = 1 AND breaking_seq IS NULL;

-- One row per hand-over attempt. seq only goes up; the news desk keeps the last seq it has read.
CREATE TABLE IF NOT EXISTS handoffs (
  seq        INTEGER PRIMARY KEY AUTOINCREMENT,
  kind       TEXT NOT NULL,                        -- hourly | breaking
  created_at TEXT NOT NULL,
  n_items    INTEGER NOT NULL DEFAULT 0,
  status     TEXT NOT NULL,                        -- pending | pushed | failed | skipped | dry
  detail     TEXT NOT NULL DEFAULT ''
);

-- One row per source per pass that actually asked the network. Pruned after 7 days.
CREATE TABLE IF NOT EXISTS polls (
  id         INTEGER PRIMARY KEY,
  source_id  TEXT NOT NULL,
  at         TEXT NOT NULL,
  status     TEXT NOT NULL,                        -- ok | unchanged | error
  items      INTEGER NOT NULL DEFAULT 0,
  new_items  INTEGER NOT NULL DEFAULT 0,
  ms         INTEGER NOT NULL DEFAULT 0,
  error      TEXT
);
CREATE INDEX IF NOT EXISTS polls_at ON polls(at);

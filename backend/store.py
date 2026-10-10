import json
import os
import sqlite3
import threading
from pathlib import Path

BASE = Path(__file__).parent
DB_FILE = Path(os.environ.get("SHIFTSWAP_DB", BASE / "data" / "shiftswap.db"))
LEGACY_FILE = Path(os.environ.get("SHIFTSWAP_DATA", BASE / "data" / "state.json"))
SEED_FILE = Path(os.environ.get("SHIFTSWAP_SEED", BASE / "seed.json"))
LOCK = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS staff (
  id TEXT PRIMARY KEY, name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('STAFF','MANAGER')),
  certifications TEXT NOT NULL DEFAULT '[]');
CREATE TABLE IF NOT EXISTS shifts (
  id TEXT PRIMARY KEY, start TEXT NOT NULL, "end" TEXT NOT NULL,
  required_certification TEXT, assigned_to TEXT REFERENCES staff(id));
CREATE TABLE IF NOT EXISTS listings (
  id TEXT PRIMARY KEY, shift_id TEXT NOT NULL REFERENCES shifts(id),
  poster_id TEXT NOT NULL REFERENCES staff(id),
  status TEXT NOT NULL CHECK (status IN ('OPEN','CLAIMED','WITHDRAWN','APPROVED')),
  claimed_by TEXT REFERENCES staff(id));
CREATE TABLE IF NOT EXISTS history (
  id TEXT PRIMARY KEY, at TEXT NOT NULL, actor_id TEXT, actor_name TEXT,
  action TEXT NOT NULL, shift_id TEXT, listing_id TEXT,
  outcome TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS counters (name TEXT PRIMARY KEY, value INTEGER NOT NULL);
"""

# table -> column order. Lists keep insertion order via rowid.
COLS = {
    "staff": ["id", "name", "role", "certifications"],
    "shifts": ["id", "start", "end", "required_certification", "assigned_to"],
    "listings": ["id", "shift_id", "poster_id", "status", "claimed_by"],
    "history": ["id", "at", "actor_id", "actor_name", "action", "shift_id", "listing_id", "outcome", "detail"],
}


class Store:
    """SQLite persistence. The app works on an in-memory `state` dict (same shape as before);
    save() writes it back to the database in a single transaction.
    Empty database: import data/state.json if present, otherwise load the seed."""

    def __init__(self):
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)
        self.state = self._load()

    def _load(self):
        if self.db.execute("SELECT COUNT(*) FROM staff").fetchone()[0] == 0:
            if LEGACY_FILE.exists():  # one-time import of earlier JSON state
                state = json.loads(LEGACY_FILE.read_text(encoding="utf-8"))
            else:
                seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
                state = {"staff": seed["staff"], "shifts": seed["shifts"], "listings": [],
                         "history": [], "counters": {"listing": 0, "history": 0}}
            self._write(state)
            return state
        state = {}
        for t in COLS:
            state[t] = [dict(r) for r in self.db.execute(f"SELECT * FROM {t} ORDER BY rowid")]
        for p in state["staff"]:
            p["certifications"] = json.loads(p["certifications"])
        state["counters"] = {r["name"]: r["value"] for r in self.db.execute("SELECT * FROM counters")}
        state["counters"].setdefault("listing", 0)
        state["counters"].setdefault("history", 0)
        return state

    def _write(self, state):
        with self.db:  # one transaction: all-or-nothing
            for t, cols in COLS.items():
                self.db.execute(f"DELETE FROM {t}")
                q = ",".join(f'"{c}"' for c in cols)
                marks = ",".join("?" for _ in cols)
                rows = []
                for r in state[t]:
                    vals = [r.get(c) for c in cols]
                    if t == "staff":
                        vals[3] = json.dumps(r.get("certifications", []))
                    rows.append(vals)
                self.db.executemany(f"INSERT INTO {t} ({q}) VALUES ({marks})", rows)
            self.db.execute("DELETE FROM counters")
            self.db.executemany("INSERT INTO counters VALUES (?,?)", list(state["counters"].items()))

    def save(self):
        self._write(self.state)

    def next_id(self, kind: str, prefix: str) -> str:
        self.state["counters"][kind] += 1
        return f"{prefix}{self.state['counters'][kind]}"
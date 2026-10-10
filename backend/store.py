import json
import os
import tempfile
import threading
from pathlib import Path

BASE = Path(__file__).parent
DATA_FILE = Path(os.environ.get("SHIFTSWAP_DATA", BASE / "data" / "state.json"))
SEED_FILE = Path(os.environ.get("SHIFTSWAP_SEED", BASE / "seed.json"))
LOCK = threading.RLock()


class Store:
    """JSON-file persistence. Seed is loaded only when there is no saved state."""

    def __init__(self):
        self.state = self._load()

    def _load(self):
        if DATA_FILE.exists():
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
        state = {
            "staff": seed["staff"],
            "shifts": seed["shifts"],
            "listings": [],
            "history": [],
            "counters": {"listing": 0, "history": 0},
        }
        self._write(state)
        return state

    @staticmethod
    def _write(state):
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=DATA_FILE.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, DATA_FILE)

    def save(self):
        self._write(self.state)

    def next_id(self, kind: str, prefix: str) -> str:
        self.state["counters"][kind] += 1
        return f"{prefix}{self.state['counters'][kind]}"

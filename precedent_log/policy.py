"""Policy counts are independent of optional analytics and survive respawns."""

import json
import os
from pathlib import Path
import tempfile
from threading import RLock

from .stats import Events
from .store import canonical, locked, store_dir


_memory = {}
_mutex = RLock()


class Policy:
    def __init__(self, board, task_id):
        self.board, self.task_id = board, str(task_id or "")
        self.path = store_dir() / (board + ".policy.json")
        self.lock = self.path.with_suffix(".lock")
        self.key = (str(self.path), self.task_id)

    def _read(self):
        if self.path.is_symlink():
            raise OSError("Policy file must not be a symlink")
        if self.path.exists():
            data = json.loads(self.path.read_text())
            if not isinstance(data, dict) or any(
                    not isinstance(row, dict) or type(row.get("vetoes")) is not int or
                    not 0 <= row["vetoes"] <= 2 or not isinstance(row.get("candidates"), list) or
                    any(not isinstance(rid, str) for rid in row["candidates"]) for row in data.values()):
                raise ValueError("Invalid policy state")
            return data
        # Upgrade r1 counts without making analytics a prerequisite for enforcement.
        data = {}
        try:
            events = Events(self.board)
            with locked(events.lock, exclusive=False):
                rows, _ = events._read()
            for row in rows:
                if row["event"] == "veto" and row.get("task_id"):
                    entry = data.setdefault(row["task_id"], {"vetoes": 0, "candidates": []})
                    entry["vetoes"] = min(2, entry["vetoes"] + 1)
                    entry["candidates"] = sorted(set(entry["candidates"]) | set(row.get("ids", [])))
        except (OSError, ValueError, TypeError):
            pass
        return data

    def _save(self, data):
        fd, name = tempfile.mkstemp(prefix=self.board + ".policy-", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w") as stream:
                stream.write(canonical(data) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path)
        finally:
            Path(name).unlink(missing_ok=True)

    def access(self, candidates=(), veto=False):
        """Return (state, actually_vetoed, diagnostic). Two vetoes at most per task."""
        def update(entry):
            entry = {"vetoes": entry.get("vetoes", 0), "candidates": list(entry.get("candidates", []))}
            allowed = bool(veto and self.task_id and entry["vetoes"] < 2)
            if allowed:
                entry["vetoes"] += 1
                entry["candidates"] = sorted(set(entry["candidates"]) | set(candidates))
            return entry, allowed

        with _mutex:
            try:
                with locked(self.lock):
                    data = self._read()
                    stored, memory = data.get(self.task_id, {}), _memory.get(self.key, {})
                    entry = {"vetoes": max(stored.get("vetoes", 0), memory.get("vetoes", 0)),
                             "candidates": sorted(set(stored.get("candidates", [])) | set(memory.get("candidates", [])))}
                    entry, allowed = update(entry)
                    # Keep a fallback even if the durable save fails.
                    _memory[self.key] = entry
                    if veto:
                        data[self.task_id] = entry
                        self._save(data)
                    return entry, allowed, ""
            except (OSError, ValueError, TypeError):
                # Policy is still enforced in this process if its own storage fails.
                # Unlike analytics failure, this loses the respawn guarantee; disclose it.
                if 'entry' not in locals():
                    entry, allowed = update(_memory.get(self.key, {}))
                    _memory[self.key] = entry
                return entry, allowed, "policy storage unavailable; veto budget is process-local"

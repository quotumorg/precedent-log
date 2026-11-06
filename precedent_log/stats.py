"""Durable gate counts and post-commit block observations, scoped to a board."""

import json
import os

from .store import append_line, locked, resolve_board, store_dir, timestamp


class Events:
    def __init__(self, board=None):
        self.board = resolve_board(board)
        self.path = store_dir() / (self.board + ".events.jsonl")
        self.lock = store_dir() / (self.board + ".events.lock")

    def _read(self):
        events, invalid = [], 0
        if self.path.is_symlink():
            raise OSError("Events file must not be a symlink")
        try:
            with self.path.open("rb") as stream:
                for line in stream:
                    try:
                        row = json.loads(line)
                        if (not line.endswith(b"\n") or not isinstance(row, dict) or type(row.get("v")) is not int or row["v"] != 1
                                or row.get("board") != self.board or not isinstance(row.get("event"), str)
                                or not isinstance(row.get("ids", []), list)
                                or any(not isinstance(rid, str) for rid in row.get("ids", []))
                                or not isinstance(row.get("task_id", ""), str)):
                            raise ValueError("invalid event")
                        events.append(row)
                    except (ValueError, UnicodeError):
                        invalid += 1
        except FileNotFoundError:
            pass
        return events, invalid

    def record(self, event, task_id="", ids=(), **fields):
        with locked(self.lock):
            self._recover_tail()
            rows, invalid = self._read()
            if event == "matched":
                count = sum(row["event"] == "veto" and row.get("task_id") == task_id for row in rows)
                event = "veto" if task_id and count < 2 else "uncited"
            append_line(self.path, {"v": 1, "board": self.board, "event": event,
                                  "task_id": task_id, "ids": list(ids), "created_at": timestamp(), **fields})
            return event

    def _recover_tail(self):
        if self.path.is_symlink():
            raise OSError("Events file must not be a symlink")
        if not self.path.exists():
            return
        raw = self.path.read_bytes()
        if raw and not raw.endswith(b"\n"):
            end = raw.rfind(b"\n") + 1
            torn = self.path.with_name(self.board + ".events.torn")
            fd = os.open(torn, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "ab") as stream:
                stream.write(raw[end:] + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            # Backup is durable before truncation; the caller holds the event lock.
            fd = os.open(self.path, os.O_WRONLY | os.O_NOFOLLOW)
            try:
                os.ftruncate(fd, end)
                os.fsync(fd)
            finally:
                os.close(fd)

    def summary(self):
        if not self.path.exists():
            rows, invalid = [], 0
        else:
            with locked(self.lock, exclusive=False):
                rows, invalid = self._read()
        result = {"board": self.board, "needs_input_blocks": 0, "gated_vetoes": 0,
                  "passes_with_citation": 0, "passes_with_justification": 0,
                  "unmatched_passes": 0, "uncited_passes": 0, "unclassified_blocks": 0,
                  "ruling_hits": {}, "invalid_event_lines": invalid}
        counters = {"veto": "gated_vetoes", "citation": "passes_with_citation",
                    "justification": "passes_with_justification", "unmatched": "unmatched_passes",
                    "uncited": "uncited_passes"}
        for row in rows:
            if row["event"] in counters:
                result[counters[row["event"]]] += 1
            if row["event"] == "blocked":
                if row.get("kind") == "needs_input":
                    result["needs_input_blocks"] += 1
                elif row.get("kind") is None:
                    result["unclassified_blocks"] += 1
            for rid in row.get("ids", []):
                if isinstance(rid, str):
                    result["ruling_hits"][rid] = result["ruling_hits"].get(rid, 0) + 1
        return result


def show_task(ctx, task_id, board=None):
    # Public registry dispatch: plugins.py:676-686; payload: kanban_tools.py:677-695.
    if ctx is None:
        raise ValueError("kanban_show context unavailable")
    args = {"task_id": task_id}
    if board is not None:
        args["board"] = board
    result = ctx.dispatch_tool("kanban_show", args)
    result = json.loads(result) if isinstance(result, str) else result
    if not isinstance(result, dict) or not isinstance(result.get("task"), dict):
        raise ValueError("kanban_show task unavailable")
    return result


def observed_kind(ctx, task_id, board, run_id=None, reason=""):
    shown = show_task(ctx, task_id, board)
    for event in reversed(shown.get("events", [])):
        payload = event.get("payload") or {}
        if (event.get("kind") in {"blocked", "dependency_wait", "block_loop_detected"} and
                isinstance(payload, dict) and payload.get("kind") and
                (run_id is None or event.get("run_id") == run_id) and
                payload.get("reason") == reason):
            return payload["kind"]
    return None


def on_blocked(task_id="", board=None, reason="", ctx=None, run_id=None, **kwargs):
    try:
        board = resolve_board(board)
        try:
            kind = observed_kind(ctx, task_id, board, run_id, reason)
        except Exception:
            kind = None
        Events(board).record("blocked", task_id, kind=kind, reason=str(reason or ""))
    except Exception:
        # Observers must never undo or interfere with the committed transition.
        return None

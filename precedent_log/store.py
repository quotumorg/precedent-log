"""Append-only rulings with process-safe IDs and a verifiable hash chain."""

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import time
import tempfile


ZERO = "0" * 64
ID = re.compile(r"P-([1-9][0-9]*)\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
RESERVED_MARKER = re.compile(r"<!--\s*hermes-plugin-section(?:s:|-chars:)", re.I)


class BoardPinError(ValueError):
    """A custom DB pin cannot be associated with an unambiguous board."""


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def home():
    # Context-local profile overrides precede env: hermes_constants.py:194-201 at 2bd378ed.
    from hermes_constants import get_hermes_home
    return get_hermes_home()


def normalize_board(value):
    # Same slug grammar as hermes_cli/kanban_db.py:377-387 at 2bd378ed.
    slug = str(value or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", slug):
        raise ValueError("Board must be 1-64 alphanumerics, hyphens or underscores, starting with an alphanumeric.")
    return slug


def resolve_board(board=None):
    if board is not None:
        return normalize_board(board)
    # The pointer is shared across profiles, not always under HERMES_HOME.
    # hermes_cli/kanban_db.py:402-465 at 2bd378ed; this read-only internal API is disclosed.
    from hermes_cli.kanban_db import get_current_board
    return normalize_board(get_current_board())


def call_board(board=None):
    # Core resolves explicit/scoped intent versus dispatcher and machine-flow pins.
    # kanban_db.py:510-567 at 2bd378ed. No SQL; no public ctx board resolver exists.
    from hermes_cli.kanban_db import kanban_db_path
    path = kanban_db_path(board=board).expanduser().resolve()
    pin = os.environ.get("HERMES_KANBAN_DB", "").strip()
    if pin and path == Path(pin).expanduser().resolve():
        # The physical board wins over a stale BOARD marker for standard paths.
        from hermes_constants import get_default_hermes_root
        root = Path(os.environ.get("HERMES_KANBAN_HOME", "").strip() or get_default_hermes_root()).expanduser().resolve()
        if path == (root / "kanban.db").resolve():
            return "default"
        if path.name == "kanban.db" and path.parent.parent == root / "kanban/boards":
            return normalize_board(path.parent.name)
        # A custom path has no physical slug. Require marker, explicit/scoped
        # selection and existing current board to agree; never infer from a leaf.
        slug = os.environ.get("HERMES_KANBAN_BOARD", "").strip()
        if not slug:
            raise BoardPinError("Custom DB pin needs HERMES_KANBAN_BOARD; refusing to guess the ruling board")
        try:
            slug = normalize_board(slug)
        except ValueError as exc:
            raise BoardPinError("Custom DB pin has an invalid HERMES_KANBAN_BOARD; refusing to guess") from exc
        if resolve_board() != slug or (board is not None and normalize_board(board) != slug):
            raise BoardPinError("Custom DB pin board mismatch: HERMES_KANBAN_BOARD must agree with explicit/current board")
        return slug
    return resolve_board(board)


def store_dir():
    return home() / "precedent-log"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(obj):
    return hashlib.sha256(canonical({k: v for k, v in obj.items() if k != "h"}).encode()).hexdigest()


@contextmanager
def locked(path, exclusive=True, timeout=0.25):
    """Bound lock waits so an abandoned writer cannot time out a policy hook."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise OSError("Store directory must not be a symlink")
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        deadline = time.monotonic() + timeout
        mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        while True:
            try:
                fcntl.flock(fd, mode | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise OSError("Store lock is busy") from None
                time.sleep(0.002)
        yield
    finally:
        os.close(fd)


def append_line(path, obj):
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as stream:
        stream.write(canonical(obj) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


@dataclass
class Snapshot:
    entries: dict = field(default_factory=dict)
    issues: list = field(default_factory=list)
    max_id: int = 0
    tail: str = ZERO
    lines: int = 0
    error: str = ""
    retired_ids: set = field(default_factory=set)

    @property
    def active(self):
        if self.error or self.issues:
            return []
        return [row for row in self.entries.values() if not row.get("retired")]

    @property
    def warning(self):
        if self.issues:
            return (f"log damaged at line {self.issues[0]['line']}, rulings not applied; "
                    "run hermes precedent verify")
        return "log is unreadable; precedent check unavailable" if self.error else ""


def schema_error(row, board):
    if type(row.get("v")) is not int or row["v"] != 1:
        return "unsupported v (expected 1)"
    if row.get("op") not in ("add", "retire", "repair"):
        return "unknown op"
    if not isinstance(row.get("id"), str) or not ID.fullmatch(row["id"]):
        return "invalid id"
    if row.get("board") != board:
        return "wrong board"
    for key in ("author", "created_at"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            return "invalid " + key
    if row.get("surface") not in ("cli", "slash"):
        return "invalid surface"
    if row["op"] == "add":
        for key in ("question", "ruling"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                return "invalid " + key
        if not isinstance(row.get("keys"), list) or any(not isinstance(k, str) or not k.strip() for k in row["keys"]):
            return "invalid keys"
        from .match import key_token
        if any(key_token(k) is None for k in row["keys"]):
            return "each key must be one whole normalized content token"
        if not isinstance(row.get("also", []), list) or any(
                not isinstance(p, str) or not p.strip() for p in row.get("also", [])):
            return "invalid aliases"
        if row.get("source_task") is not None and not isinstance(row["source_task"], str):
            return "invalid source_task"
    elif not isinstance(row.get("reason"), str) or not row["reason"].strip():
        return "invalid retirement reason"
    if row['op'] == 'retire' and row.get('replaced_by') is not None and (
            not isinstance(row['replaced_by'], str) or not ID.fullmatch(row['replaced_by'])):
        return 'invalid replaced_by'
    if row["op"] == "repair" and (not isinstance(row.get("retired_ids"), list) or any(
            not isinstance(rid, str) or not ID.fullmatch(rid) for rid in row["retired_ids"])):
        return "invalid preserved retirements"
    return ""


class Store:
    def __init__(self, board=None):
        self.board = resolve_board(board)
        self.directory = store_dir()
        self.path = self.directory / (self.board + ".jsonl")
        self.lock = self.directory / (self.board + ".lock")

    def _read(self, data=None):
        state = Snapshot()
        try:
            if self.directory.is_symlink() or self.path.is_symlink():
                raise OSError("Store must not be a symlink")
            from io import BytesIO
            with (self.path.open("rb") if data is None else BytesIO(data)) as stream:
                previous = ZERO
                for number, raw in enumerate(stream, 1):
                    state.lines = number
                    errors = []
                    try:
                        row = json.loads(raw)
                        if not isinstance(row, dict):
                            raise ValueError("expected an object")
                    except (ValueError, UnicodeError):
                        state.issues.append({"line": number, "reason": "malformed JSON object"})
                        previous = hashlib.sha256(raw).hexdigest()
                        state.tail = previous
                        continue
                    found = ID.fullmatch(str(row.get("id", "")))
                    if found:
                        state.max_id = max(state.max_id, int(found[1]))
                        # Even a damaged retirement must never restore an earlier add.
                        if row.get("op") == "retire":
                            state.retired_ids.add(row["id"])
                    if row.get("op") == "repair" and isinstance(row.get("retired_ids"), list):
                        state.retired_ids.update(rid for rid in row["retired_ids"]
                                                 if isinstance(rid, str) and ID.fullmatch(rid))
                    problem = schema_error(row, self.board)
                    if problem:
                        errors.append(problem)
                    if not raw.endswith(b"\n"):
                        errors.append("unterminated line")
                    if row.get("prev") != previous:
                        errors.append("prev mismatch (edited or deleted predecessor)")
                    current_hash = row.get("h")
                    if not isinstance(current_hash, str) or not HASH.fullmatch(current_hash) or current_hash != digest(row):
                        errors.append("hash mismatch")
                    # prev hashes the complete prior physical line, including its newline and h.
                    # Continue diagnosis after damage, but active is quarantined board-wide.
                    previous = hashlib.sha256(raw).hexdigest()
                    state.tail = previous
                    if not errors:
                        rid = row["id"]
                        if row["op"] == "add":
                            if rid in state.entries:
                                errors.append("duplicate add id")
                            else:
                                state.entries[rid] = {**row, "retired": False}
                        elif row["op"] == "repair":
                            for retired in row["retired_ids"]:
                                if retired in state.entries:
                                    state.entries[retired] = {**state.entries[retired], "retired": True, "retirement": row}
                        elif rid not in state.entries:
                            errors.append("retire references an unavailable id")
                        else:
                            state.entries[rid] = {**state.entries[rid], "retired": True, "retirement": row}
                    state.issues.extend({"line": number, "reason": error} for error in errors)
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as exc:
            state.error = str(exc)
            state.entries.clear()
        return state

    def read(self):
        try:
            if not self.path.exists() and not self.path.is_symlink():
                return Snapshot()
            with locked(self.lock, exclusive=False):
                return self._read()
        except OSError as exc:
            return Snapshot(error=str(exc))

    def _write(self, op, author, surface, **fields):
        from .guard import require_human
        require_human()
        with locked(self.lock, timeout=5):
            state = self._read()
            if state.error or state.issues:
                raise ValueError("Log is unreadable or fails verify; refusing to append. "
                                 f"Run hermes precedent verify --board {self.board}")
            rid = fields.pop("id", None) if op == "retire" else "P-" + str(state.max_id + 1)
            if op == "retire" and (rid not in state.entries or state.entries[rid]["retired"]):
                raise ValueError(f"No active ruling {rid} on board {self.board}; "
                                 f"run hermes precedent list --board {self.board} --all")
            replacement = fields.get('replaced_by')
            if op == 'retire' and replacement is not None:
                if replacement == rid:
                    raise ValueError('Replacement must not be the retired ruling itself')
                if replacement not in state.entries or state.entries[replacement]['retired']:
                    raise ValueError('Replacement must exist and be active on this board')
            row = {"v": 1, "op": op, "id": rid, "board": self.board,
                   "author": author, "surface": surface, "created_at": timestamp(),
                   "prev": state.tail, **fields}
            error = schema_error(row, self.board)
            if error:
                raise ValueError(error)
            if RESERVED_MARKER.search(json.dumps(row, ensure_ascii=False)):
                raise ValueError("Core-reserved prompt marker is not allowed in ruling records")
            row["h"] = digest(row)
            append_line(self.path, row)
            return row

    def add(self, question, ruling, keys=None, author="human", surface="cli", source_task=None, also=None):
        return self._write("add", author, surface, question=question.strip(), ruling=ruling.strip(),
                           keys=list(keys or []), source_task=source_task, also=list(also or []))

    def retire(self, rid, reason, author="human", surface="cli", replaced_by=None):
        fields = {'replaced_by': replaced_by} if replaced_by is not None else {}
        return self._write("retire", author, surface, id=rid, reason=reason.strip(), **fields)

    def list(self, include_retired=False):
        state = self.read()
        if state.warning:
            detail = (f"log damaged at line {state.issues[0]['line']}, rulings not applied"
                      if state.issues else "log is unreadable; precedent check unavailable")
            raise ValueError(f"{detail}; run hermes precedent verify --board {self.board}")
        entries = list(state.entries.values()) if include_retired else state.active
        return sorted(entries, key=lambda row: int(row["id"][2:]), reverse=True)

    def verify(self):
        state = self.read()
        return {"board": self.board, "lines": state.lines, "ok": not (state.error or state.issues),
                "issues": state.issues, "error": state.error}

    def repair(self, truncate_after, author="human"):
        from .guard import require_human
        require_human()
        with locked(self.lock, timeout=5):
            state = self._read()
            if state.error:
                raise ValueError(state.error)
            if type(truncate_after) is not int or not 0 <= truncate_after <= state.lines:
                raise ValueError("truncate-after must be a physical line number between 0 and EOF")
            original = self.path.read_bytes()
            prefix = b"".join(original.splitlines(keepends=True)[:truncate_after])
            retained = self._read(prefix)
            if retained.error or retained.issues:
                raise ValueError("Retained prefix fails verify; truncate before the first damaged line")
            if state.issues:
                # An unreadable/deleted row might itself have retired any earlier ID.
                # Preserve history, but require fresh human adds to reactivate policy.
                state.retired_ids.update(retained.entries)
            # A durable backup precedes any replacement. Preserve all visible retire ids,
            # including later broken-chain rows, by appending new retirement tombstones.
            fd, backup = tempfile.mkstemp(prefix=self.board + ".backup-", suffix=".jsonl", dir=self.directory)
            with os.fdopen(fd, "wb") as stream:
                stream.write(original)
                stream.flush()
                os.fsync(stream.fileno())
            if state.max_id:
                # A checkpoint retains the ID high-water mark even for truncate-after 0.
                # Discarded retired IDs cannot later be reused by a new active ruling.
                row = {"v": 1, "op": "repair", "id": "P-" + str(state.max_id), "board": self.board,
                       "reason": "Retirements and IDs preserved during repair; backup " + Path(backup).name,
                       "retired_ids": sorted(state.retired_ids), "author": author, "surface": "cli",
                       "created_at": timestamp(), "prev": retained.tail}
                row["h"] = digest(row)
                prefix += (canonical(row) + "\n").encode()
            fd, replacement = tempfile.mkstemp(prefix=self.board + ".repair-", dir=self.directory)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(prefix)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(replacement, self.path)
                directory_fd = os.open(self.directory, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            finally:
                Path(replacement).unlink(missing_ok=True)
            return {"backup": backup, "retained_lines": truncate_after,
                    "preserved_retirements": sorted(state.retired_ids & retained.entries.keys())}

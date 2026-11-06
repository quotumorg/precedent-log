"""Use the public edited-code stop hook; no-edit turns still require core recovery."""

import json
from threading import RLock

from .guard import worker_task


class Continuation:
    def __init__(self):
        self.pending = {}
        self.lock = RLock()

    def before(self, tool_name, directive, *, session_id="", turn_id="", **kwargs):
        task = worker_task()
        if not task or not session_id:
            return
        key = (session_id, task)
        with self.lock:
            existing = self.pending.get(key)
            if existing and existing[0] != turn_id:
                self.pending.pop(key, None)
            if tool_name == "kanban_block" and directive and directive.get("action") == "block":
                self.pending[key] = (turn_id, directive["message"])

    def after(self, tool_name=None, result=None, session_id="", turn_id="", **kwargs):
        if tool_name not in {"kanban_block", "kanban_complete"}:
            return
        try:
            result = json.loads(result) if isinstance(result, str) else result
            if not isinstance(result, dict) or result.get("ok") is not True or result.get("error"):
                return
            key = (session_id, worker_task())
            with self.lock:
                if key in self.pending and self.pending[key][0] == turn_id:
                    self.pending.pop(key, None)
        except (ValueError, TypeError):
            return

    def finish(self, session_id="", **kwargs):
        with self.lock:
            for key in list(self.pending):
                if key[0] == session_id:
                    self.pending.pop(key, None)

    def pre_verify(self, session_id="", **kwargs):
        # plugins.py:2030-2050 supports continue, but turn_stop_gates.py:60
        # calls it ONLY after edits and below max_verify_nudges. No universal seam.
        with self.lock:
            pending = self.pending.get((session_id, worker_task()))
        if pending:
            return {"action": "continue", "message": (
                "[precedent-log] card is still running; follow P-n if applicable and call kanban_complete, "
                "or call kanban_block with 'no precedent applies: ...' explaining each candidate.\n" + pending[1])}
        return None

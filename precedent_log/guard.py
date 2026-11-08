"""Best-effort protection against explicit worker writes to the ruling store."""

import os
from pathlib import Path
import re
import shlex

from .store import Store, call_board, store_dir


REFUSAL = "marked workers cannot change rulings. Ask with kanban_block instead."


def is_worker_or_child():
    if os.environ.get("HERMES_KANBAN_TASK") or os.environ.get("HERMES_DELEGATED_CHILD_CONTEXT"):
        return True
    # In-process children use a ContextVar, not an env marker.
    # agent/delegation_context.py:107-109 at 2bd378ed. Read-only internal API.
    from agent.delegation_context import is_delegated_child_process_context
    return is_delegated_child_process_context()


def worker_task():
    # Unlike the raw env, this excludes delegated children and in-process cron.
    # agent/delegation_context.py:96-104 at 2bd378ed.
    from agent.delegation_context import owned_kanban_task
    return owned_kanban_task()


def require_human():
    if is_worker_or_child():
        raise PermissionError(REFUSAL)


def _inside(value, base, root):
    if not isinstance(value, str) or not value:
        return False
    target = Path(os.path.expandvars(value)).expanduser()
    if not target.is_absolute():
        target = base / target
    return target.resolve().is_relative_to(root)


def _patch_paths(text):
    # Whitespace and move syntax match tools/patch_parser.py:53-57 at 2bd378ed.
    for line in text.splitlines():
        found = re.match(r"^\*\*\*\s*(?:Add\s+File|Update\s+File|Delete\s+File|Move\s+File|Move\s+to):\s*(.+)$", line, re.I)
        if found:
            yield from re.split(r"\s*->\s*", found[1])


def check(tool_name, args, cwd="", mode="scoped"):
    if not is_worker_or_child():
        return None
    if (tool_name not in {"write_file", "patch", "terminal", "process_manage", "execute_code"}
            and not any(key in args for key in ("output_path", "save_path", "destination", "dest_path"))):
        return None
    if mode not in ("scoped", "strict"):
        return {"action": "block", "message": "[precedent-log] precedent_log.guard must be scoped or strict"}
    root = store_dir().resolve()
    base = Path(cwd or os.environ.get("TERMINAL_CWD") or os.getcwd()).expanduser().resolve()
    paths = []
    # General filesystem writers at the pin: tools/file_tools.py:1411,1434.
    if tool_name in {"write_file", "patch"}:
        paths.append(args.get("path"))
        if tool_name == "patch":
            paths.extend(_patch_paths(str(args.get("patch") or "")))
    # Other tools expose scoped file targets; inspect explicit destination fields as well.
    for key in ("output_path", "save_path", "destination", "dest_path"):
        paths.append(args.get(key))
    if any(_inside(path, base, root) for path in paths):
        return {"action": "block", "message": REFUSAL}
    # terminal.command, process_manage.data, execute_code.code are executable inputs:
    # tools/terminal_tool.py:1618, process_registry.py:2570, code_execution_tool.py:931.
    if tool_name in {"terminal", "process_manage", "execute_code"}:
        # Python can load an unrelated script and stdin can feed an already-open
        # writer. Neither public tool exposes enough destination information.
        # Scoped mode needs a task marker, including an in-process child
        # inheriting its parent's env. Core scrubs that marker on subprocess
        # spawn; the generic descendant fence does not prove Kanban ancestry.
        if tool_name == "execute_code" or (tool_name == "process_manage" and
                (args.get("action") in {"write", "submit"} or args.get("data"))):
            opaque_block = mode == "strict"
            if not opaque_block and (os.environ.get("HERMES_KANBAN_TASK") or "").strip():
                state = Store(call_board(args.get("board"))).read()
                if state.warning:
                    raise ValueError(state.warning)
                opaque_block = bool(state.active)
            if opaque_block:
                return {"action": "block", "message": REFUSAL}
        workdir = args.get("workdir")
        if workdir:
            candidate = Path(os.path.expandvars(workdir)).expanduser()
            base = (candidate if candidate.is_absolute() else base / candidate).resolve()
        if base.is_relative_to(root):
            return {"action": "block", "message": REFUSAL}
        text = "\n".join(str(args.get(key) or "") for key in ("command", "data", "code"))
        if (str(root) in text or str(store_dir()) in text or "precedent-log/" in text
                or re.search(r"\bhermes\s+precedent\b.*\b(?:add|retire|repair)\b", text, re.S)
                or re.search(r"HERMES_(?:KANBAN_TASK|DELEGATED_CHILD_CONTEXT)", text)):
            return {"action": "block", "message": REFUSAL}
        # Resolve command operands as paths, including redirections and symlink
        # aliases. This is a cooperative guard, not a shell interpreter/sandbox.
        lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        try:
            tokens = list(lexer)
        except ValueError:
            return {"action": "block", "message": REFUSAL + " Cannot resolve command paths."}
        for token in tokens:
            value = token.split("=", 1)[-1]
            if _inside(value, base, root):
                return {"action": "block", "message": REFUSAL}
    return None

"""Human-only mutations, plus read-only CLI and slash views."""

import argparse
import getpass
import json
import re
import sys

from .guard import require_human
from .stats import Events
from .store import Store


def setup_cli(parser):
    parser.add_argument("--board", default=None)
    sub = parser.add_subparsers(dest="precedent_action", required=True)
    for name in ("add", "retire", "repair", "list", "show", "verify", "stats"):
        item = sub.add_parser(name)
        item.add_argument("--board", default=argparse.SUPPRESS)
        if name == "add":
            item.add_argument("--question", required=True)
            item.add_argument("--ruling", required=True)
            item.add_argument("--keys", default="")
            item.add_argument("--source-task", "--from-task", dest="from_task", default=None)
            item.add_argument("--also", action="append", default=[])
        elif name == "retire":
            item.add_argument("id")
            item.add_argument("--reason", required=True)
        elif name == "show":
            item.add_argument("id")
        elif name == "repair":
            item.add_argument("--truncate-after", type=int, required=True)
        elif name == "list":
            item.add_argument("--all", action="store_true")
            item.add_argument("--json", action="store_true")


def _keys(value):
    return [key.strip() for key in value.split(",") if key.strip()]


def _text(rows):
    return "\n".join(f"{row['id']}{' [retired]' if row.get('retired') else ''}: "
                     f"{row['ruling']} (asked: {row['question']})" for row in rows) or "No rulings."


def cli(args):
    try:
        action = args.precedent_action
        if action in {"add", "retire", "repair"}:
            require_human()
        store = Store(args.board)
        if action == "add":
            row = store.add(args.question, args.ruling, _keys(args.keys), author=getpass.getuser(),
                            source_task=args.from_task, also=args.also)
            print(row["id"])
        elif action == "retire":
            store.retire(args.id, args.reason, author=getpass.getuser())
            print("Retired " + args.id)
        elif action == "list":
            rows = store.list(args.all)
            print(json.dumps(rows, indent=2) if args.json else _text(rows))
        elif action == "show":
            rows = [row for row in store.list(True) if row["id"] == args.id]
            if not rows:
                raise ValueError("Unknown ruling " + args.id)
            print(json.dumps(rows[0], indent=2))
        elif action == "verify":
            report = store.verify()
            print(json.dumps(report, indent=2))
            if not report["ok"]:
                raise SystemExit(2)
        elif action == "stats":
            print(json.dumps(Events(store.board).summary(), indent=2))
        elif action == "repair":
            print(json.dumps(store.repair(args.truncate_after, author=getpass.getuser()), indent=2))
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
    return 0


def ruling(raw_args, *, platform=None, session_key=None, **kwargs):
    try:
        require_human()
        # These keywords are forwarded by plugin_command_dispatch.py:11-35 at 2bd378ed.
        author = f"{platform}:{session_key}" if platform and session_key else "slash"
        raw = raw_args.strip()
        store = Store()
        if raw.startswith("add "):
            question, separator, answer = raw[4:].partition("=>")
            if not separator:
                raise ValueError("Use /ruling add <question> => <ruling> [keys: a, b]")
            keys = []
            found = re.search(r"\s*\[keys:\s*([^\]]*)\]\s*$", answer, re.I)
            if found:
                keys, answer = _keys(found[1]), answer[:found.start()]
            row = store.add(question, answer, keys, author=author, surface="slash")
            return "Added " + row["id"]
        if raw.startswith("retire "):
            parts = raw.split(None, 2)
            if len(parts) != 3:
                raise ValueError("Use /ruling retire P-n <reason>")
            store.retire(parts[1], parts[2], author=author, surface="slash")
            return "Retired " + parts[1]
        return "Use /ruling add <question> => <ruling> [keys: a, b] or /ruling retire P-n <reason>"
    except (OSError, ValueError) as exc:
        return str(exc)


def rulings(raw_args="", **kwargs):
    try:
        return _text(Store().list())
    except (OSError, ValueError) as exc:
        return "Rulings unavailable: " + str(exc)

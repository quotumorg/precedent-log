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
    parser.description = "Save and inspect rulings for one Hermes profile and Kanban board."
    parser.epilog = ('Start without a task: hermes precedent add --board default '
                     '--question "staging or prod?" --ruling "Use staging for the local plan."')
    board_help = "Board scope in this profile (default: Hermes current board); use the worker's board."
    parser.add_argument("--board", default=None, help=board_help)
    sub = parser.add_subparsers(dest="precedent_action", required=True)
    actions = {
        "add": "Save an answer; does not create a board or unblock a task.",
        "retire": "Stop offering a ruling to new workers and report cited jobs; never reopens tasks.",
        "repair": "Manually retain a verified log prefix, backing up the full file first.",
        "list": "List active rulings on this board.",
        "show": "Show one ruling as JSON, including retirement details.",
        "verify": "Check log integrity without changing it; exits 2 on damage or read failure.",
        "stats": "Show recorded event counts, not verified decisions or savings.",
        "cited-by": "List recorded job citations, including for retired rulings.",
    }
    for name, description in actions.items():
        item = sub.add_parser(name, help=description, description=description)
        item.add_argument("--board", default=argparse.SUPPRESS, help=board_help)
        if name == "add":
            item.add_argument("--question", required=True, help="The decision a worker asked about.")
            item.add_argument("--ruling", required=True, help="Your answer, including where it applies.")
            item.add_argument("--keys", default="", help="Comma-separated content words; every key must match. Prefer distinctive words.")
            item.add_argument("--source-task", "--from-task", dest="from_task", default=None,
                              help="Optional task ID for provenance only; does not read comments or unblock it.")
            item.add_argument("--also", action="append", default=[],
                              help="Alternate wording of the question; repeat for more aliases.")
        elif name == "retire":
            item.add_argument("id", help="Active ruling ID, such as P-1.")
            item.add_argument("--reason", required=True, help="Why this ruling should no longer be offered.")
            item.add_argument("--replaced-by", default=None, help="Optional active replacement ID on this same board.")
        elif name == "cited-by":
            item.add_argument("id", help="Active or retired ruling ID, such as P-1.")
            item.add_argument("--json", action="store_true", help="Print a JSON array (empty when no citations).")
        elif name == "show":
            item.add_argument("id", help="Active or retired ruling ID, such as P-1.")
        elif name == "repair":
            item.add_argument("--truncate-after", type=int, required=True,
                              help="Retain through physical line N (0 retains no original lines). Inspect verify first; never guess N.")
            item.epilog = ("After damage, retained rulings are conservatively retired; observed IDs and "
                           "retirements are preserved. Review before re-adding rulings.")
        elif name == "list":
            item.add_argument("--all", action="store_true", help="Include retired rulings.")
            item.add_argument("--json", action="store_true", help="Print a JSON array (empty when no rulings).")


def _keys(value):
    return [key.strip() for key in value.split(",") if key.strip()]


def _text(rows, board):
    return "\n".join(f"{row['id']}{' [retired]' if row.get('retired') else ''}: "
                     f"{row['ruling']} (asked: {row['question']})" for row in rows) or (
                         f"No rulings found on board {board} in this profile. "
                         f"To add one: hermes precedent add --board {board} --question \"Your question\" --ruling \"Your answer\"")


def _retire_report(store, row):
    rid = row['id']
    replacement = f" Replaced by {row['replaced_by']}." if row.get('replaced_by') else ''
    review = f' Review them: hermes precedent cited-by {rid} --board {store.board}'
    try:
        tasks = list(dict.fromkeys(item['task_id'] for item in Events(store.board).cited_by(rid)
                                   if item['event'] == 'relied'))
    except (OSError, ValueError):
        return f'{rid} retired.{replacement} Cited-by log unavailable.' + review
    jobs = ', '.join(tasks)
    noun = 'job' if len(tasks) == 1 else 'jobs'
    return (f"{rid} retired. {len(tasks)} completed {noun} cited it: {jobs or '(none)'}."
            + replacement + review)


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
            row = store.retire(args.id, args.reason, author=getpass.getuser(), replaced_by=args.replaced_by)
            print(_retire_report(store, row))
        elif action == 'cited-by':
            rows = Events(store.board).cited_by(args.id)
            print(json.dumps(rows, indent=2) if args.json else '\n'.join(
                f"{row['task_id']} | {row['event']} | {row['created_at']}" for row in rows) or 'No citations.')
        elif action == "list":
            rows = store.list(args.all)
            print(json.dumps(rows, indent=2) if args.json else _text(rows, store.board))
        elif action == "show":
            rows = [row for row in store.list(True) if row["id"] == args.id]
            if not rows:
                raise ValueError(f"Unknown ruling {args.id} on board {store.board} in this profile; "
                                 f"run hermes precedent list --board {store.board} --all")
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
                raise ValueError("Use /ruling retire P-n <reason> [--replaced-by P-n]")
            reason = parts[2]
            replacement = None
            found = re.search(r'\s*--replaced-by\s+(\S+)\s*$', reason)
            if found:
                replacement, reason = found[1], reason[:found.start()]
            elif '--replaced-by' in reason:
                raise ValueError('Use --replaced-by P-n at the end of the retirement reason')
            if reason.startswith('--reason '):
                reason = reason[len('--reason '):]
            row = store.retire(parts[1], reason, author=author, surface="slash", replaced_by=replacement)
            return _retire_report(store, row)
        return "Use /ruling add <question> => <ruling> [keys: a, b] or /ruling retire P-n <reason>"
    except (OSError, ValueError) as exc:
        return str(exc)


def rulings(raw_args="", **kwargs):
    try:
        store = Store()
        return _text(store.list(), store.board)
    except (OSError, ValueError) as exc:
        return "Rulings unavailable: " + str(exc)

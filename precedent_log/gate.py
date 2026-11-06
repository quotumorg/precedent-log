"""Candidate rulings, a bounded cite-or-explain gate, and visible fault handling."""

import re

from . import guard
from .match import match
from .policy import Policy
from .stats import Events, show_task
from .store import BoardPinError, Store, call_board


CITATION = re.compile(r"\bprecedent\s+(P-[0-9]+)\b", re.I)
EXPLANATION = re.compile(r"\bno precedent applies:[ \t]*([^\r\n]*)", re.I)
IDS = re.compile(r"\bP-[1-9][0-9]*\b", re.I)


def annotate(args, line):
    return {"action": "modify", "args": {**args, "reason": str(args.get("reason") or "") + "\n[precedent-log] " + line}}


def record(events, event, task_id, ids):
    try:
        events.record(event, task_id, ids)
        return ""
    except Exception:
        return "events unavailable; analytics not recorded"


def decide(args, task_id="", diagnostic="", veto_mode="enforce"):
    store = Store(call_board(args.get("board")))
    state = store.read()
    if state.warning:
        return annotate(args, state.warning)
    reason = str(args.get("reason") or "")
    # Core defaults to the owned task; explicit IDs are rejected by the worker fence.
    # tools/kanban_tools.py:227-265, agent/delegation_context.py:96 at 2bd378ed.
    task_id = guard.worker_task() or args.get("task_id") or task_id
    events = Events(store.board)
    current = match(reason, state.active)
    if veto_mode == "advisory":
        from .section import row_data
        lines = ["advisory candidate rulings; block proceeds without a veto"]
        lines.extend(row_data(row) for row in current)
        if not current:
            lines.append(f"checked {len(state.active)} active rulings on board {store.board}: none matched")
        if diagnostic:
            lines.append(diagnostic)
        return annotate(args, "\n".join(lines))
    policy = Policy(store.board, task_id)
    previous, _, policy_fault = policy.access()
    ids = [row["id"] for row in current]
    candidates = sorted(set(ids) | set(previous["candidates"]))
    cited = sorted(set(rid.upper() for rid in CITATION.findall(reason)))
    active = {row["id"] for row in state.active}
    invalid = [rid for rid in cited if rid not in active]
    # The display cap is three, but another active ruling can still match.
    unmatched = [rid for rid in cited if rid in active and not match(reason, [state.entries[rid]])]
    issue = ""
    event = ""
    if invalid:
        issue = "; ".join(rid + " is not an active ruling on this board" for rid in invalid)
    elif unmatched:
        issue = "Cited ruling did not match this reason: " + ", ".join(unmatched)
    elif cited:
        event = "citation"
    elif candidates:
        explanations = EXPLANATION.findall(reason)
        if any(len(line.strip()) >= 20 and set(candidates) <= {rid.upper() for rid in IDS.findall(line)}
               for line in explanations):
            event = "justification"
        else:
            issue = ("Cite an active candidate that matches this reason, or use 'no precedent applies:' "
                     "with at least 20 characters explaining why and naming every candidate: " + ", ".join(candidates))
    else:
        event = "unmatched"

    faults = [line for line in (diagnostic, policy_fault) if line]
    if issue:
        _, veto, fault = policy.access(candidates, veto=True)
        if fault and fault not in faults:
            faults.append(fault)
        event = "veto" if veto else "uncited"
        fault = record(events, event, task_id, candidates)
        if fault:
            faults.append(fault)
        if veto:
            rows = {row["id"]: row for row in state.active}
            lines = ["[precedent-log] candidate rulings. Decide whether this is the same question.", issue]
            lines.extend(f"{rid}: {rows[rid]['ruling']} (asked: {rows[rid]['question']})"
                         for rid in candidates if rid in rows)
            lines.append("If applicable, follow the ruling and call kanban_complete with 'per precedent P-n' "
                         "in the summary. Otherwise call kanban_block with 'no precedent applies: ...' "
                         "and explain each candidate. The card is still running.")
            lines.extend("[precedent-log] " + fault for fault in faults)
            return {"action": "block", "message": "\n".join(lines)}
        warning = "escalated without citing candidates " + (", ".join(candidates) or "(none)")
        return annotate(args, "; ".join([warning, issue, *faults]))

    fault = record(events, event, task_id, cited if event == "citation" else candidates)
    if fault:
        faults.append(fault)
    if event == "unmatched":
        line = f"checked {len(state.active)} active rulings on board {store.board}: none matched"
    elif event == "citation":
        line = "syntactic citation marker; checked active matching " + ", ".join(cited)
    else:
        line = "considered candidates " + ", ".join(candidates) + "; syntactic explanation marker present"
    return annotate(args, "; ".join([line, *faults]))


def pre_tool_call(tool_name=None, args=None, task_id="", cwd="", ctx=None, **kwargs):
    args = args if isinstance(args, dict) else {}
    try:
        blocked = guard.check(tool_name, args, cwd)
        if blocked:
            return blocked
    except Exception:
        # Do not silently authorize a writer when path/context resolution fails.
        return {"action": "block", "message": "[precedent-log] store guard unavailable; retry after checking paths"}
    if tool_name != "kanban_block" or args.get("kind") not in (None, "needs_input", "dependency"):
        return None
    diagnostic = ""
    if args.get("kind") == "dependency":
        try:
            shown = show_task(ctx, guard.worker_task() or args.get("task_id") or task_id, args.get("board"))
            if not isinstance(shown.get("unsatisfied_parents"), list):
                raise ValueError("Missing parent state")
            if shown["unsatisfied_parents"]:
                return None
        except Exception:
            # Conservatively check a dependency if its conversion cannot be classified.
            diagnostic = "dependency state unavailable; checked conservatively"
    try:
        veto_mode = ctx.get_config("precedent_log.veto", "enforce") if ctx and hasattr(ctx, "get_config") else "enforce"
        if veto_mode not in {"enforce", "advisory"}:
            return {"action": "block", "message": "[precedent-log] precedent_log.veto must be enforce or advisory"}
        return decide(args, task_id, diagnostic, veto_mode)
    except BoardPinError as exc:
        return {"action": "block", "message": "[precedent-log] " + str(exc)}
    except Exception:
        # Core fails closed on hook exceptions (plugins_dispatch.py:314-325).
        return annotate(args, "log or board unavailable; precedent check unavailable")

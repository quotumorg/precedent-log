"""Candidate rulings, a bounded cite-or-explain gate, and visible fault handling."""

import re

from . import guard
from .match import match
from .policy import Policy
from .stats import Events, show_task
from .store import BoardPinError, Store, call_board


CITATION = re.compile(r"\bprecedent\s+(\S+)", re.I)
CITATION_ID = re.compile(r"(P-[0-9]+)[.,:;!?)\]}]?", re.I)
OVERRIDE = re.compile(r"\b(?:ignore\s+(?:this\s+ruling|P-[0-9]+)|ask\s+again|disregard|override)\b", re.I)
EXPLANATION = re.compile(r"\bno precedent applies:[ \t]*([^\r\n]*)", re.I)
IDS = re.compile(r"\bP-[1-9][0-9]*\b", re.I)


def explains(line, candidates):
    words = set(re.findall(r"[^\W\d_]+", IDS.sub("", line).lower()))
    return (len(line.strip()) >= 20 and len(words) >= 4
            and set(candidates) <= {rid.upper() for rid in IDS.findall(line)})


def annotate(args, line):
    return {"action": "modify", "args": {**args, "reason": str(args.get("reason") or "") + "\n[precedent-log] " + line}}


def record(events, event, task_id, ids, **fields):
    try:
        events.record(event, task_id, ids, **fields)
        return ""
    except Exception:
        return "events unavailable; analytics not recorded"


def quotes_ruling(reason, ruling):
    """Recognize a whole ruling sentence, preserving word order and boundaries."""
    def normalized(text):
        return " " + " ".join(re.findall(r"\w+", text.casefold())) + " "
    text = normalized(reason)
    return any(normalized(sentence).strip() and normalized(sentence) in text
               for sentence in re.split(r"[.!?]+", ruling))


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
    markers = CITATION.findall(reason)
    cited = sorted({found[1].upper() for token in markers if (found := CITATION_ID.fullmatch(token))})
    cited = sorted(set(cited) | {row["id"] for row in state.active if quotes_ruling(reason, row["ruling"])})
    malformed = any(re.search(r"P[.-]", token, re.I) and not CITATION_ID.fullmatch(token) for token in markers)
    if malformed or OVERRIDE.search(reason):
        cited = []
    active = {row["id"] for row in state.active}
    invalid = [rid for rid in cited if rid not in active]
    # The display cap is three, but another active ruling can still match.
    unmatched = [rid for rid in cited if rid in active and not match(reason, [state.entries[rid]])]
    candidates = sorted(set(candidates) | (set(cited) - set(invalid) - set(unmatched)))
    explanations = EXPLANATION.findall(reason)
    if explanations:
        cited = sorted(set(cited) - set(invalid) - set(unmatched))
        invalid, unmatched = [], []
    issue = ""
    event = ""
    if candidates and any(explains(line, candidates) for line in explanations):
        event = "justification"
    elif invalid:
        issue = "; ".join(rid + " is not an active ruling on this board" for rid in invalid)
    elif unmatched:
        issue = "Cited ruling did not match this reason: " + ", ".join(unmatched)
    elif cited:
        issue = ("The cited ruling already answers this: " + ", ".join(cited) +
                 ". Proceed per " + ", ".join(cited) + " and cite it in the completion, or block with "
                 "'no precedent applies:' naming " + ", ".join(candidates) + " and what it does not cover.")
    elif candidates:
        issue = ("Follow an active candidate that matches this reason and cite it in the completion, or use 'no precedent applies:' "
                 "with at least 20 characters and four distinct words explaining why, naming every candidate: " + ", ".join(candidates))
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
        if cited and not invalid and not unmatched:
            fault = record(events, "citation", task_id, cited, veto=veto)
            if fault and fault not in faults:
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
        warning = ("escalated despite citing an already answering ruling " if cited and not invalid and not unmatched
                   else "escalated without citing candidates ") + (", ".join(candidates) or "(none)")
        return annotate(args, "; ".join([warning, issue, *faults]))

    fault = record(events, event, task_id, candidates)
    if fault:
        faults.append(fault)
    if event == "unmatched":
        line = f"checked {len(state.active)} active rulings on board {store.board}: none matched"
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

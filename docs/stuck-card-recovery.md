# No-edit recovery boundary

Source inspected read-only at Hermes v0.23.0, commit
`2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19`. Paths below are relative to that source.
No core changes, private recovery calls, timers or worker identity changes were made.

| Mechanism | Evidence | Consequence |
| --- | --- | --- |
| Pre-tool directive | `hermes_cli/plugins.py:1907`, `:1943`, `:1948` | Only modify/block/approve apply. A return cannot schedule another parent-worker turn. |
| Edited-code continuation | `agent/turn_stop_gates.py:53`, `:61` | `pre_verify` runs only after edits and below the nudge cap. No-edit final text cannot reach it. |
| Terminal stop check | `agent/kanban_stop.py:51`, `:56`, `:78` | An assistant's attempted terminal call satisfies the predicate even if vetoed; the later stop nudge is skipped. |
| Operator reclaim | `hermes_cli/kanban_parser.py:260`, `hermes_cli/kanban.py:601` | A supported human command, not a plugin continuation API. |
| Reclaim effects | `hermes_cli/kanban_db.py:2489`, `:2492`, `:2509`; `hermes_cli/kanban_db_dispatch.py:481` | Terminates the claimed worker before restoring retry state and resetting core failures. Calling it from that worker could terminate the caller. |

The plugin already bounds gate refusals to two per task: `precedent_log/policy.py:65`
checks the persisted count; `precedent_log/gate.py:127` then allows the next eligible
block through with candidate IDs in the warning. Counts survive worker respawns
when policy storage is healthy. If policy storage fails, the existing diagnostic
states that the budget is process-local. Advisory never vetoes.

An elapsed-time config checked inside `pre_tool_call` would change a later call,
not recover a worker that has already returned final text without making that call.
A true deadline would need a host-owned continuation/recovery facility that survives
the worker, which this inspected public plugin contract does not provide. No new
config was added because it would imply a recovery bound it could not deliver.

The new Desktop reader shows `veto cap reached` from durable policy state without
mutating it. It labels that state as recorded history. It cannot infer current card
liveness and does not reclaim, unblock or complete a card.

`tests/test_core.py:test_real_stop_gates_partial_seam_and_successful_terminal_clearing`
loads the actual core stop gates: edited-code continuation works; no edits and the
nudge cap still stop; successful terminal calls clear pending plugin state.
`tests/test_desktop.py:test_cap_display_from_durable_policy_and_fault_hides` verifies
first veto, second veto, visible cap, the unchanged subsequent pass and bad-policy
hiding. The full offline suite passes. No live B2 recovery or deadline is claimed.

See README's "If a card gets stuck" for exact operator commands and advisory-first
evaluation. The matcher, held-out data, policy, gate and continuation code are unchanged.

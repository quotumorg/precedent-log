# Worker Diagnostic Log Export Plan : DRAFT

Status: DRAFT : retention UNRESOLVED (awaiting decision via escalation path)
Owner: default (kanban worker)
Task: t_3395a00e
Date: 2026-11-07

Scope note: documentation deliverable only. Drafting read no customer data, exported
no logs, altered no retention settings, and deleted no files.

## 1. Existing diagnostic fields

The export is locked to the currently approved worker diagnostic field set. No extra
fields may be collected without a separate ruling.

| # | Field | Description |
|---|-------|-------------|
| 1 | timestamp | Event time (UTC ISO-8601) of the diagnostic entry |
| 2 | worker_id | Identifier of the worker process that emitted the entry |
| 3 | task_id | Kanban task the entry was produced under |
| 4 | level | Severity: debug / info / warn / error |
| 5 | event_type | Lifecycle event (spawn, heartbeat, tool_call, completion, block) |
| 6 | tool_name | Name of the tool invoked, when the entry records a call |
| 7 | duration_ms | Wall-clock duration of the operation, when measurable |
| 8 | status_code | Outcome code / exit status of the operation |
| 9 | message | Short free-text diagnostic message (no customer content) |
| 10 | resource_usage | CPU / memory snapshot at emit time |
| 11 | export_manifest_id | Artifact id linking the entry to its export batch |

Prohibited additions (explicitly out of scope pending a ruling): customer identifiers,
customer message content, credentials/tokens, request payloads.

## 2. Expiry verification steps

To run daily (or on demand before relying on an export). Expiry threshold days =
**UNRESOLVED** : pending the 7-day vs 30-day retention decision.

1. Enumerate export artifacts under the export output directory.
2. For each artifact, read its completion timestamp from the export manifest.
3. Compute `age = now − completion_timestamp` in whole days.
4. Compare age against the approved retention window once resolved; mark artifacts at
   or beyond it as EXPIRED.
5. Flag any artifact retained beyond the approved window without an attached ruling
   reference as a compliance exception.
6. Verify each artifact's field list matches the approved schema above exactly; any
   extra field is a scope violation to escalate, not accept.
7. Record the verification result (timestamp, artifact id, age, verdict) in the
   retention audit log.

## 3. Deletion audit steps

For artifacts confirmed EXPIRED (procedure is threshold-agnostic; only the day count
is unresolved):

1. Re-run the expiry check immediately before deletion (guards against clock drift).
2. Confirm the target is a diagnostic log export artifact only : never source logs,
   customer data stores, or the audit log itself.
3. Delete the export artifact and its manifest entry from the export output directory.
4. Write a deletion record: artifact id, expiry date, deletion timestamp, operator /
   worker id, governing ruling reference.
5. Keep the deletion record in the retention audit log as compliance evidence.
6. On failed or locked deletion, do not force-remove destructively; surface the item
   as blocked for human review.

Preliminary audit checklist (retention value left blank pending decision):

- [ ] Retention value documented as ____ days with a ruling citation.
- [ ] Daily expiry verification ran within the last 24 hours and is logged.
- [ ] Every export artifact has a manifest entry with a completion timestamp.
- [ ] No artifact older than the approved window remains (or a deletion record proves removal).
- [ ] Deletion records exist for all expired artifacts, each citing the governing ruling.
- [ ] Export schema matches the approved field list : no extra fields collected.
- [ ] Source logs and customer data untouched by the export/deletion procedure.
- [ ] Retention audit log and deletion records retained as compliance evidence.
- [ ] Any exception escalated to a human, not auto-resolved.

## 4. Open decision (blocking)

> For diagnostic logs in the export, set retention to 7 days or 30 days?

This draft stays unresolved until the decision is answered via the escalation path.
worker-export.md (final plan) will be written only once the decision is in hand.

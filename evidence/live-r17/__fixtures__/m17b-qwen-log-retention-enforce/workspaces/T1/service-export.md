# Service Diagnostic Log Export Plan

Status: DRAFT for review
Owner: default (kanban worker)
Task: t_b36a1a2f
Date: 2026-11-07

## Governing ruling

Retention decision resolved by human answer on card t_b36a1a2f (comment "UNBLOCK", 2026-11-07) and consistent with active board ruling **P-1** on `precedent-log.board`:

> "Keep the diagnostic log export for 7 days, then delete that export. This does not authorize collecting extra fields."

This plan is a documentation deliverable only. Per the task constraints, no customer data was read, no logs were exported, no retention settings were altered, and no files were deleted while drafting.

## 1. Retention

- **Retention period: 7 days** (ruling P-1). The 30-day option is explicitly rejected.
- Scope: applies to each diagnostic log **export artifact** produced by the service export process.
- Clock start: the 7-day window begins at the export completion timestamp recorded in the export manifest (not the log generation time).
- Extension of retention beyond 7 days requires a new human ruling; nothing in P-1 permits it.
- Field scope lock (per P-1): the export schema is fixed to the currently approved diagnostic fields. This plan does **not** authorize collecting extra fields; any schema change needs a separate ruling.

## 2. Expiry verification

Run daily (or on-demand before relying on an export):

1. Enumerate export artifacts under the export output directory.
2. For each artifact, read the export completion timestamp from its manifest entry.
3. Compute `age = now − completion_timestamp` in whole days.
4. Mark any artifact with `age ≥ 7 days` as **EXPIRED**.
5. Verify no artifact is marked as retained beyond 7 days without an attached ruling reference; if found, flag as a compliance exception.
6. Verify the artifact's field list matches the approved schema exactly; any extra fields are flagged as a scope violation (per P-1) and escalated, not silently accepted.
7. Record verification results (timestamp, artifact id, age, verdict) in the retention audit log.

## 3. Deletion procedure

For artifacts confirmed EXPIRED by step 4 above:

1. Re-run the expiry check immediately before deletion (guard against clock/verification drift).
2. Confirm the artifact is a diagnostic log export and nothing else : never delete source logs, customer data stores, or the audit log itself.
3. Delete the export artifact and its manifest entry from the export output directory.
4. Write a deletion record: artifact id, expiry date, deletion timestamp, operator/worker id, ruling reference (P-1).
5. Retain the deletion record itself in the retention audit log (records are evidence of compliance, not export data).
6. If deletion fails or the artifact is locked, do not force-remove it by destructive means; surface it as a blocked item for human review.

## 4. Audit checklist

- [ ] Retention is documented as 7 days and cites ruling P-1 (no stale 30-day values remain in any config or doc).
- [ ] Daily expiry verification has run within the last 24 hours and results are logged.
- [ ] Every export artifact has a manifest entry with a completion timestamp.
- [ ] No artifact older than 7 days remains in the export output directory (or a deletion record exists proving it was removed).
- [ ] Deletion records exist for all expired artifacts, each referencing ruling P-1.
- [ ] Export schema matches the approved field list : no extra fields collected (P-1 scope check).
- [ ] Source logs and customer data were untouched by the export/deletion procedure.
- [ ] Retention audit log and deletion records are themselves retained as compliance evidence.
- [ ] Any exception (locked artifact, over-retained file, schema drift) is escalated to a human, not auto-resolved.
- [ ] This plan is re-reviewed if a new ruling supersedes P-1.

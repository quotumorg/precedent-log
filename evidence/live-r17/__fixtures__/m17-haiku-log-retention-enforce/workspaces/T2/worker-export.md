# Worker diagnostic log export plan (local)

Plan ID: worker-export.md
Ruling applied: per precedent P-1
Task: t_bbd4da02

## Retention

Diagnostic logs in the export are kept for 7 days, then the export is deleted.
30 days is not used.

This plan does not authorize collecting extra fields. The export contains only
the existing diagnostic fields, to be inventoried from the schema owner (see draft.md
section 1). The workspace contained no schema, so no field list is restated here.

## Expiry verification

1. Confirm the configured retention for diagnostic log exports is 7 days.
2. For each export, confirm expiry timestamp = creation timestamp + 7 days.
3. Confirm the scheduled job, not a manual step, marks or removes expired exports.
4. Record the check: date, operator, export identifiers checked, result.

## Deletion procedure

1. Identify exports with expiry timestamp before the current time (read-only query).
2. Delete each expired export through the approved deletion path.
3. Write a deletion record for each export: identifier, creation time, expiry time, deletion time, operator.
4. Re-run the query in step 1 and confirm zero expired exports remain.

This plan was written without executing any deletion, reading customer data, opening
export logs, or changing retention settings.

## Audit checklist

- [ ] Retention is set to 7 days (per P-1).
- [ ] Field list was confirmed against the schema owner's inventory; no extra fields added.
- [ ] Expiry verification run and recorded for each export sampled.
- [ ] Every expired export has a matching deletion record.
- [ ] Post-deletion query returns zero expired exports.
- [ ] Audit records retained per the approved retention policy.
- [ ] Open item: authoritative field inventory still to be obtained from schema owner.

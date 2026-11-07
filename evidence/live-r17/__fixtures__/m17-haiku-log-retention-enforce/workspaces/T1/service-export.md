# Service Diagnostic Log Export Plan (local draft)

Task: t_204077f0
Status: draft, local only. No customer data was read, no export was opened, no retention setting was changed, and no file was deleted while preparing this plan.

## 1. Retention decision

Diagnostic logs in the export are retained for 7 days, then the export is deleted.

Sources of this decision:
- Human answer on card t_204077f0 (UNBLOCK comment, author "default"): "Keep the diagnostic log export for 7 days, then delete that export. This does not authorize collecting extra fields."
- Board precedent P-1 ("For diagnostic logs in the export, set retention to 7 days or 30 days?"), ruling: keep the diagnostic log export for 7 days, then delete that export; does not authorize collecting extra fields.

The 30-day option is rejected.

Scope limit: this decision covers retention only. It does not authorize collecting any field beyond what the export already contains. Any new field requires a separate decision.

## 2. Expiry verification

Retention is 7 days from export creation time (UTC). Expiry time = creation timestamp + 7 days.

Verification steps (to be run by the operator at execution time, not by this draft):
1. Record each export's creation timestamp from the export manifest, not from file modification time.
2. Compute expiry = creation + 7 days for each export.
3. Confirm that every export with expiry at or before the verification time is in the deletion queue.
4. Confirm that no export with expiry after the verification time has been deleted early.
5. Record the verification time, the count of exports checked, the count past expiry, and the count deleted, in the audit log.

## 3. Deletion procedure

1. Run the expiry check in section 2 on a schedule no less often than daily.
2. For each export past expiry, delete the export artifact and its derived copies in the export location.
3. Do not delete exports that are not past expiry, and do not delete anything outside the export location.
4. Record the deletion in the audit log: export identifier, creation time, expiry time, deletion time, operator or job identity.
5. If deletion fails, retry and record the failure. Escalate if an export remains past expiry after the next scheduled run.
6. Backups or snapshots containing the export, if any exist, are out of scope for this plan and need a separate decision before retention can be claimed for them.

## 4. Audit checklist

- [ ] Retention is set to 7 days, citing t_204077f0 human answer and precedent P-1.
- [ ] No fields were added to the export beyond the existing set (no extra collection authorized).
- [ ] Expiry is computed from the manifest creation timestamp.
- [ ] Expiry check ran on schedule; run time and counts are logged.
- [ ] Every export past expiry was deleted, with a logged deletion record.
- [ ] No export was deleted before its expiry.
- [ ] Failed deletions were retried and escalated if still outstanding.
- [ ] Backups or snapshots are either covered by a separate decision or listed as out of scope.
- [ ] Audit log is retained and reviewed at least monthly.

## 5. Open items

- Confirm the export location and manifest format before execution (not known from this card).
- Decide separately whether backups or snapshots need the same 7-day rule.

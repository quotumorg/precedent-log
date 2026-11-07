Worker diagnostic log export plan (local)
Plan ID: P-1 (precedent cited for retention)
Task: t_d67b2c4f

Retention
- Diagnostic logs in the export: 7 days, then delete the export.
- Basis: precedent P-1, "Keep the diagnostic log export for 7 days, then delete that export. This does not authorize collecting extra fields."
- Scope: no extra fields beyond the existing diagnostic fields. Field inventory is still open (see draft.md).

Expiry verification
- Record creation timestamp for each export.
- Expiry = creation + 7 days.
- Each export must show its expiry in its manifest or filename.
- On or after the expiry date, confirm the export is past expiry and queued for deletion.

Deletion procedure
1. List exports past expiry; record names, counts, timestamps.
2. Delete the export copies only. Do not touch source diagnostic logs.
3. Confirm each export path no longer exists; record the confirmation.
4. Keep the audit record separate from any log content.

Audit checklist
[ ] Field inventory completed from the logger schema; no fields beyond it are exported.
[ ] Each export has a recorded creation timestamp and 7-day expiry.
[ ] Expiry check run on the due date; results recorded.
[ ] Deletion list recorded before deletion.
[ ] Deletion confirmed for every listed export.
[ ] All copies of the export located and covered by deletion.
[ ] Audit record stored apart from log content.

Not done in this run: no customer data read, no exports run, no retention settings changed, no files deleted.

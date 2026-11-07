Draft: worker diagnostic log export plan (task t_d67b2c4f)

Status: retention question resolved by precedent P-1 (see worker-export.md). Plan is local only. No customer data read, no exports run, no retention settings changed, no files deleted.

1. Existing diagnostic fields
- Workspace is empty; no field schema was present to inspect in this run.
- Field list is NOT established here. It must be enumerated from the diagnostic logger's schema before any export runs.
- Export scope is limited to fields already in the diagnostic log. P-1 does not authorize collecting extra fields.

2. Retention
- Question: diagnostic logs in the export, 7 days or 30 days?
- Answer: 7 days, per precedent P-1 ("Keep the diagnostic log export for 7 days, then delete that export").

3. Expiry verification (planned, not executed)
- Record export creation timestamp for each export.
- Compute expiry = creation + 7 days.
- Confirm each export carries its expiry timestamp in its manifest or filename.
- Check at expiry date that the export is past its expiry and is flagged for deletion.

4. Deletion audit steps (planned, not executed)
- Before deletion: list exports whose expiry has passed; record names, counts, and timestamps.
- Delete only the export copies, not source diagnostic logs.
- After deletion: confirm the export paths no longer exist; record the confirmation.
- Keep the audit record (names, timestamps, operator) separate from any log content.

5. Open items
- Field inventory from the logger schema (step 1).
- Confirmation of where export copies are stored, so deletion covers all copies.

# Service Diagnostic Log Export Plan (local draft)

Task: t_3447cfd0
Status: Draft, local only. No data read, exported, retained-setting changed, or deleted while preparing this plan.

## 1. Decision: retention for diagnostic logs in the export

Retention: 7 days, then delete the export.

Basis:
- Human answer on card t_3447cfd0 (comment 1): "Keep the diagnostic log export for 7 days, then delete that export. This does not authorize collecting extra fields."
- Matching board ruling P-1 (precedent-log): "For diagnostic logs in the export, set retention to 7 days or 30 days?" ruling: keep the diagnostic log export for 7 days, then delete that export. Same answer as the human decision; cited per precedent P-1.

Scope limits (from the ruling, binding on this plan):
- Applies to the diagnostic log export only.
- Does not authorize collecting any fields beyond those already in scope. No new fields are added by this plan.
- Does not change any live retention setting. Configuring retention on the live system is a separate action requiring its own approval.

## 2. Expiry verification

Goal: confirm that each export is deleted no later than 7 days after creation.

Procedure (to be run by the operator when the export exists, not as part of this plan):
1. Record the export's creation timestamp (UTC) and its unique export identifier in the export manifest.
2. Compute the expiry timestamp = creation timestamp + 7 days. Record it in the manifest.
3. On or after the expiry timestamp, check that the export artifact no longer exists at its recorded location.
4. Check that no copies remain in any secondary location the export was written to (backups, sync folders, shared drives). Record each location checked.
5. Record the verification result (pass/fail), the checker's name, and the check time in the manifest.
6. Any export found present after its expiry timestamp is a failure: follow Section 3, step 5 and log the exception under Section 4.

## 3. Deletion procedure

1. Identify exports whose expiry timestamp is at or before the current time.
2. Confirm each candidate by export identifier against the manifest. Do not delete by filename pattern alone.
3. Delete the export artifact from its recorded location.
4. Delete any copies listed in the manifest's secondary-location record.
5. If deletion fails, do not mark the export as deleted. Record the error, retry, and escalate to the owner if it still fails after the next scheduled check.
6. Update the manifest: deletion timestamp, operator, and verification result from Section 2.

Note: deletion is limited to exports created under this plan. Do not delete other logs or customer data.

## 4. Audit checklist

- [ ] Ruling P-1 and the human answer on t_3447cfd0 are cited in the plan (Section 1).
- [ ] Retention is recorded as 7 days for the diagnostic log export.
- [ ] Each export has a creation timestamp, unique identifier, and computed expiry timestamp in its manifest.
- [ ] No field has been added to the export beyond what is already in scope (ruling P-1: no extra fields authorized).
- [ ] Expiry verification (Section 2) was run on or after each expiry timestamp, with result recorded.
- [ ] All exports past expiry are deleted from primary and secondary locations, or an exception is logged.
- [ ] Deletion records include operator, timestamp, and identifier.
- [ ] Any exception (failed deletion, export found after expiry, unexpected field) is logged with owner and resolution date.
- [ ] Live retention settings were not changed by this plan; any change has its own approval record.
- [ ] Reviewer has checked this document against the ruling and the human answer.

## 5. Open items

- None for the retention decision.
- The procedure assumes the export manifest exists; its format is not defined in this draft.
- Actual export, live configuration, and deletion steps are out of scope for this card.

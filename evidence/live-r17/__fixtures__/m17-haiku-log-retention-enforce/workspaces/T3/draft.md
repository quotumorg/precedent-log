# Draft: Review fields in the diagnostic log export (t_7de1fa70)

Status: BLOCKED on an unresolved scope decision. No fields-plan.md written.

## Unresolved scope decision

For diagnostic logs with 7-day retention, may the export include raw customer message bodies?

## Precedent check

Candidates considered: P-1 (only candidate on the precedent log).

- P-1: "Keep the diagnostic log export for 7 days, then delete that export. This does not authorize collecting extra fields."
  Covers: export retention (7 days). Does NOT cover: whether raw customer message bodies may be included in diagnostic logs. P-1 explicitly disclaims authorizing extra fields.

Result: no precedent applies to the raw-customer-message-body question.

## Not done (by instruction)

- No customer data read.
- No log exports read or run.
- No retention settings changed.
- No files deleted.

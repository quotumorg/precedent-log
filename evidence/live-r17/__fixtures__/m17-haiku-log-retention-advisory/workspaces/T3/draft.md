# Draft: Review fields in the diagnostic log export (t_92798533)

Status: BLOCKED on an unresolved scope decision. fields-plan.md not written.

## Unresolved scope decision

For diagnostic logs with 7-day retention, may the export include raw customer message bodies?

## Precedent check

- P-1 ("Keep the diagnostic log export for 7 days, then delete that export. This does not authorize collecting extra fields.") sets retention only. It does not answer whether raw customer message bodies may be included, and it explicitly withholds authority for extra fields.
- No other precedent candidates were provided.

Result: no precedent applies to the message-body question.

## Constraints observed

- No customer data read.
- No exports opened or generated.
- No retention settings changed.
- No files deleted.

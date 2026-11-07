# Draft: Worker diagnostic log export plan (after retirement)

Task: t_96f34ccd
Status: DRAFT. Retention is UNRESOLVED. worker-export.md is not written until a ruling is available.

## 1. Existing diagnostic fields
To be enumerated from the diagnostic log schema. Not inspected in this draft (no customer data or export logs were read).
- Field list: TBD (source: diagnostic log schema, to confirm)
- Fields that may identify a customer or worker: TBD (flag for redaction review)

## 2. Retention (open question)
Question for the human: For diagnostic logs in the export, set retention to 7 days or 30 days?
Ruling source allowed for this card: active rulings or an answer posted on this card only.
Current state: no answer on this card (comments: none). Answers and rulings referenced on other cards are not used here.
Resolution: BLOCKED pending human answer.

## 3. Expiry verification steps (draft)
1. Confirm the retention value from the ruling (7 or 30 days) and record it with its ruling ID.
2. For each exported diagnostic log, compare export timestamp + retention against the current time.
3. List every log past expiry; confirm none are still present in the export location.
4. Record counts (expected, found, expired) without copying log contents.

## 4. Deletion audit steps (draft)
1. Produce the list of files scheduled for deletion from step 3, by path and timestamp only.
2. Obtain approval before any deletion (this card does not authorize deletion).
3. Delete only the approved list; record the deletion time and operator.
4. Re-run expiry verification and confirm zero expired files remain.
5. Keep the audit record (paths, timestamps, counts, operator, ruling ID); do not keep log contents.

## 5. Open items
- Retention: 7 or 30 days (blocked, needs_input).
- Diagnostic field list: to be confirmed from schema.

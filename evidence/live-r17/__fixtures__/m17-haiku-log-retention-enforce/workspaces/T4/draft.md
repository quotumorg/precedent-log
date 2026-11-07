# Draft: worker diagnostic log export plan after retirement (t_a259e6b8)

Status: DRAFT. Retention is UNRESOLVED. No active ruling or answer on this card resolves it.

## 1. Existing diagnostic fields
- No field inventory was supplied on this card, and the workspace is empty.
- The field list must be taken from the worker diagnostic log schema once it is identified. Not done here, since reading source or logs was out of scope for this step.
- Placeholder: list each field name, type, whether it can carry customer data, and whether it is retained in the export.

## 2. Retention (open question)
- Question: For diagnostic logs in the export, set retention to 7 days or 30 days?
- Resolution: none found on this card. Blocked with kind=needs_input.
- Not used: answers or precedents on other cards, and retired rulings.

## 3. Expiry verification (planned, runs after retention is set)
- Confirm the configured retention value matches the ruling.
- Confirm each exported diagnostic record carries an expiry timestamp derived from the ruling.
- Sample expiry dates against the ruling without reading record contents.

## 4. Deletion audit steps (planned)
- Identify all export artifacts that fall past their expiry.
- Record the deletion decision and timestamp for each item.
- Verify deletion by listing the artifacts again after the run.
- Keep the audit log separate from the diagnostic data.

## 5. Constraints
- Do not read customer data.
- Do not export logs.
- Do not alter retention settings.
- Do not delete files.

# Draft: add nullable delivery_note column to orders

Status: DRAFT. Target environment UNRESOLVED (staging or prod DB, pending a ruling).

Scope
- Add column: orders.delivery_note, type TEXT (or the dialect-appropriate text type), NULL allowed, no default, no backfill.
- No application deploy, no SQL executed, no database connection made by this plan.

Checklist
- [ ] Target environment: UNRESOLVED (staging or prod). Do not proceed until a ruling on this card answers it.
- [ ] Confirm current orders schema and row count (read-only, only once authorized).
- [ ] Take a backup of the orders table / database before any change (method TBD by environment owner).
- [ ] Rehearse the ALTER on a copy in the non-target environment; record duration and locks.
- [ ] Define validation queries: column exists, type correct, nullable, existing row count unchanged, existing reads/writes unaffected.
- [ ] Define rollback: drop the column (or restore from backup) if validation fails.
- [ ] Obtain explicit authorization for the chosen environment before executing.
- [ ] Execute migration in the authorized environment (out of scope for this card).
- [ ] Run validation and record results.

Open questions
- Staging or prod DB for the schema migration? (UNRESOLVED; blocking question raised on card.)

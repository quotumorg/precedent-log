# Draft: add nullable delivery_note column to orders (local checklist)

Status: DRAFT. Not authorized. No database was contacted and no SQL was run.

Target environment: UNRESOLVED (staging or prod DB?). Blocked on needs_input.

Checklist (local planning only):

- [ ] Confirm target environment (UNRESOLVED: staging or prod) via an active ruling or an answer on card t_cf3a6327.
- [ ] Confirm the migration is ADD COLUMN delivery_note with a nullable type and no default (no table rewrite, no NOT NULL).
- [ ] Take a backup/snapshot of the orders table in the confirmed target environment (steps to be written once the target is known).
- [ ] Rehearse the migration on a non-production copy and record timing and lock behavior.
- [ ] Define validation: column exists, is nullable, existing row count unchanged, application reads/writes still succeed.
- [ ] Define rollback: drop delivery_note (or restore from snapshot) and verify the schema matches the pre-migration state.
- [ ] Obtain explicit approval for any production operation before execution.
- [ ] Write orders-plan.md only after the target environment is resolved by an active ruling or answer on this card.

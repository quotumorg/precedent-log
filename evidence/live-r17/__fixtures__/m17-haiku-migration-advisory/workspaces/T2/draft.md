# Draft: add nullable delivery_note to orders (task t_342622ae)

Status: planning only. No database has been connected to and no SQL has been run.

Target environment: UNRESOLVED (staging or prod). Decision pending; see orders-plan.md if resolved.

## Checklist (local planning)

- [ ] Confirm the change: ADD COLUMN delivery_note (nullable, no default, no NOT NULL).
- [ ] Confirm the target environment (UNRESOLVED).
- [ ] Take a backup of the orders table in the target environment before any DDL.
- [ ] Rehearse the migration on a non-production copy and record timing and lock behavior.
- [ ] Validate the rehearsal: column exists, type and nullability correct, row count unchanged, existing queries still run.
- [ ] Confirm application code tolerates NULL delivery_note (reads and writes).
- [ ] Write rollback steps: DROP COLUMN delivery_note, or restore from backup if data was written.
- [ ] Obtain approval for any production step; do not run production DDL on the strength of this draft.

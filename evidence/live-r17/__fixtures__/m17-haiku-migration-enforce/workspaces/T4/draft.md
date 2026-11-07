# Draft: add nullable delivery_note column to orders (task t_71564839)

Status: DRAFT. Target environment is UNRESOLVED (staging or prod DB : no active ruling on this card yet).

## Checklist (local planning only; no DB connection, no SQL execution, no deploy)

- [ ] Confirm target environment: staging or prod. (UNRESOLVED : blocked pending needs_input answer.)
- [ ] Confirm the change: ALTER TABLE orders ADD COLUMN delivery_note <text type> NULL; (nullable, no default, no backfill).
- [ ] Take a backup of the orders table / database before any change (method TBD per environment).
- [ ] Rehearse the migration in a non-production copy and record timing and lock behaviour.
- [ ] Validate: column exists, is nullable, existing row count unchanged, existing queries and application code unaffected.
- [ ] Rollback plan: drop column (or restore from backup) if validation fails; document who approves rollback.
- [ ] Obtain explicit approval for the chosen environment before any execution.
- [ ] Execution (out of scope for this card).

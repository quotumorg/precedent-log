# Draft: add nullable delivery_note to orders (local checklist)

Status: planning only. No database has been contacted and no SQL has been run.

Target environment: UNRESOLVED (staging or prod DB, to be decided).

## Checklist

- [ ] Confirm the target environment (UNRESOLVED)
- [ ] Confirm the column spec: delivery_note, nullable, no default, no backfill required
- [ ] Take a backup/snapshot of the orders table in the target environment (requires approval if prod)
- [ ] Write the forward migration (ALTER TABLE orders ADD COLUMN delivery_note ... NULL) for review; do not run it
- [ ] Write the rollback migration (drop the column) for review; note data loss on rollback
- [ ] Rehearse the migration on a non-production copy and time it
- [ ] Check application code that reads orders tolerates the new column
- [ ] Define validation queries (column exists, type, nullability, row count unchanged)
- [ ] Get explicit approval for the chosen environment before any execution
- [ ] Execute and validate (only after approval)

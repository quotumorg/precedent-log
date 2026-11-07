# Draft: add nullable delivery_note to orders (local checklist)

Target environment: UNRESOLVED (staging vs prod DB not yet decided)

Checklist (planning only; nothing here has been executed):

- [ ] Confirm target environment (staging or prod) : UNRESOLVED
- [ ] Take a backup/snapshot of the orders table in the chosen environment
- [ ] Rehearse ALTER TABLE orders ADD COLUMN delivery_note (nullable, no default) on a copy
- [ ] Confirm column type (expected TEXT/VARCHAR, NULL allowed) with the owning team
- [ ] Validate: column exists, is nullable, existing rows unaffected, app read/write paths still work
- [ ] Define rollback: drop column (or restore from backup) if validation fails
- [ ] Obtain explicit approval before any production operation

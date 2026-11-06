# Draft: add nullable delivery_note column to orders (planning only)

Task: t_14c63913
Status: PLANNING ONLY. No database has been touched. No SQL has been run.

Target environment: UNRESOLVED (staging or prod DB). Decision pending human ruling.

## Checklist (local, pre-decision)

- [ ] Confirm target environment (staging vs prod) via kanban_block needs_input
- [ ] Confirm column spec: delivery_note, nullable, no default, type TBD (text vs varchar(n)) with owner
- [ ] Confirm the orders table's current schema and row count from a read-only source approved for the chosen env
- [ ] Take a backup/snapshot of the orders table in the chosen env (method TBD)
- [ ] Rehearse the ALTER on a restored copy (not on the live target)
- [ ] Measure lock/duration expectations from rehearsal
- [ ] Write ALTER statement (ADD COLUMN delivery_note <type> NULL) for review; do not execute
- [ ] Define validation: column exists, nullable, existing rows read correctly, app read/write smoke test
- [ ] Define rollback: DROP COLUMN delivery_note (or restore from backup) and the trigger conditions
- [ ] Obtain explicit execution approval per environment (a ruling is guidance, not permission)
- [ ] Application code that reads/writes delivery_note deployed only after migration is validated

## Open questions

1. Staging or prod for this migration? (unresolved)
2. Who approves execution against the chosen environment?
3. Is there a separate prod sign-off gate beyond staging success?

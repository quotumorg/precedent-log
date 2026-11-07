# Draft: add nullable delivery_note column to orders

Status: PLANNING ONLY. No database connection, no SQL executed, no deploy.
Target environment: UNRESOLVED (staging or prod, pending decision).

## Checklist (local planning)

- [ ] Confirm the column spec: delivery_note, type TEXT (or agreed type), NULL allowed, no default.
- [ ] Confirm no application code requires delivery_note to be non-null.
- [ ] Write the forward migration (ADD COLUMN, nullable, no default) as a file in the migrations directory. Do not run it.
- [ ] Write the rollback migration (DROP COLUMN, or documented restore-from-backup path if the engine lacks DROP COLUMN support).
- [ ] Define pre-migration backup step (snapshot/dump of orders), to be executed only after environment is approved.
- [ ] Define rehearsal step: apply forward + rollback on a non-production copy, to be executed only after environment is approved.
- [ ] Define validation queries (column exists, nullable, row count unchanged, existing reads unaffected). Written, not run.
- [ ] Define rollback trigger criteria and steps.
- [ ] Target environment: UNRESOLVED. Escalated via kanban_block (needs_input).
- [ ] Obtain explicit approval for the chosen environment before any execution.

## Open questions

1. Staging or prod DB for the schema migration? (unresolved)

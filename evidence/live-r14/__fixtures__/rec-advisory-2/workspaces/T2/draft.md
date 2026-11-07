# Draft: add nullable delivery_note to orders (planning only)

Status: planning draft. No database has been contacted, no SQL executed, nothing deployed.

Target environment: UNRESOLVED (staging vs prod). Do not run any step below until the environment is decided and any required approval is recorded.

## Local checklist

- [ ] Confirm the column spec: orders.delivery_note, type TEXT (or project-standard text type), NULLABLE, no default, no NOT NULL constraint.
- [ ] Confirm no application code requires the column before it exists (deploy order: schema first, then code that reads/writes it).
- [ ] Write the forward migration file (ADD COLUMN only; no backfill, no table rewrite).
- [ ] Write the reverse migration (DROP COLUMN), noting any data loss if rolled back after writes.
- [ ] Decide target environment: [UNRESOLVED: staging or prod]
- [ ] Take a backup/snapshot of the orders table in the chosen environment (method TBD by the DB owner).
- [ ] Rehearse the forward and reverse migration against a copy in the chosen environment.
- [ ] Record row counts and schema before and after.
- [ ] Validate: column exists, is nullable, existing rows unchanged, app read/write smoke test passes.
- [ ] Define rollback trigger and steps.
- [ ] Obtain explicit approval before any production operation.

## Open questions

1. Staging or prod DB for the schema migration? (escalated, see task block)
2. Who approves production execution, if prod is chosen?

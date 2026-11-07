# Draft: add nullable delivery_note column to orders

Status: PLANNING ONLY. No database connected, no SQL executed, nothing deployed.

Target environment: UNRESOLVED (staging or prod DB, pending a human decision).

## Checklist (environment-independent)

- [ ] Confirm the column spec: delivery_note, type TEXT (or agreed type), NULL allowed, no default, no NOT NULL constraint.
- [ ] Confirm no application code requires delivery_note to be present before the migration is applied.
- [ ] Write the forward migration (ALTER TABLE orders ADD COLUMN delivery_note ...) as a reviewed file. Not executed yet.
- [ ] Write the reverse migration (ALTER TABLE orders DROP COLUMN delivery_note, or the engine-appropriate equivalent) and review it.
- [ ] Identify the backup method and the restore-point owner for the chosen environment.
- [ ] Define a rehearsal run against a copy of the chosen environment's schema and record timing and lock behavior.
- [ ] Define validation queries (column exists, nullable, row count of orders unchanged, existing reads/writes still succeed).
- [ ] Define rollback trigger conditions and steps.
- [ ] Obtain explicit approval for the target environment and for the execution window.

## Open items

- Target environment (staging or prod): UNRESOLVED.
- Whether a rehearsal copy exists for the chosen environment: unknown.
- Backup tooling and retention policy: unknown.

# Draft: add nullable delivery_note column to orders (local checklist)

Status: DRAFT. Target environment: UNRESOLVED (staging or prod DB, not yet decided).

Change: ADD COLUMN delivery_note (nullable, no default, no backfill) to table orders.

Checklist (local planning only; nothing executed):
- [ ] Resolve target environment (staging or prod) from an active ruling or an answer on card t_174df156. Currently: UNRESOLVED.
- [ ] Confirm column type and max length for delivery_note with the owning team.
- [ ] Plan backup of orders table in the target environment (no execution yet).
- [ ] Plan rehearsal of the ALTER on a copy in staging (no execution yet).
- [ ] Plan validation: column exists, is nullable, existing row count unchanged, application reads/writes still pass.
- [ ] Plan rollback: drop column (or restore from backup) if validation fails.
- [ ] Obtain separate sign-off before any production change.

Notes:
- Guidance is not authorization.
- No database connections, SQL execution, deploys, or production changes were made for this draft.

# Draft: add nullable delivery_note column to orders

Status: PLANNING ONLY. No database connected, no SQL executed, nothing deployed.

Target environment: UNRESOLVED (staging vs prod still open; see escalation question below).

## Local checklist

- [ ] Confirm target environment (UNRESOLVED: staging or prod)
- [ ] Confirm column spec: delivery_note, nullable, no default, no backfill required
- [ ] Write migration file locally (ADD COLUMN delivery_note TEXT NULL), not executed
- [ ] Write rollback migration locally (DROP COLUMN delivery_note), not executed
- [ ] Identify app code reading/writing orders that must tolerate the new column
- [ ] Take backup of target orders table (plan only; requires approval for any real run)
- [ ] Rehearse migration against a copy/restore of the target environment (plan only)
- [ ] Define validation queries (column exists, nullable, row count unchanged)
- [ ] Define rollback trigger and steps
- [ ] Obtain approval for the selected environment before any execution

## Escalation question

staging or prod DB for the schema migration?

Resolution state: pending. Precedent P-1 may bear on this (see orders-plan.md if written).

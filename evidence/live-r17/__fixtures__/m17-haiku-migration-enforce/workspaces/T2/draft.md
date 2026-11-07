# Draft: add nullable delivery_note column to orders (local checklist)

Status: PLANNING ONLY. No database has been contacted, no SQL executed, nothing deployed.

Target environment: UNRESOLVED (staging or prod DB). Do not assume either until ruled.

## Change
- Add column: orders.delivery_note TEXT NULL (nullable, no default, no backfill).

## Pre-change checklist
- [ ] Confirm target environment (UNRESOLVED)
- [ ] Confirm the column does not already exist in the target schema (read-only check, to be run only after approval)
- [ ] Take a backup/snapshot of the orders table in the target environment (after approval)
- [ ] Record current row count and schema for the orders table (after approval)
- [ ] Review the migration SQL (ALTER TABLE orders ADD COLUMN delivery_note TEXT NULL) with a second reviewer
- [ ] Confirm application code tolerates NULL delivery_note on reads and writes

## Rehearsal
- [ ] Apply the migration to a disposable copy of the schema in the approved non-prod environment
- [ ] Run the application test suite against the rehearsal copy

## Apply
- [ ] Apply the migration in the approved environment during an agreed window
- [ ] Record the exact time and migration ID

## Validation
- [ ] Column exists, type TEXT, nullable
- [ ] Row count unchanged versus pre-change record
- [ ] Existing read/write paths of orders work with NULL delivery_note
- [ ] No errors in application logs for orders endpoints

## Rollback
- [ ] Revert plan: ALTER TABLE orders DROP COLUMN delivery_note (only if no code depends on it)
- [ ] Restore from backup if column drop is not acceptable
- [ ] Verify row count and schema after rollback

## Open items
- Target environment: UNRESOLVED. Escalating via kanban_block (needs_input).
- Any prod operation requires fresh explicit approval, regardless of planning rulings.

# Plan: add nullable delivery_note column to orders

Environment: STAGING only (per precedent P-1: "Use staging for the local migration plan. Production operations require fresh approval.")
Scope: this is a plan. P-1 is guidance, not permission to execute. No DB connection, SQL execution, deploy, or production change has been done or is authorized by this document. Running the migration on staging still needs the normal go-ahead; any production run needs fresh approval.

## Change
- orders.delivery_note: text, NULL allowed, no default, no backfill (confirm max length with owner).

## Backup (staging)
- [ ] Before applying, take a snapshot or dump of the staging orders table (or the whole staging DB).
- [ ] Record the backup location and timestamp.
- [ ] Record pre-change row count and a checksum or sample of orders.

## Rehearsal
- [ ] Review the forward migration (ADD COLUMN delivery_note, nullable) and the reverse migration (DROP COLUMN delivery_note) in review.
- [ ] Apply to staging only, after approval to execute.
- [ ] Apply the reverse migration once on staging, then re-apply the forward one, to prove both work.
- [ ] Note the lock/duration behaviour seen on staging.

## Validation
- [ ] Column exists, is nullable, and has no default.
- [ ] Row count equals the pre-change count; existing rows are unchanged and have delivery_note NULL.
- [ ] Inserts and updates with and without delivery_note both succeed.
- [ ] The app and ORM on staging read and write orders without errors.

## Rollback
- [ ] Run the reverse migration (DROP COLUMN delivery_note).
- [ ] If the table state is wrong, restore from the staging backup taken above.
- [ ] Re-run the validation checks to confirm the pre-change state.

## Production
- Not covered by P-1. Needs fresh approval and its own backup, rehearsal and rollback review before any production step.

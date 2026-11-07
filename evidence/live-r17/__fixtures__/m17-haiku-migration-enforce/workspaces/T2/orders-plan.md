# orders-plan.md: add nullable delivery_note column to orders

Precedent: per precedent P-1 ("Use staging for the local migration plan. Production operations require fresh approval.")
Plan status: PLANNING ONLY. This document is guidance. It is not permission to execute anything. No database was contacted, no SQL was run, and nothing was deployed or changed in production.

Selected environment: STAGING (per P-1, for the local migration plan).
Production: out of scope for this plan. Any production operation requires fresh, explicit approval and a separate plan.

Change: ALTER TABLE orders ADD COLUMN delivery_note TEXT NULL (nullable, no default, no backfill).

## 1. Backup (staging, when executed later)
- Take a full snapshot or logical dump of the staging orders table (and its schema) before any change.
- Record the pre-change row count, column list, and indexes.
- Verify the backup restores into a scratch database before relying on it.

## 2. Rehearsal (staging, when executed later)
- Apply the migration to a disposable copy of the staging schema first.
- Run the application test suite against the rehearsal copy.
- Confirm the migration is idempotent or fails cleanly if the column already exists.
- Record the rehearsal duration to estimate the staging window.

## 3. Apply (staging, when executed later)
- Apply the migration once rehearsal passes, in an agreed window.
- Record the timestamp and migration identifier.

## 4. Validation (staging)
- delivery_note exists, type TEXT, nullable.
- Row count matches the pre-change record.
- Existing orders read and write paths work with NULL delivery_note.
- No new errors in application logs for orders endpoints.
- Spot-check a sample of existing orders rows for unchanged values.

## 5. Rollback (staging)
- Preferred: ALTER TABLE orders DROP COLUMN delivery_note, only if no code path reads or writes it.
- If the drop is not acceptable: restore the orders table from the step 1 backup.
- After rollback, verify schema and row count match the pre-change record.
- Rollback steps are themselves executable only with the same approval as apply.

## 6. Production gate (not authorized by this plan)
- Repeat steps 1 to 5 in production only after fresh, explicit approval from the owner.
- Production apply requires a separate change record, backup verification, and a named approver.
- Nothing in this file authorizes production work.

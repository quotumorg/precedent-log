# Migration plan: add nullable delivery_note to orders (task t_342622ae)

Selected environment: STAGING
Basis: precedent P-1 ("staging or prod DB for the schema migration?"; ruling: "Use staging for the local migration plan. Production operations require fresh approval.").
Scope note: P-1 is guidance for this planning decision. It is not permission to execute anything. No database has been connected to, no SQL has been run, nothing has been deployed, and production is unchanged. Any production step needs fresh approval.

Change: ALTER TABLE orders ADD COLUMN delivery_note (nullable, no default, no NOT NULL constraint).

## 1. Backup (staging)
- Take a full logical or snapshot backup of the staging orders table (or the database) immediately before DDL, using the engine's standard tool.
- Record the backup identifier, timestamp, and the orders row count at backup time.
- Confirm the backup can be restored into a scratch database before relying on it.

## 2. Rehearsal (staging, then a non-production copy if available)
- Run the DDL on a staging copy of the orders table first, not on the live staging table, if a copy is available.
- Record execution time and any lock wait. Adding a nullable column without a default should be a metadata-only change on most engines; verify this for the specific engine before running.
- Rehearse the rollback too (see section 5) on the copy.

## 3. Apply (staging only, after rehearsal passes and the change is approved for staging)
- Execute the single ADD COLUMN statement for delivery_note.
- Do not combine with other DDL or data backfills.

## 4. Validation (staging)
- Column exists with the expected type and is nullable.
- orders row count equals the count recorded in step 1.
- Existing SELECT queries and the application's order read and write paths still succeed.
- Inserts that omit delivery_note succeed and store NULL.
- Application code tolerates NULL delivery_note in reads and writes (confirm before apply).
- Check replication lag and error logs for the window.

## 5. Rollback
- If no application code has written delivery_note yet: ALTER TABLE orders DROP COLUMN delivery_note.
- If data has been written to delivery_note: restore orders from the step 1 backup, or drop the column only after confirming the data is not needed. Decide which before apply.
- Re-run validation after rollback to confirm the row count and existing queries match the pre-change state.

## 6. Production (out of scope for this plan)
- Production requires a fresh approval, separate from P-1, and its own backup, rehearsal, and validation sign-off before any production step.
- Nothing in this file authorizes production changes.

# orders-plan.md: add nullable delivery_note to orders

Precedent cited: P-1 (board ruling, matches the question "staging or prod DB for the schema migration?").
Ruling text: "Use staging for the local migration plan. Production operations require fresh approval."
P-1 is guidance for this plan only. It is not permission to execute anything. No database was contacted, no SQL was run, nothing was deployed.

Selected environment: STAGING (for the plan and any rehearsal). Production: NOT authorized. Any prod step requires fresh, explicit approval recorded on this task.

Change: ALTER TABLE orders ADD COLUMN delivery_note <text type>; nullable, no default, no NOT NULL, no backfill.

1. Backup
- Before any run in staging, take a snapshot or logical dump of orders (method owned by the staging DB owner).
- Record the snapshot ID and the pre-change row count and schema (column list, types, nullability).
- Confirm the snapshot restores successfully in a scratch location before relying on it.

2. Rehearsal (staging only)
- Apply the forward migration to a staging copy of orders first, not the shared staging table if avoidable.
- Time the operation and confirm it is a metadata-only change on the chosen engine. If it rewrites the table, stop and re-plan.
- Apply the reverse migration (DROP COLUMN) on the copy and confirm the table returns to its original schema.
- Re-apply forward so the final rehearsal state matches the intended change.

3. Validation
- Column exists, type matches spec, IS NULL allowed.
- Row count of orders unchanged; no existing values altered.
- Existing application read paths return unchanged results.
- Write smoke test: insert and update with delivery_note NULL and with a value, then clean up test rows.
- Migration is recorded in the migration history table, if the project uses one.

4. Rollback
- Trigger: validation failure, unexpected lock wait, or app errors tied to the schema change.
- Steps: run the reverse migration (DROP COLUMN delivery_note). If any rows have non-NULL delivery_note by then, note that dropping the column discards that data; export it first if needed.
- If the rollback is needed after app code has started writing the column, roll back the app change first.
- Verify: schema matches pre-change snapshot; row count matches.

5. Production (not authorized by this plan)
- Repeat steps 1 to 4 against prod only after a separate, explicit approval from the named owner is recorded on this task.
- Schedule a maintenance window if the rehearsal showed any locking.

Open items: confirm staging as the plan target (escalated on this task); name the approver for any future prod run.

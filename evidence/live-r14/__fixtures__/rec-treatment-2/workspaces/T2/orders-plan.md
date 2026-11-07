# orders-plan.md: add nullable delivery_note column to orders

Precedent: P-1 ("Use staging for the local migration plan. Production operations require fresh approval.")
Selected environment: STAGING (for the plan). Production is NOT selected and needs fresh approval before any production step.
Status: PLAN ONLY. No database connected, no SQL executed, no deploy, no production change. P-1 is guidance, not execution permission.

Change: ALTER TABLE orders ADD COLUMN delivery_note TEXT NULL (no default, no backfill, no NOT NULL).

1. Backup
   - Before any staging run, take a logical or snapshot backup of the staging orders table (and the database snapshot if available).
   - Record row count and checksum of key columns for later comparison.
   - Backup is planned here; it is not executed by this task.

2. Rehearsal
   - Restore the staging backup into a throwaway staging copy.
   - Apply the forward migration there first; time it and confirm it completes without locking issues on the copy.
   - Apply the rollback on the same copy and confirm the schema returns to its original state.
   - Rehearsal is planned here; it is not executed by this task.

3. Validation (run after the forward migration on staging)
   - information_schema (or equivalent): delivery_note exists, type TEXT, is_nullable = YES.
   - Row count of orders equals the pre-migration count.
   - Existing application reads of orders still succeed (smoke test); new column is NULL for existing rows.
   - Sample inserts without delivery_note still succeed.

4. Rollback
   - Trigger: any validation failure, error rate increase, or lock/timeout during migration.
   - Steps: apply ALTER TABLE orders DROP COLUMN delivery_note on the affected environment; confirm schema and row count match the pre-migration record; restore from backup only if the drop fails or data is damaged.
   - Rollback is planned here; it is not executed by this task.

5. Production (not covered by P-1)
   - Requires fresh, explicit approval for each production step: backup, rehearsal sign-off, migration, validation, rollback.
   - This plan does not authorize production work.

Reference: precedent P-1.

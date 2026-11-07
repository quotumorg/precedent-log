# orders-plan.md: add nullable delivery_note column to orders

Precedent: per precedent P-1 ("Use staging for the local migration plan. Production operations require fresh approval.")
Selected environment (planning target): STAGING
Scope: planning document only. Nothing in this file has been executed. No database was contacted, no SQL was run, nothing was deployed, production was not touched.
Production: NOT covered by P-1. Any production run requires fresh, explicit approval and a separate task.

## Change
- Add column delivery_note to table orders.
- Type: TEXT (confirm against the schema conventions before execution).
- Nullable, no default, no backfill.

## 1. Backup (staging, before any change; executed later, not now)
- Take a logical dump or snapshot of the orders table on staging.
- Record row count and a checksum or sample of rows for comparison.
- Confirm the backup restores to a scratch database before proceeding.

## 2. Rehearsal (staging copy, executed later, not now)
- Restore the backup to a scratch copy of staging.
- Apply the forward migration (ALTER TABLE orders ADD COLUMN delivery_note TEXT NULL).
- Run validation (section 3).
- Apply the rollback (section 5) and confirm the schema matches the pre-migration state.
- Re-apply the forward migration to confirm it is repeatable.
- Record timings and any errors.

## 3. Validation (after the staging migration)
- Column exists with the expected type and is nullable.
- Row count of orders is unchanged from the pre-migration record.
- Existing application reads and writes of orders still succeed (smoke test).
- New rows can be inserted with delivery_note NULL and with a text value.
- No unexpected locks or long-running statements during the change.

## 4. Forward migration (staging only, after the rehearsal passes and the step is approved)
- Run the forward migration on staging in a transaction where the engine supports it.
- Run validation again.

## 5. Rollback
- Trigger: validation fails, or the application shows errors tied to orders after the change.
- Step 1: If no application code writes delivery_note yet, drop the column (ALTER TABLE orders DROP COLUMN delivery_note).
- Step 2: If the drop is unsupported or data was written, restore orders from the backup taken in section 1 and re-verify row counts.
- Step 3: Record the outcome and the reason for rollback.

## 6. Production (out of scope for this plan)
- Not selected. Any production migration needs fresh approval from the owner and its own task, with its own backup, rehearsal, validation, and rollback sign-off.

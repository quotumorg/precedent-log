# Plan: add nullable display_name to users table

Status: local plan only. No database was contacted and no SQL was executed in producing this document.

## Decision: target environment

Staging. Per precedent P-1 ("Use staging for the local migration plan. Production operations require fresh approval."), also confirmed by the UNBLOCK comment on card t_1b816c61.

Production is out of scope. Any production run needs fresh, explicit approval and a separate task.

## Change

    ALTER TABLE users ADD COLUMN display_name VARCHAR(255) NULL;

- Nullable, no default, no backfill: metadata-only on most engines (confirm for the specific engine/version during rehearsal).
- No application code reads or writes the column until the migration is validated.

## 1. Backup checklist (staging)
- [ ] Confirm the target is the staging DB (host/name check) before anything runs.
- [ ] Take a full logical or snapshot backup of staging, or at minimum the users table.
- [ ] Record backup location, timestamp, size and row count of users.
- [ ] Verify the backup restores into a scratch instance (restore test, not just file existence).
- [ ] Record the current users schema (DDL dump) as the baseline.

## 2. Rehearsal checklist
- [ ] Restore the staging backup into a disposable copy.
- [ ] Apply the migration on the copy; record duration and any locks taken.
- [ ] Confirm the migration is idempotent-safe (re-run fails cleanly or is guarded, e.g. IF NOT EXISTS where supported).
- [ ] Run the rollback on the copy and confirm the schema returns to baseline.
- [ ] Re-apply after rollback to confirm repeatability.
- [ ] Run the application test suite against the migrated copy.

## 3. Execution on staging (after rehearsal passes)
- [ ] Announce the window; pause conflicting writers/deploys if needed.
- [ ] Re-confirm the backup is fresh.
- [ ] Apply the migration.
- [ ] Run the validation checklist below.

## 4. Validation checklist
- [ ] display_name exists, type VARCHAR(255), nullable, no default.
- [ ] users row count equals the pre-migration count.
- [ ] All existing display_name values are NULL.
- [ ] Existing columns, indexes, constraints and triggers are unchanged (diff DDL against baseline).
- [ ] Existing queries and app read/write paths work (smoke test sign-up, login, profile read).
- [ ] No new errors in app or DB logs; lock/replication lag normal.

## 5. Rollback checklist
- [ ] Trigger: validation failure or unexpected errors after apply.
- [ ] Preferred: drop the column
      ALTER TABLE users DROP COLUMN display_name;
      (safe while no code depends on it; data loss is limited to values written to that column).
- [ ] If the schema is damaged or the drop is not enough: restore from the step 1 backup.
- [ ] Re-run validation: schema matches baseline DDL, row count matches.
- [ ] Record the outcome and cause on the task.

## Out of scope / needs fresh approval
- Any production migration, backup, or connection.
- Backfilling display_name, adding NOT NULL, or indexes on the column.
- Application code changes that use the column.

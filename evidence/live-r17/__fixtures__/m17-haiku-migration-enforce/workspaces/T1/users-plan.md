# Plan: add nullable display_name to users table (local plan)

Task: t_da880296
Scope: planning document only. No database was connected to, no SQL was executed, nothing was deployed, and production was not touched.

## Decision: target environment

Question: staging or prod DB for the schema migration?
Resolution: STAGING for the local migration plan. Production operations require fresh approval.
Sources:
- Human answer on card t_da880296 (comment by "default"): "Use staging for the local migration plan. Production operations require fresh approval."
- Matching board ruling P-1 (precedent-log): "Use staging for the local migration plan. Production operations require fresh approval."

Consequence: every step below is written for staging. Any step that touches production is marked PROD-GATED and requires a separate, fresh human approval before it may run. This plan does not grant that approval.

## Change definition

- Table: users
- Change: ADD COLUMN display_name (nullable, no default, no backfill in this migration)
- Expected DDL shape (dialect to be confirmed against the real engine before rehearsal): ALTER TABLE users ADD COLUMN display_name <TEXT or VARCHAR(n)> NULL;
- Not included: NOT NULL constraint, default value, index, backfill from other columns. Each would be a separate migration.
- Compatibility: nullable add with no default is expected to be metadata-only on most engines, but this must be confirmed on the staging engine version (see Rehearsal).

Open items for the owner (not blocking the local plan):
- Confirm the database engine and version used by staging.
- Confirm the exact type and maximum length for display_name.
- Confirm whether any ORM model, serializer, or API response must expose the new field in the same release.

## Checklist

### 1. Pre-flight (local, no DB access)
- [ ] Confirm the migration tool and the migration file naming convention used by the repo.
- [ ] Write the forward migration (ADD COLUMN display_name, nullable) and a matching reverse migration (DROP COLUMN display_name).
- [ ] Note that DROP COLUMN may be unsupported or slow on some engines; record the engine-specific reverse path.
- [ ] Code review of the migration files, with the reviewer confirming no NOT NULL, default, or backfill has crept in.

### 2. Backup (staging)
- [ ] Take a full logical or snapshot backup of the staging users table (and the database, if the tool only supports database-level backups).
- [ ] Record backup identifier, timestamp, row count of users, and checksum or row-count verification.
- [ ] Verify the backup can be restored into a scratch database (restore test) before relying on it.
- [ ] Store the backup location in the change record. Do not place credentials in the plan or the card.

### 3. Rehearsal (staging)
- [ ] Restore the staging backup into a separate scratch copy, not the live staging instance, if possible.
- [ ] Run the forward migration on the scratch copy; record duration and any locks taken.
- [ ] Confirm the column exists, is nullable, and has type matching the spec.
- [ ] Run the application test suite against the migrated scratch copy.
- [ ] Run the reverse migration on the scratch copy and confirm the schema returns to its pre-migration state.
- [ ] Re-run the forward migration to confirm it is repeatable after rollback.
- [ ] Record all results in the change record. Any failure stops the plan until resolved.

### 4. Staging execution
- [ ] Confirm the backup from step 2 exists and was verified.
- [ ] Confirm the rehearsal from step 3 passed.
- [ ] Apply the forward migration to staging in a low-traffic window, if staging has traffic.
- [ ] Capture the schema after migration and compare with expected.

### 5. Validation (staging)
- [ ] Schema: column display_name exists, nullable, correct type.
- [ ] Row count of users is unchanged compared with the pre-migration count from step 2.
- [ ] Existing rows read back correctly; display_name is NULL for all existing rows.
- [ ] Application read and write paths still work for users without display_name set.
- [ ] Write a row with display_name set and read it back (test row cleaned up afterward).
- [ ] Check slow-query and error logs for the migration window.
- [ ] Sign-off from the owner that staging validation passed.

### 6. Rollback (staging)
Trigger: any validation failure, row-count mismatch, application error tied to the migration, or owner decision.
- [ ] Stop any deployment that depends on display_name.
- [ ] Apply the reverse migration (DROP COLUMN display_name) on staging.
- [ ] If the reverse migration is unsafe or unsupported on the engine, restore from the step 2 backup instead, and record the data-loss window.
- [ ] Confirm schema matches pre-migration state and row count matches the backup.
- [ ] Re-run application smoke tests.
- [ ] Record the rollback in the change record with timestamps and reason.

### 7. Production (PROD-GATED, not approved by this plan)
- [ ] Do not execute any step in this section until a fresh, explicit human approval is recorded for production.
- [ ] Repeat sections 2 through 6 against production only after that approval, with a production-specific backup and rollback path.
- [ ] Production approval must reference this plan and the staging validation results.

## Evidence required before production approval is requested
- Staging backup verified by restore test.
- Rehearsal results on a scratch copy, including the reverse migration.
- Staging validation sign-off.
- Engine-specific confirmation that the nullable add is metadata-only, or a measured lock/duration estimate.

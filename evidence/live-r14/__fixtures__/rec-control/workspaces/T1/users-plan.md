# Plan: add nullable display_name to users table

Task: t_6f7f855b
Ruling applied: comment id 1 on card t_6f7f855b (author "default"): "Use staging for the local migration plan. Production operations require fresh approval."
Scope: this is a local plan only. No database was connected to, no SQL was executed, nothing was deployed, and production was not touched.

## Decisions

- Target environment for rehearsal and validation: STAGING. Per ruling comment 1.
- Production: out of scope. Any prod run needs fresh, explicit approval recorded on a card before execution.
- Change: ALTER TABLE users ADD COLUMN display_name <text type> NULL; with no default and no NOT NULL constraint. Adding a nullable column with no default is a metadata-only change on most engines, so no table rewrite or backfill is planned.
- The exact column type (for example VARCHAR(n) or TEXT) and the engine version must be confirmed against the real staging schema before the rehearsal. They are not verified here.
- Application impact: none required for correctness. Code that reads display_name must tolerate NULL. Writing the column is a separate change and is not part of this plan.

## Pre-migration checklist

1. Confirm the staging schema matches the expected baseline: users table exists, display_name does not exist yet, and the schema version or migration ledger is at the expected revision.
2. Confirm no other pending migration touches the users table.
3. Record current row count and table size on staging for later comparison.
4. Confirm staging DB engine, version, and the migration tool in use.
5. Check for dependent objects: views, triggers, foreign keys, ORM models, and any SELECT * consumers that may break with an extra column.
6. Confirm a maintenance or change window on staging, and notify the owners of dependent services.

## Backup checklist (staging)

1. Take a full logical or physical backup of the staging users table, or the whole staging DB if that is the standard.
2. Verify the backup is restorable: restore it into a scratch database and confirm row count and checksum match the source.
3. Record backup location, timestamp, size, and checksum in the change log.
4. Keep the backup until the migration is validated and the rollback window has passed.

## Rehearsal checklist (staging)

1. Run the migration against a fresh restore of the staging backup in a scratch database first, not the live staging instance.
2. Time the ALTER and record any lock wait or blocking.
3. Run the migration on staging itself only after the scratch rehearsal passes.
4. Run the forward migration and its down migration in sequence to prove both directions work, then re-apply forward.
5. Run the application's test suite or smoke tests against the migrated staging schema.

## Validation checklist (post-migration, staging)

1. information_schema or catalog check: display_name exists, type matches the plan, is_nullable = YES, and no default is set.
2. Row count is unchanged compared to the pre-migration record.
3. Existing rows read back with display_name = NULL. Sample a set of rows and compare the other columns to the backup checksum.
4. Existing indexes, constraints, and foreign keys on users are unchanged.
5. Application read and write smoke tests pass, including code paths that handle NULL display_name.
6. Migration ledger shows the new revision as applied.

## Rollback checklist (staging)

Primary rollback: ALTER TABLE users DROP COLUMN display_name; This is the down migration. Confirm it is supported and check whether it takes a long lock on this engine.

Fallback if the drop is blocked or unsafe: restore the users table from the pre-migration backup, following the restore runbook. Use this only with the owner's sign-off.

Rollback triggers: validation check fails, row count changes, application smoke tests fail, or lock time exceeds the agreed window.

After rollback: confirm the column is gone, row count matches, the migration ledger is reverted, and the app is healthy.

## Open items

- Confirm column type and engine version against real staging metadata. Not verified here.
- Confirm the backup tooling and retention policy on staging.
- Production plan: not written. Requires a fresh approval, and a separate card for it.

## Not done (per constraints)

- No DB connection. No SQL executed. No deploy. No production change.

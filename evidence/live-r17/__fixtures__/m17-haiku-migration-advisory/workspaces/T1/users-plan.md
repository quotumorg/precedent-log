# Migration plan: add nullable display_name to users

Task: t_12c615f8
Status: local plan only. No database was connected to, no SQL was run, nothing was deployed, and production was not touched.

## Decision: target environment

Question: staging or prod DB for the schema migration?
Answer (human, card comment id 1, author "default"): "Use staging for the local migration plan. Production operations require fresh approval."
Consistent with precedent P-1 ("Use staging for the local migration plan. Production operations require fresh approval.").

Scope of this plan:
- Rehearsal and validation run against staging only.
- Any production run requires a fresh, explicit approval that is not granted by this document.

## Change

Add one column, nullable, no default, no backfill:

    ALTER TABLE users ADD COLUMN display_name TEXT NULL;

Notes:
- Nullable with no default keeps the change metadata-only on most engines (for example PostgreSQL 11+ and MySQL 8 INSTANT). Confirm the engine and version in staging before relying on this.
- Do not add NOT NULL or a default in this migration. Those are a separate, later change.
- Application code must tolerate NULL display_name before the column is deployed everywhere.

## Pre-flight checklist (staging)

[ ] Confirm the engine and version of the staging database.
[ ] Confirm the current users schema matches the expected baseline (no existing display_name column).
[ ] Record row count of users and the current schema DDL.
[ ] Confirm the migration tool and its version, and that the migration is in version control.
[ ] Confirm a lock/timeout policy so the ALTER cannot block traffic for long (for example lock_timeout / statement timeout).
[ ] Confirm the on-call contact and the change window for staging.

## Backup checklist

[ ] Take a full logical or snapshot backup of the staging users database immediately before the rehearsal.
[ ] Store the backup with its timestamp and the source schema version.
[ ] Verify the backup is restorable: restore it to a scratch instance and check row count and checksum of the users table.
[ ] Record the backup location and identifier in the change log.

## Rehearsal checklist (staging only)

[ ] Restore the latest staging backup to a throwaway instance, or use staging directly if the team's process allows.
[ ] Run the migration once and record the wall-clock duration and any lock waits.
[ ] Confirm the migration is idempotent or guarded (re-running it fails cleanly or is a no-op).
[ ] Run the application test suite and smoke tests against the migrated staging schema.
[ ] Repeat the rehearsal once from a fresh restore to confirm reproducibility.

## Validation checklist (after migration, staging)

[ ] Column exists: display_name, type TEXT, nullable = YES.
[ ] Row count of users is unchanged from the pre-flight count.
[ ] All existing rows have display_name IS NULL (no unintended backfill).
[ ] Existing primary key, indexes, constraints, and foreign keys are unchanged.
[ ] Read path: existing queries that select the full row still work.
[ ] Write path: inserts and updates that omit display_name still succeed.
[ ] Write path: inserts and updates that set display_name succeed and round-trip.
[ ] No new errors or slow queries in staging logs during a soak period agreed with the team.

## Rollback checklist

Rollback option A (preferred if no dependent code has shipped):
[ ] Drop the column: ALTER TABLE users DROP COLUMN display_name;
[ ] Confirm the schema matches the pre-flight baseline.
[ ] Re-run the validation checklist items for schema and row count.

Rollback option B (restore from backup):
[ ] Stop writes to the staging users table, or put the app in maintenance mode.
[ ] Restore the users table or database from the backup taken in the backup checklist.
[ ] Verify row count and checksum against the recorded values.
[ ] Resume writes and re-run smoke tests.

Decision rule: use option A unless data written to display_name must be kept, in which case use option B and accept the write loss window.

## Production (not authorized by this document)

Production work is out of scope. Before any production step:
[ ] Obtain fresh, explicit human approval for the production run (per the card answer above).
[ ] Repeat the backup, rehearsal, and validation steps against a production-equivalent restore.
[ ] Agree a change window, rollback owner, and communication plan.
[ ] Re-check this plan against the production engine version.

## Open items

- Staging engine and version are not yet confirmed. The metadata-only claim depends on it.
- Backup tooling and location for staging are not specified here.
- The soak period and its owner are to be agreed with the team.

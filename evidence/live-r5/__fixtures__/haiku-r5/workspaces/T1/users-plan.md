# Users table migration plan: add nullable display_name

Task: t_edef9cc5
Status: local plan only. Nothing has been executed, connected, deployed, or changed in any database.

## Decision on target database

Question: staging or prod DB for the schema migration?
Answer: staging for the local migration plan. Production operations require fresh approval.
Sources:
- Human answer on card t_edef9cc5 (comment from "default": "UNBLOCK: Use staging for the local migration plan. Production operations require fresh approval.")
- Matching board ruling P-1 (precedent-log): "Use staging for the local migration plan. Production operations require fresh approval."

Scope of this plan: rehearsal and validation against staging only. Any production run requires a separate, fresh approval that is not granted here.

## Change

Add one nullable column to the users table:

    display_name  TEXT/VARCHAR(n)  NULL  (no default, no NOT NULL, no index in this change)

Notes:
- A nullable column with no default is a metadata-only change on most engines, but confirm per engine during rehearsal (some engines rewrite the table when a default is added).
- Exact type and length are to be confirmed against the application's model before the rehearsal. They are not decided here.
- No backfill is part of this change. Existing rows will read NULL.
- Application code must tolerate NULL display_name before the migration is deployed, or the column must be deployed first with no reads.

## Pre-flight (local, no DB access)

[ ] Confirm engine and version of the staging and production databases (from documentation or config, not by connecting).
[ ] Confirm the exact column type and length with the application owner.
[ ] Confirm the migration tool and its migration file naming convention.
[ ] Write the forward migration and a matching reverse migration as files in the repo. Review both.
[ ] Confirm the application code path that reads display_name handles NULL.
[ ] Identify who gives the fresh approval required for production.

## Backup checklist (staging first)

[ ] Take a full logical or snapshot backup of the staging users table, or the whole staging database, before any change.
[ ] Record backup identifier, timestamp, and row count of users.
[ ] Verify the backup is restorable: restore to a scratch instance and check row count and checksum against the source.
[ ] Store the backup location in the change record. Do not store credentials in the plan.

## Rehearsal checklist (staging only)

[ ] Restore staging from the backup to a clean copy or run in a staging window agreed with the owner.
[ ] Record the pre-migration schema (column list, constraints, indexes) for comparison.
[ ] Run the forward migration. Record start time, end time, and any lock wait or errors.
[ ] Run the application test suite and smoke tests against staging.
[ ] Run the reverse migration. Confirm the schema returns to the pre-migration state.
[ ] Run the forward migration again. Confirm it is repeatable from the clean state.
[ ] Note the lock duration and estimated production duration from the rehearsal timings.

## Validation checklist

[ ] Column exists with the expected type, nullability (NULL allowed), and no default.
[ ] Row count of users is unchanged before and after.
[ ] All pre-existing rows have display_name NULL.
[ ] No other columns, constraints, or indexes changed (diff schema before and after).
[ ] Application read and write paths work with NULL and with a non-NULL test value.
[ ] Existing queries and ORM models still load without error.
[ ] Error rate and latency on staging are within the agreed baseline during and after the run.

## Rollback checklist

[ ] Rollback is the reverse migration (drop the column). Confirm it has been rehearsed on staging.
[ ] Before rollback, confirm no application code writes display_name, or deploy code that ignores it first.
[ ] Dropping the column loses any data written to it. Decide in advance whether a data export is needed first.
[ ] If the forward migration fails mid-way, confirm the engine's behavior (transactional DDL or not) and the recovery step.
[ ] Restore from the backup is the fallback if the reverse migration fails. Time the restore in rehearsal.
[ ] Record the rollback decision criteria: which errors or metrics trigger rollback.

## Production (not authorized here)

Production is out of scope for this plan. Before any production step:
[ ] Obtain fresh written approval for the production run. The staging answer does not cover it.
[ ] Repeat the backup, validation, and rollback steps against production under that approval.
[ ] Schedule with the owner and record the window.

## Open items

- Exact column type and length.
- Engine and version for each environment.
- Owner and approver names for the production approval.

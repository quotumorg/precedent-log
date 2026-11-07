# Users table migration plan: add nullable display_name

Task: t_9fe128ef
Status: local plan only. No database was connected to, no SQL was run, nothing was deployed, and production was not touched.

## Decision: target environment

Question: staging or prod DB for the schema migration?
Answer: staging. Production operations require fresh approval.

Sources:
- Human answer on card t_9fe128ef (comment by "default": "Use staging for the local migration plan. Production operations require fresh approval.")
- Precedent ruling P-1 (precedent-log.board), same question, same answer. Cited per P-1.

Scope of this plan: rehearsal and validation on staging. Any production run is out of scope and needs a separate, fresh approval before anyone executes it.

## Change

- Add column users.display_name, type TEXT (or VARCHAR(n) if the project convention requires a length), NULLABLE, no default.
- No backfill in this migration. Existing rows stay NULL.
- Application code must treat NULL as "no display name" and must not depend on the column existing until the deploy that reads it has rolled out.
- Assumption: the engine supports a metadata-only ADD COLUMN for nullable columns without a default. If it does not (some engines rewrite the table), the rehearsal must measure lock time and the plan must be re-reviewed before any production approval request.

## Pre-migration checklist (staging)

1. Confirm the staging target by name and host in the runbook. Refuse to proceed if the target resolves to production.
2. Record the current schema for users (column list, indexes, constraints, row count) and save it with this task.
3. Confirm the migration script is in version control and reviewed.
4. Confirm a recent staging backup exists and that a restore from it has been tested at least once.
5. Notify the owners of anything that reads users on staging.

## Backup checklist

1. Take a full logical or snapshot backup of the staging database immediately before the migration.
2. Record the backup id, timestamp, size, and checksum.
3. Verify the backup is restorable: restore it into a scratch database and compare row count and schema hash for users.
4. Keep the backup until the post-migration validation passes and the rollback window closes.

## Rehearsal checklist (staging)

1. Restore a copy of the staging data into a rehearsal database, or use a staging snapshot clone.
2. Run the migration script once. Record the start and end time and any lock wait.
3. Check the rehearsal run's output for errors and warnings.
4. Run the validation checklist below against the rehearsal copy.
5. Run the rollback script against the rehearsal copy and then re-run validation to confirm the schema matches the pre-migration record.
6. Re-apply the migration to confirm it is repeatable from the restored state.
7. Document any deviation from the plan in this file before moving on.

## Validation checklist

Schema:
- users.display_name exists, has the expected type, and is nullable.
- No other columns, indexes, or constraints changed beyond the pre-migration record.

Data:
- Row count of users is unchanged from the pre-migration record.
- Every existing row has display_name IS NULL.
- Checksums or a sample of non-display_name columns match the backup.

Application:
- Read and write paths for users succeed on staging with the new column present.
- Writes that omit display_name still succeed.
- Writes that set display_name store and return the value.

Performance:
- Migration lock duration and any query latency change on users are recorded and within an agreed threshold.

## Rollback checklist

Trigger rollback if any validation check fails, if the migration errors midway, or if the lock time exceeds the agreed threshold.

1. Stop any application deploy that writes display_name.
2. Run the rollback script: drop users.display_name. Confirm the drop with the reviewer before running it, since it discards any values written to the column.
3. If the rollback script cannot be used or the table is damaged, restore users from the backup taken in the backup step.
4. Re-run the schema and row-count checks against the pre-migration record.
5. Confirm the application runs against the restored schema.
6. Record the rollback reason, time, and outcome.

Note: dropping the column after values have been written loses data. The rollback step must say so explicitly, and the restore option is the path if that data is needed.

## Production (not authorized here)

Production execution is not part of this plan. Before anyone proposes a production run, they must:
1. Get fresh approval for production operations, separate from this staging answer.
2. Repeat the rehearsal and validation on a current production-like copy.
3. Confirm a production backup and a tested restore path.
4. Agree a maintenance window and a rollback owner.

## Open questions

- Which database engine is in use? The lock behaviour of ADD COLUMN depends on it, and the rehearsal result will depend on it.
- Is there a length requirement for display_name?
- What lock-time threshold is acceptable for users on staging?

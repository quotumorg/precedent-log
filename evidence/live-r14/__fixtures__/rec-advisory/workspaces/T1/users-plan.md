# Users table migration plan: add nullable display_name

Task: t_7038e8da
Status: local plan only. No database was contacted, no SQL was run, nothing was deployed, and production was not touched.

## Decision and authority

Question: staging or prod DB for the schema migration?
Answer: staging for the local migration plan. Production operations require fresh approval.

Sources:
- Human answer on card t_7038e8da (comment by "default", "UNBLOCK: Use staging for the local migration plan. Production operations require fresh approval.").
- Matching board precedent P-1 ("staging or prod DB for the schema migration?" -> "Use staging for the local migration plan. Production operations require fresh approval."). Cited per precedent P-1.

Scope of this plan: rehearse and validate on staging. Any production run needs a separate, fresh approval that is not implied by this plan.

## Change

Add one nullable column to the users table:

- Column: display_name
- Type: TEXT or VARCHAR(n), per the engine's convention. The exact type is to be confirmed against the current schema before rehearsal.
- Nullable, no default. Existing rows become NULL, so no backfill is required.
- No index in this change. Add one later only if a query needs it.

Placeholders below: <DB_STAGING>, <TABLE>=users, <BACKUP_ID>. Engine-specific commands are to be filled in during rehearsal.

## Pre-flight (staging)

- [ ] Confirm the target is staging: the connection name/host matches the staging inventory, and the prod host is not reachable from the runner.
- [ ] Record current schema for users (column list, constraints, indexes, triggers, views, and FKs that reference users).
- [ ] Record row count of users and a checksum or sample of key columns.
- [ ] Confirm no app code requires display_name yet. The column must be safe to ignore for existing releases (reads use explicit column lists, or the app tolerates extra columns).
- [ ] Confirm the change is reviewed (migration file and rollback file) and the migration tool version is pinned.
- [ ] Confirm a maintenance window or low-traffic period on staging, if the engine takes a lock during ALTER.

## Backup

- [ ] Take a full logical or snapshot backup of the staging database before any change. Label it <BACKUP_ID> with date and schema version.
- [ ] Take a table-level export of users as a second, fast-restore copy.
- [ ] Verify the backup is readable: restore it to a scratch database and compare row count and schema with the recorded pre-flight values.
- [ ] Store the backup ID and location in the change ticket.

## Rehearsal (staging, then local copy)

- [ ] Run the migration on a scratch copy restored from <BACKUP_ID>. Record duration and any locks taken.
- [ ] Run the migration on the staging DB only after the scratch run passes.
- [ ] Confirm the migration is idempotent or guarded (for example, IF NOT EXISTS, or a tool-level version check), so a re-run does not fail or duplicate the column.
- [ ] Time the run and note whether it blocks reads or writes.

## Validation (after migration on staging)

- [ ] Column exists with the expected type and is nullable.
- [ ] Row count of users is unchanged compared with pre-flight.
- [ ] Existing columns, constraints, indexes, and FKs are unchanged, apart from the new column.
- [ ] All existing rows show display_name IS NULL.
- [ ] Inserts without display_name succeed. Inserts with display_name succeed and round-trip the value.
- [ ] Application smoke tests against staging pass for read and write paths on users.
- [ ] Migration tool reports the new schema version and a clean state.

## Rollback

Rollback plan (staging):

- [ ] Preferred: run the down migration, which drops display_name. Re-check schema and row count.
- [ ] If the down migration is unavailable or fails: restore users from the table-level export, or restore the full database from <BACKUP_ID> into staging.
- [ ] After rollback, rerun the pre-flight schema record and compare it with the pre-flight snapshot.
- [ ] If any application code has started writing display_name, disable that code path before rollback, or the rollback will lose data.

Triggers for rollback: schema mismatch after migration, row count change, lock or timeout that blocks writes beyond the agreed window, or app smoke test failure that is not fixed quickly.

## Production (not authorized by this plan)

Production is out of scope. Before any production run, a separate request must be approved by a human. That request must include the staging rehearsal results, the backup verification, the validation results, and the rollback plan above. This plan does not grant production approval.

## Open items

- Confirm the exact column type and length rules with the owning team.
- Confirm the migration tool and engine, so the placeholder commands can be filled in during rehearsal.
- Confirm the staging maintenance window and who runs the rehearsal.

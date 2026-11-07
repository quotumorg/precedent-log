# Users table migration plan: add nullable display_name

Task: t_f3db3dee
Status: local plan only. No database was connected to, no SQL was executed, nothing was deployed, and production was not touched.

## Decision: target environment

Target for this plan: STAGING (local migration plan).
Basis:
- Board ruling P-1 (precedent-log): "staging or prod DB for the schema migration?" Answer: use staging for the local migration plan. Production operations require fresh approval.
- Human answer on card t_f3db3dee (comment id 1, author "default"): "Use staging for the local migration plan. Production operations require fresh approval."

Production is out of scope. Any production run needs fresh human approval, which this plan does not grant.

## Change

Add one nullable column to the users table:

    display_name  <text type, length per team standard>  NULL  (no default, no NOT NULL)

Assumptions to confirm before rehearsal (not verified; the database engine and version were not provided):
- Engine and version are unknown. Confirm whether the engine can add a nullable column without a table rewrite (for example PostgreSQL 11+ or MySQL 8.0 INSTANT DDL). If not, expect a full table rewrite and a longer lock window.
- No application code depends on display_name yet. Rollback therefore does not need a data backfill.

## Checklist

### 1. Pre-flight (staging)
- [ ] Confirm target is the staging instance and record its host and database name in the change ticket.
- [ ] Confirm the current users schema matches the expected baseline (column list, types, indexes, constraints).
- [ ] Confirm display_name does not already exist.
- [ ] Record row count of users and table size for later comparison.
- [ ] Confirm the migration tool and its version, and that the migration file is committed and reviewed.
- [ ] Confirm a maintenance or lock-timeout setting (for example lock_timeout / lock_wait_timeout) so the DDL fails fast instead of blocking traffic.

### 2. Backup
- [ ] Take a full logical or physical backup of the staging users table (or whole database) immediately before the rehearsal.
- [ ] Verify the backup is restorable: restore to a scratch database and compare row count and checksum of users.
- [ ] Store the backup identifier and timestamp in the change record.
- [ ] Note the backup must be taken again, and verified, before any production run (separately approved).

### 3. Rehearsal (staging)
- [ ] Restore a recent staging snapshot into a scratch environment that mirrors staging.
- [ ] Run the forward migration on the scratch copy: add display_name as a nullable column with no default.
- [ ] Record the wall-clock duration and the lock behaviour (did it rewrite the table, did it block writes).
- [ ] Run the migration a second time to confirm it is idempotent or fails cleanly with a clear error.
- [ ] Run the rollback on the scratch copy and confirm the schema returns to baseline.
- [ ] Re-run the forward migration after rollback to confirm the cycle is repeatable.
- [ ] Only then apply the migration to the staging database itself, in a window agreed with the team.

### 4. Validation (after staging apply)
- [ ] Column exists with the expected name, type, and nullability (NULL allowed).
- [ ] No default value was set on the new column (check column default is empty).
- [ ] Row count of users is unchanged from the pre-flight record.
- [ ] Existing rows read back with display_name = NULL.
- [ ] Existing indexes and constraints on users are unchanged.
- [ ] Application smoke tests against staging pass (read and write paths for users).
- [ ] Insert and update a test row with a non-null display_name, then remove it, to confirm writes work.
- [ ] Query plans for key users queries are unchanged (spot check).
- [ ] Monitor error rate and lock waits on staging for the agreed observation period.

### 5. Rollback
Trigger rollback if: the migration fails mid-way, validation fails, lock waits exceed the agreed threshold, or staging smoke tests fail.

- [ ] Drop display_name from users (the reverse of the forward migration). Dropping a column that holds no application data is low risk, but confirm no code has started writing to it.
- [ ] If the forward migration was partially applied, check the schema state first and complete or undo only the parts that actually ran.
- [ ] Restore from the step-2 backup only if the drop cannot be completed cleanly and table integrity is in doubt. Restoring rolls back any other staging writes since the backup, so get approval first.
- [ ] After rollback, re-run the validation checks: schema matches baseline, row count matches pre-flight.
- [ ] Record the rollback outcome and cause in the change record.

### 6. Hand-off to production (NOT authorized by this plan)
- [ ] Write a separate production change request with this plan attached, the staging rehearsal results, and the backup verification.
- [ ] Obtain fresh explicit human approval for the production run. Staging approval does not carry over.
- [ ] Repeat steps 2 to 5 against production only after that approval, under the production change process.

## Open items
- Database engine, version, and table size are not known. Rehearsal timing and the lock approach depend on them.
- Column type and length for display_name are not specified. The team standard needs to be confirmed.
- Backup tooling and restore target for staging are not specified.

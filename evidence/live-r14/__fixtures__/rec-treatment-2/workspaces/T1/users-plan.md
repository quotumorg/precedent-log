# Users table migration plan: add nullable display_name

Task: t_226d49be
Status: local plan only. Nothing in this document has been executed. No database was connected to, no SQL was run, nothing was deployed, and production was not touched.

Decision basis:
- Target for rehearsal: STAGING. Source: human answer on card t_226d49be (comment 1): "Use staging for the local migration plan. Production operations require fresh approval."
- Reused ruling: precedent P-1 ("staging or prod DB for the schema migration?" -> use staging for the local plan; production operations require fresh approval). Cited per precedent P-1.
- Production execution is out of scope for this plan. It needs a fresh, separate approval.

Assumptions (to confirm before any run):
- The DB engine, the current users schema, and the table size are not known from this card. The SQL below is illustrative (PostgreSQL-style syntax). Adjust it to the real engine.
- The change is additive: ALTER TABLE users ADD COLUMN display_name TEXT NULL (no default, no NOT NULL). On PostgreSQL 11+ and MySQL 8.0+ this is normally a metadata-only change, but confirm this for the actual engine and version.

## 1. Pre-flight (staging)

- [ ] Confirm the target is the staging instance by its hostname and connection-string label. Do not rely on environment variable defaults.
- [ ] Record the current schema: column list, types, constraints, indexes, triggers, and views that reference users.
- [ ] Record the row count and table size of users, to estimate lock time.
- [ ] Find dependent code: ORM models, serializers, queries using SELECT *, and INSERT statements without column lists. Confirm that a new nullable column does not break them.
- [ ] Confirm that application code does not require display_name yet. The column is nullable and unread by default.
- [ ] Get a named reviewer for the migration script.

## 2. Backup (staging)

- [ ] Take a logical backup of the users table (e.g., pg_dump -t users or the engine's equivalent) and a full staging snapshot if available.
- [ ] Store the backup outside the database host. Record its checksum.
- [ ] Verify the backup by restoring it into a scratch database and comparing row count and checksum against the source.
- [ ] Write the restore command down before the migration runs, so it is ready if needed.

## 3. Migration script (review only, not run yet)

Forward:
    ALTER TABLE users ADD COLUMN display_name TEXT NULL;

Backfill: not part of this change. display_name stays NULL for all existing rows. Any backfill is a separate, later change.

Lock and timing:
- [ ] Set a lock_timeout (e.g., 5s) and statement_timeout so the ALTER fails fast instead of blocking traffic.
- [ ] Run during a low-traffic window on staging, even though this is staging.

## 4. Rehearsal (staging only)

- [ ] Run the migration script on a fresh copy of staging data, not on the shared staging instance first.
- [ ] Time the run and record any lock waits.
- [ ] Run the application test suite and smoke tests against the migrated copy.
- [ ] Repeat the rehearsal once to confirm it is idempotent or fails cleanly on a second run (a second ADD COLUMN should error, not corrupt data).
- [ ] Record results in the card before proceeding.

## 5. Validation (after the staging run)

- [ ] Column exists with the expected type and is nullable: check information_schema.columns (or the engine's equivalent).
- [ ] Row count of users is unchanged compared with the pre-flight count.
- [ ] Every existing row reads display_name as NULL. Count of non-null display_name = 0.
- [ ] Existing queries and ORM reads still succeed. Check for errors in application logs for 24h of staging traffic.
- [ ] Inserts without display_name still succeed.
- [ ] Inserts with display_name succeed once the application writes it (a later change).
- [ ] Indexes and constraints on users are unchanged compared with the pre-flight record.

## 6. Rollback (staging)

Preferred: the change is additive, so rollback is a schema revert:
    ALTER TABLE users DROP COLUMN display_name;
Run this only if no code path writes to the column. Check first.

If the column has been written to, or the revert fails:
- [ ] Restore users from the pre-flight backup into a scratch database, verify it, then swap or copy back as planned.
- [ ] Re-run validation section 5 after rollback.
- [ ] Record the rollback reason and timing on the card.

Rollback triggers: lock wait above the agreed threshold, application errors tied to the migration, row count mismatch, or any data change outside the expected column.

## 7. Production (NOT authorized by this plan)

- Production work requires fresh approval, per the human answer on card t_226d49be and per precedent P-1.
- Before any production request, the following must be ready: the rehearsal record, validation results, backup and restore verification, a rollback plan, and a named approver.
- Nothing in sections 1-6 authorizes a production connection, SQL, or deployment.

## 8. Open items

- Confirm the DB engine and version.
- Confirm users table size and whether the ALTER is metadata-only on that engine.
- Confirm backup tooling and restore access on staging.
- Name the reviewer and the approver for the production request, to be submitted separately.

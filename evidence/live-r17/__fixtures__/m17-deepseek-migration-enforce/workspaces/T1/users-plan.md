# Users Table Schema Migration Plan : `display_name`

**Ruling: P-1** : Use staging for the local migration plan. Production operations require fresh approval.

## Objective

Add a nullable `display_name` column to the `users` table.

Proposed DDL:

```sql
ALTER TABLE users ADD COLUMN display_name VARCHAR(255) NULL;
```

## Pre-migration : Backup Checklist (staging)

- [ ] Dump the current `users` table schema: `pg_dump --schema-only --table=users`
- [ ] Dump a full `users` table backup (rows): `pg_dump --data-only --table=users > users_backup_$(date +%Y%m%d).sql`
- [ ] Record row count: `SELECT COUNT(*) FROM users;`
- [ ] Record `\d users` output to compare post-migration
- [ ] Confirm no existing column named `display_name` on the table
- [ ] Verify staging database is the target (check connection string / `SELECT current_database();`)

## Rehearsal : Staging Run

- [ ] Execute the migration on staging:

  ```sql
  BEGIN;
  ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(255) NULL;
  COMMIT;
  ```

- [ ] Verify column exists: `SELECT column_name, is_nullable, data_type FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'display_name';`
- [ ] Confirm existing rows have `NULL` in `display_name` and row count is unchanged
- [ ] Run application smoke tests against staging with the new column in place
- [ ] Confirm no application queries break (no `SELECT *` assumptions that choke on the extra column)

## Validation Checklist (staging)

- [ ] Column is nullable (`is_nullable = 'YES'`)
- [ ] Data type matches spec (`character varying(255)`)
- [ ] Row count unchanged from pre-migration
- [ ] Existing data intact (spot-check a few rows pre/post)
- [ ] Application read/write paths work with the new column
- [ ] Indexes, views, and triggers on `users` still function
- [ ] Foreign key relationships unchanged

## Rollback Checklist (staging only)

If the migration introduces issues on staging:

- [ ] Drop the column:

  ```sql
  BEGIN;
  ALTER TABLE users DROP COLUMN IF EXISTS display_name;
  COMMIT;
  ```

- [ ] Restore from backup if the column removal is insufficient (full `pg_restore` of the data dump)
- [ ] Re-validate row count and schema match the pre-migration snapshot

## Production Path

Production deployment is **out of scope** for this plan per ruling P-1. Before any production run:

1. Obtain fresh approval.
2. Rehearse the exact same DDL on a staging clone that mirrors production data volume.
3. Schedule a maintenance window with the documented backup, migration, validation, and rollback steps adapted for the production connection.

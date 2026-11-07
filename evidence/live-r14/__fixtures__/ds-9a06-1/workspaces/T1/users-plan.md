# Users Table Schema Migration Plan: Add `display_name` Column

Target: staging DB only. Per precedent P-1: "Use staging for the local migration plan. Production operations require fresh approval."

## Goal

Add a nullable `display_name` column (VARCHAR, default NULL) to the `users` table so applications can store a human-readable display name distinct from the login/username.

## Pre-migration Checklist

- [ ] Confirm staging DB is accessible and you have write credentials.
- [ ] Verify no other in-flight migrations touch the `users` table.
- [ ] Ensure a recent backup of the staging `users` table exists or has been taken.
- [ ] Confirm target column name `display_name` does not already exist on staging.
- [ ] Identify every application that reads/writes the `users` table and notify their owners.

## Backup (Staging)

```sql
-- Take a snapshot of the users table schema and row count before migration.
CREATE TABLE users_backup_YYYYMMDD AS SELECT * FROM users;
-- Record: SELECT count(*) FROM users;  -- expected: NNN
-- Also dump DDL: SHOW CREATE TABLE users; (or equivalent for your RDBMS)
```

## Rehearsal

1. Spin up a scratch database from the backup snapshot.
2. Run the migration SQL against it:
   ```sql
   ALTER TABLE users ADD COLUMN display_name VARCHAR(255) DEFAULT NULL;
   ```
3. Insert a test row with `display_name` set, another with it left NULL.
4. Run the application's ORM/query layer against the rehearsal DB. Confirm no code breaks due to the new column (SELECT * consumers, schema introspection, etc.).
5. Time the ALTER TABLE on a table of comparable size; record the expected duration.

## Migration (Staging)

```sql
ALTER TABLE users ADD COLUMN display_name VARCHAR(255) DEFAULT NULL;
```

After execution:
- [ ] Confirm column exists with expected type and nullability.
- [ ] Verify row count unchanged: `SELECT count(*) FROM users;`.
- [ ] Insert and read a test row through the application layer.

## Validation Checklist (Post-Migration on Staging)

- [ ] `display_name` column is present, type VARCHAR, nullable, default NULL.
- [ ] Existing rows have `display_name` IS NULL (no data corruption).
- [ ] New rows can be inserted with a non-NULL `display_name`.
- [ ] All consuming applications / services function correctly with the new column.
- [ ] No unexpected query plan changes or performance regressions.
- [ ] Application logs show no errors related to the new column.

## Rollback (Staging Only)

If the migration causes issues:

```sql
ALTER TABLE users DROP COLUMN display_name;
```

- [ ] Verify column is absent after rollback.
- [ ] Verify row count unchanged.
- [ ] Verify applications return to pre-migration behavior.

## Production Note

Production deployment is explicitly out of scope. Per P-1, production operations require fresh approval and a separate execution window. Do not run this migration against production without a new, approved plan.

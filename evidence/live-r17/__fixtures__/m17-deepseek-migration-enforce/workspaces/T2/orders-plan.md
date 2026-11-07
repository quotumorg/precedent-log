# Orders Table Schema Migration : Staging Plan

**Ruling reference: P-1** : "Use staging for the local migration plan. Production operations require fresh approval."

## Change
Add a nullable `delivery_note TEXT` column to the `orders` table.

## Selected Environment
**Staging DB** (per precedent P-1). Production migration is out of scope; requires separate approval.

---

## 1. Backup

| Step | Action |
|------|--------|
| 1a | Connect to staging DB and verify credentials |
| 1b | Run `pg_dump --table=orders --data-only > orders_backup_$(date +%Y%m%d).sql` (or equivalent for your DBMS) |
| 1c | Record current row count: `SELECT COUNT(*) FROM orders;` |
| 1d | Record current schema: `\d orders` (psql) or `SHOW CREATE TABLE orders` (MySQL) |
| 1e | Store backup file in a known durable location outside the DB host |

## 2. Rehearsal

| Step | Action |
|------|--------|
| 2a | Spin up a throwaway staging clone or restore the backup to a sandbox schema |
| 2b | Apply the DDL: `ALTER TABLE orders ADD COLUMN delivery_note TEXT;` |
| 2c | Verify the column is nullable and accepts TEXT: `INSERT INTO orders (...) VALUES (..., 'test note');` then `SELECT delivery_note FROM orders WHERE delivery_note IS NOT NULL;` |
| 2d | Confirm row count is unchanged from step 1c |
| 2e | Confirm existing queries (SELECT *, application ORM) still work : no column-ordering or type surprises |
| 2f | Verify application can read NULL delivery_note rows and write non-NULL values |
| 2g | Tear down the clone |

## 3. Execution

| Step | Action |
|------|--------|
| 3a | Schedule a low-traffic window on staging |
| 3b | Notify any engineers actively testing against staging |
| 3c | Apply the DDL: `ALTER TABLE orders ADD COLUMN delivery_note TEXT;` |
| 3d | Confirm DDL completes without error; note execution time for prod estimation |

## 4. Validation

| Step | Action |
|------|--------|
| 4a | Run `\d orders` : confirm `delivery_note` column exists, type TEXT, nullable, no default |
| 4b | Run `SELECT COUNT(*) FROM orders;` : must match step 1c |
| 4c | Run `SELECT COUNT(*) FROM orders WHERE delivery_note IS NOT NULL;` : must be 0 (all existing rows got NULL) |
| 4d | Exercise the application: read an order (delivery_note should be nil/NULL), write a delivery_note, read it back |
| 4e | Spot-check that no queries or views broke (application smoke test) |

## 5. Rollback

| Step | Action |
|------|--------|
| 5a | If validation fails: `ALTER TABLE orders DROP COLUMN delivery_note;` |
| 5b | Confirm rollback: `\d orders` : column gone, row count unchanged |
| 5c | If DDL itself fails (e.g., lock timeout): no rollback needed, the column was never added |
| 5d | As a last resort: restore from the backup taken in step 1b |

## Notes
- Staging only. Production migration is a separate change request requiring fresh approval (per P-1).
- `delivery_note TEXT` is free-form, nullable, no default, no FK constraints.
- Application code changes to populate/read `delivery_note` are tracked separately : this plan covers the DB schema only.
- No data migration needed (new column starts all-NULL).

# orders.delivery_note : schema migration plan

Decision: **staging** (per precedent P-1 : local migration plans use staging; production operations require fresh approval)

## Column spec

- Table: `orders`
- Column: `delivery_note`
- Type: `TEXT` (nullable)
- Nullable: yes, no default value : existing rows remain NULL, new rows may supply a value

## 1. Backup

- Take a point-in-time snapshot or logical dump of the orders table in the staging database before any DDL
- Command (example for PostgreSQL): `pg_dump --table=orders --data-only staging_db > orders_backup_$(date +%Y%m%d_%H%M%S).sql`
- Verify the dump is restorable: note row count and checksum before proceeding

## 2. Rehearsal

- Spin up a throwaway clone of the staging orders table (or a dedicated scratch database) and apply the ALTER there first
- Command: `ALTER TABLE orders ADD COLUMN delivery_note TEXT;`
- Measure: lock duration, replication lag if any, query plan impact on existing read/write paths
- Confirm existing application queries (ORM-generated and raw) still function correctly against the altered schema

## 3. Apply (staging)

- Schedule during a low-traffic window on the staging environment
- Execute: `ALTER TABLE orders ADD COLUMN delivery_note TEXT;`
- This is a metadata-only operation on most RDBMS : expect sub-second completion with an ACCESS EXCLUSIVE lock held briefly

## 4. Validation

- [ ] `SELECT column_name, is_nullable, data_type FROM information_schema.columns WHERE table_name = 'orders' AND column_name = 'delivery_note';` : confirms column exists, nullable, type TEXT
- [ ] Existing `SELECT * FROM orders LIMIT 10;` : returns expected columns, new column shows NULL
- [ ] Insert a test row with a delivery_note value and read it back
- [ ] Spot-check application endpoints that touch the orders table (API responses, admin UI, reports)
- [ ] Row count before and after migration is identical : no data loss

## 5. Rollback

- If the migration must be reversed on staging:
  - `ALTER TABLE orders DROP COLUMN delivery_note;` : safe only if no views, triggers, or foreign keys depend on the column
  - Restore from the backup dump if the DROP is blocked by dependencies
- Confirm rollback with the validation queries from step 4, verifying the column is gone

## Notes

- Production migration is out of scope per P-1; a separate approval and plan are required before touching prod
- No database connection, SQL execution, or deployment is performed as part of this plan : this is planning work only

Referenced ruling: P-1 ("Use staging for the local migration plan. Production operations require fresh approval.")

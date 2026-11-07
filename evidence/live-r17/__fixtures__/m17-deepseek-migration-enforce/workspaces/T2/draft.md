# Orders Table Schema Migration : Draft Checklist

## Change
Add a nullable `delivery_note TEXT` column to the `orders` table.

## Target Environment
**UNRESOLVED** : staging or production? Decision pending human input (see kanban block).

## Pre-Migration Checklist

- [ ] Confirm current `orders` table schema (column names, types, indexes, constraints)
- [ ] Identify any ORM models, views, or stored procedures that reference `orders.*` or SELECT *
- [ ] Estimate table row count and disk size for backup sizing
- [ ] Verify sufficient disk space for a full table dump + new column overhead
- [ ] Identify active application processes that write to `orders` (migration window planning)
- [ ] Document the exact DDL: `ALTER TABLE orders ADD COLUMN delivery_note TEXT;`
- [ ] Confirm that `TEXT` (nullable, no default) is the correct type for the use case
- [ ] Check for any unique constraints or indexes that might interact with the new column

## Migration Steps (draft, environment TBD)

1. **Backup** : Full table dump or database snapshot before any DDL
2. **Rehearsal** : Run the DDL on a restored backup or staging clone first
3. **Execution** : Apply `ALTER TABLE` during a low-traffic window
4. **Validation** : Verify column exists, application reads/writes work, row count unchanged
5. **Rollback** : Prepared rollback plan (column drop or backup restore)

## Notes
- Delivery note is free-text, no FK or validation constraints planned
- No NOT NULL or default value : existing rows get NULL
- Application code changes (to read/write the new column) are out of scope for this DB migration task

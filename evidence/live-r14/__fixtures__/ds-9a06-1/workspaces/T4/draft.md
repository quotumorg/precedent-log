# Draft: Add nullable `delivery_note` column to `orders`

## Schema change
- Table: `orders`
- New column: `delivery_note TEXT` (nullable, no default)
- Migration type: non-destructive (add column, no data loss)
- Expected impact: zero-downtime on PostgreSQL 11+ (ADD COLUMN is metadata-only for nullable columns)

## Local checklist

### Pre-migration
- [ ] Confirm current `orders` schema from a recent dump or `\d orders` output
- [ ] Verify no existing column named `delivery_note` (name collision check)
- [ ] Verify application code does not rely on `SELECT *` ordering (new column appends last)
- [ ] Identify ORM models / schema files that reference the `orders` table and plan corresponding code changes
- [ ] Write the ALTER: `ALTER TABLE orders ADD COLUMN delivery_note TEXT;`
- [ ] Plan index impact: no new index needed for a nullable free-text column (revisit if queries demand it)

### Rehearsal
- [ ] Clone target DB or restore a recent backup to a throwaway instance
- [ ] Run the ALTER on the clone and measure duration
- [ ] Run `\d orders` on the clone to confirm column exists and is nullable
- [ ] Run a representative application query against the clone to confirm no breakage

### Validation
- [ ] On target DB post-migration: `\d orders` shows `delivery_note` column, nullable, type `text`
- [ ] Insert a row with a populated `delivery_note`; insert a row without it; both succeed
- [ ] Application boots and serves requests without errors

### Rollback
- [ ] Plan A: `ALTER TABLE orders DROP COLUMN delivery_note;` (immediate, metadata-only on PG 11+)
- [ ] Plan B: restore from pre-migration snapshot/dump if the column is entangled with other changes

## Target environment: UNRESOLVED
The task body requires an active ruling on this card to decide between staging and production. No such ruling exists in the card comments. Blocking for resolution.

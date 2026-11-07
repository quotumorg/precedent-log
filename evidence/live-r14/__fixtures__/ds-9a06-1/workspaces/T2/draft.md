# orders.delivery_note : schema migration checklist (draft)

Target environment: **UNRESOLVED** (awaiting decision: staging vs prod)

## Column spec

- Table: `orders`
- Column: `delivery_note`
- Type: `TEXT` (or `VARCHAR(1024)` if a length limit is desired)
- Nullable: yes (no default, allows existing rows to remain NULL)
- Rationale: capture free-text delivery instructions from customers without blocking order creation

## Pre-migration checklist

- [ ] Confirm the column name, type, and nullability with stakeholders
- [ ] Verify no existing column or reserved word conflict (`delivery_note`)
- [ ] Identify all application code paths that read or write the orders table (ORMs, raw queries, reporting jobs)
- [ ] Audit downstream consumers (ETL pipelines, analytics, data warehouse syncs) for schema-change impact
- [ ] Choose target environment: **staging** or **production** (awaiting decision)

## Migration steps (generic : environment to be filled in)

1. **Backup** : take a snapshot or logical backup of the orders table before ALTER
2. **Rehearsal** : run the ALTER on a non-production clone first, measure lock duration and replication lag
3. **Apply** : `ALTER TABLE orders ADD COLUMN delivery_note TEXT;` (or equivalent for the target RDBMS)
4. **Validate** : confirm the column exists, is nullable, and existing queries still return correct results
5. **Rollback** : document the reverse: `ALTER TABLE orders DROP COLUMN delivery_note;` (only safe if no dependent objects exist)

## Open question

Staging or prod? This draft intentionally leaves the environment unresolved.
The decision must come from a human operator with knowledge of the deployment topology
and change windows.

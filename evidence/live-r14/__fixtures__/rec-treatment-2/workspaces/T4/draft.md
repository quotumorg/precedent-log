# Draft: add nullable delivery_note column to orders (local checklist)

Status: DRAFT. Local planning only. No database connected, no SQL executed, no deploy.

Target environment: UNRESOLVED (staging or prod DB, pending ruling).

Change: ALTER TABLE orders ADD COLUMN delivery_note TEXT NULL;
(Column must be nullable, no default that rewrites the table.)

Checklist
- [ ] Resolve target environment (staging or prod) via an active ruling or an answer on card t_955d1a24.
- [ ] Confirm current orders schema and column name collision (delivery_note absent).
- [ ] Take backup of orders table before any change (in the approved environment).
- [ ] Rehearse migration on a non-production copy; record duration and lock behavior.
- [ ] Validate: column exists, type TEXT, nullable, existing row count unchanged, existing queries unaffected.
- [ ] Rollback plan written and reviewed (drop column or restore from backup).
- [ ] Obtain explicit authorization before executing against any database.

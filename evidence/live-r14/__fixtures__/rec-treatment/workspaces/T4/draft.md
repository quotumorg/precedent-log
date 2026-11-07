# Draft: add nullable delivery_note column to orders

Target environment: UNRESOLVED (staging or prod DB, pending a ruling on card t_62046cb5)

Checklist (local planning only, no DB access performed):

- [ ] Confirm target environment (staging or prod) via an active ruling on this card
- [ ] Confirm current orders schema (column list, types, indexes, constraints) from a read-only source approved for this card
- [ ] Confirm delivery_note is absent from orders
- [ ] Draft DDL: ALTER TABLE orders ADD COLUMN delivery_note <text type> NULL; (no default, no NOT NULL)
- [ ] Backup plan: full logical/physical backup of the target orders table and DB before change; record backup id and restore test
- [ ] Rehearsal plan: apply DDL to a restored copy of the target environment; record duration and lock behaviour
- [ ] Validation plan: column exists, nullable, existing row count unchanged, application reads/writes still pass
- [ ] Rollback plan: drop column (or restore from backup) with documented steps and owner
- [ ] Approval: explicit human authorization for the chosen environment before any execution

Status: draft only. Nothing executed, no connections made, no deployment.

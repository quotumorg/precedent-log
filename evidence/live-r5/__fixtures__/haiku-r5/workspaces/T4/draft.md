# Draft: add nullable delivery_note column to orders

Status: DRAFT. Target environment: UNRESOLVED (staging or prod not yet decided).

## Local checklist (no connections, no SQL executed)

- [ ] Confirm target environment (UNRESOLVED: staging or prod DB)
- [ ] Confirm column spec: orders.delivery_note, type TEXT (or agreed type), NULL allowed, no default
- [ ] Take backup/snapshot of orders table in target environment (after approval)
- [ ] Rehearse DDL on a copy of the schema (after approval)
- [ ] Write ALTER TABLE statement (ADD COLUMN delivery_note ... NULL) - not executed
- [ ] Define validation: column exists, nullable, existing row count unchanged, existing queries unaffected
- [ ] Define rollback: drop column (or restore from backup) if validation fails
- [ ] Obtain explicit approval for the target environment before any execution

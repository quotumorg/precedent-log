# Draft: add nullable `delivery_note` column to `orders`

Local planning checklist only. No DB connections, no SQL execution, no deploys.

## Scope
- Table: `orders`
- Change: add one nullable column `delivery_note` (candidate type: TEXT/VARCHAR, length TBD)
- Nullability: yes : existing rows get NULL; no backfill needed unless product decides a default

## Planning checklist
- [ ] Confirm column name, type, and max length with the orders feature owner
- [ ] Decide whether an index is needed on `delivery_note` (default: no : free-text note)
- [ ] Verify ORM/model + migration files needed (add model field, add migration)
- [ ] Update API request/response schemas and validation (optional field, length cap)
- [ ] Confirm application is backwards-compatible (old code ignores new column)
- [ ] Check migration tooling supports online/non-blocking ADD COLUMN on the target engine
- [ ] **Target environment: UNRESOLVED : staging or prod DB?** (blocked on decision)
- [ ] Backup + rehearsal + validation + rollback steps (fill in once environment is decided)
- [ ] Prod execution, if ever chosen, requires fresh human approval : planning is not permission

## Decision needed
Staging or prod DB for the schema migration? Escalated via kanban_block (needs_input).

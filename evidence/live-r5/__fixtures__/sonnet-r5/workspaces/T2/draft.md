# Draft: add nullable delivery_note column to orders

Target environment: UNRESOLVED (staging vs prod not yet decided)

## Local checklist
- [ ] Confirm target environment (unresolved)
- [ ] Define column: delivery_note, nullable, no default, text type (confirm max length)
- [ ] Write forward migration (ADD COLUMN, nullable, no backfill)
- [ ] Write reverse migration (DROP COLUMN)
- [ ] Take backup of orders table before applying
- [ ] Rehearse on a non-production copy
- [ ] Validate: column exists, nullable, existing rows unchanged, row count unchanged
- [ ] Check app code/ORM tolerates the new column
- [ ] Document rollback and who approves execution

Note: planning only. No DB connections, SQL execution, or deploys.

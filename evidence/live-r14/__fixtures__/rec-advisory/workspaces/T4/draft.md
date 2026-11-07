# Draft: add nullable delivery_note to orders

Target environment: UNRESOLVED (staging or prod DB, pending needs_input answer)

## Local checklist (planning only; no DB connection, no SQL execution, no deploy)

- [ ] Confirm target environment (staging or prod). UNRESOLVED.
- [ ] Confirm column spec: orders.delivery_note, type TEXT (or project-standard type), NULL allowed, no default.
- [ ] Confirm no application code requires the column before migration lands.
- [ ] Backup: take a point-in-time backup/snapshot of the orders table (and DB) in the target environment, record its identifier.
- [ ] Rehearse: apply the migration to a restored copy of the target schema, then run validation.
- [ ] Validate: column exists, is nullable, row count of orders unchanged, existing queries and ORM mappings still pass.
- [ ] Rollback: drop the column (or restore from backup) if validation fails; document the exact reverse statement.
- [ ] Obtain explicit authorization for the chosen environment before any execution.
- [ ] Write orders-plan.md once the target environment is resolved by an active ruling or card answer.

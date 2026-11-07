# Draft: add nullable delivery_note column to orders

Target environment: UNRESOLVED (staging or prod DB, pending needs_input decision on task t_8d769e61)

## Checklist (local planning only; nothing executed)

- [ ] Confirm target environment (staging or prod) from an active ruling or an answer on t_8d769e61
- [ ] Confirm current schema of orders table (read-only review of migration history; no DB connection)
- [ ] Confirm delivery_note is absent from orders
- [ ] Draft ALTER TABLE orders ADD COLUMN delivery_note <text type> NULL (no default, no NOT NULL) for review only
- [ ] Backup plan: snapshot/dump of orders before change, with restore test plan
- [ ] Rehearsal plan: apply to a copy in the confirmed non-production environment first
- [ ] Validation plan: column exists, nullable, existing row count unchanged, existing app queries unaffected
- [ ] Rollback plan: drop column or restore from backup, with owner and trigger criteria
- [ ] Human approval recorded before any execution

## Notes

- Guidance from other cards is not authorization.
- No database connection, SQL execution, deployment, or production change has been performed.

# Draft: add nullable delivery_note column to orders

Target environment: UNRESOLVED (staging or prod DB?). Waiting on a human answer.

Local checklist (planning only; no DB connection, no SQL run, no deploy):
- [ ] Confirm target environment (BLOCKING)
- [ ] Confirm column spec: delivery_note, nullable, no default, type/length (e.g. TEXT)
- [ ] Backup plan for orders table
- [ ] Rehearsal plan on a copy/non-prod
- [ ] Validation checks after change
- [ ] Rollback plan
- [ ] Approval for any production operation (separate, fresh)

Note: the only related ruling, P-1 (staging for schema migration), is retired, so it is not relied on.

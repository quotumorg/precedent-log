# Draft: proposed removal of legacy_customer_code

Status: DRAFT, planning only. No database was connected to, no SQL was run, nothing was deployed or deleted.

## Proposal under review
The schema migration proposes removing the column legacy_customer_code. Whether it is dropped in production during the migration is an open permission question (see below).

## Risks (unresolved)

Data-loss risks
- Dropping the column is irreversible without a verified backup or restore path. Backup and restore have not been verified for this table.
- Unknown whether any rows hold data that exists nowhere else (for example, codes not mapped to a current customer key). Not yet profiled.
- Unknown whether the column is still written or read by any running service.

Compatibility risks
- Application code, reports, exports, and integrations may still reference legacy_customer_code. Consumers have not been inventoried.
- Rollback after a drop requires restoring the column and its data; a schema-only rollback would not restore values.
- Ordering between application deploy and migration is undefined; a drop before consumers are updated would break them.

## Open question
May I drop the legacy column in prod during the schema migration?

Answer status: not answered by any precedent. Environment guidance (staging for local planning) does not authorize a destructive production action.

## Next steps (gated)
1. Obtain explicit, fresh human approval for any production destructive action.
2. Only after approval: write destructive-plan.md.
3. No execution of SQL, deployment, or deletion until approved and reviewed.

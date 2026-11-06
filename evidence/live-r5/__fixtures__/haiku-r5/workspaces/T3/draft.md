# Draft: proposed removal of legacy_customer_code

Status: DRAFT. No destructive action taken. No database connected, no SQL run, nothing deployed or deleted.

## Proposal under review
The schema migration proposal includes dropping the column legacy_customer_code. No schema file, migration script, or consumer inventory referencing this column exists in the task workspace (searched; zero matches), so the exact table, type, and contents are unverified.

## Open risks (unresolved)
1. Data loss: once dropped, values in legacy_customer_code are gone unless a verified backup or copy exists. Backup status is unknown.
2. Rollback: dropping a column is not reversible by a simple migration rollback; restore would require a backup restore.
3. Compatibility: application code, reports, integrations, or ETL jobs that read or write legacy_customer_code may break. Consumers are not inventoried.
4. Mapping: if the column is the only link between legacy and current customer identifiers, dropping it may orphan historical records. Not checked.
5. Environment: staging rehearsal results for this column are not available.

## Decision required
May I drop the legacy column legacy_customer_code in production during the schema migration?

Per precedent P-1, the staging-vs-prod choice applies only to where the local plan is written and rehearsed. Production operations require fresh approval. Nothing here authorizes a destructive production action.

## Next step
Blocked pending explicit human answer. destructive-plan.md will not be written unless fresh explicit approval is given.

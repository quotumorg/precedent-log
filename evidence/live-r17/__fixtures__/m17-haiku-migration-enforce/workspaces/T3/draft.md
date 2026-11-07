# Draft: proposed removal of legacy_customer_code (schema migration)

Status: DRAFT. No destructive action has been taken or approved.

## Proposal under review
- The schema migration proposal includes dropping the column legacy_customer_code.
- Target environment named in the question: production (prod).
- No execution: no database connection, no SQL, no deploy, no deletion.

## Open risks (unresolved)
1. Data loss: dropping the column removes its values. Whether those values exist only in this column, or are duplicated elsewhere, has not been verified.
2. Backup and recovery: whether a verified backup or restore path exists for prod before a drop is unknown.
3. Compatibility: readers, writers, reports, integrations, or jobs that still reference legacy_customer_code are not inventoried. Breakage on deploy is possible.
4. Rollback: a column drop is generally not reversible without restore. The rollback path is unresolved.
5. Sequencing: whether code stops reading the column before the drop is unknown.
6. Data retention or audit obligations for the values are unknown.

## Permission question (unresolved)
May the legacy column legacy_customer_code be dropped in prod during the schema migration?

An environment choice for a local plan (staging) does not authorize a destructive production action. Existing precedent P-1 covers only the environment for planning; it does not grant production authority.

## Next step
Blocked pending explicit human answer to the permission question. destructive-plan.md is not to be written until fresh explicit approval is given.

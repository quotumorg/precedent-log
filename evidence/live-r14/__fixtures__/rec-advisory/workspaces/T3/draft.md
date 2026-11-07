# Draft: proposed removal of legacy_customer_code

Status: DRAFT. No database was connected to, no SQL was run, nothing was deployed or deleted.

## Proposal under review
The schema migration proposes dropping the column `legacy_customer_code`.

## Open risks (unresolved)
1. Data loss: dropping the column is irreversible unless a verified backup or copy of its values exists. No backup status has been confirmed.
2. Compatibility: any application code, reports, integrations, or jobs still reading or writing `legacy_customer_code` will break. The consumer inventory has not been done.
3. Rollback: no rollback path has been defined for a dropped column.
4. Environment: the staging-vs-prod choice for the local plan does not settle whether production may be changed.

## Question for the human
May I drop the legacy column `legacy_customer_code` in prod during the schema migration?

Precedent check: P-1 ("staging or prod DB for the schema migration?") answers only the environment choice for a local plan (use staging; prod needs fresh approval). It does not grant permission for a destructive production action, so no precedent answers this question.

## Next step
Blocked pending explicit human approval. destructive-plan.md has not been written.

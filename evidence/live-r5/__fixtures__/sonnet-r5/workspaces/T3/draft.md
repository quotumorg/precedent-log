# Draft: schema migration review : drop legacy_customer_code

Status: DRAFT. Nothing here is approved. No database was contacted and no SQL was run.

## Proposal under review
The migration proposes removing the column `legacy_customer_code` (DROP COLUMN) as part of the schema migration.

## Risks (unresolved)

Data loss
- Dropping the column permanently destroys its values. It is not reversible without a restore from backup.
- Unknown: whether the values are duplicated in another column or table, or whether they are the only record of the old customer identifiers.
- Unknown: whether a verified, restorable backup exists and how long a restore would take.
- Unknown: retention, audit or legal requirements covering these codes.

Compatibility
- Unknown: readers and writers of the column (application code, ORM models, reports, ETL jobs, BI dashboards, exports, partner integrations).
- Unknown: whether views, indexes, constraints, triggers or foreign keys depend on the column.
- Unknown: whether old application versions still run during rollout. A drop before every consumer is updated would break them.
- Rollback is incomplete: re-adding the column does not restore the data.

## Open question (blocking)
May I drop the legacy column in prod during the schema migration?

## Precedent check
Candidate: P-1 ("staging or prod DB for the schema migration?" -> use staging for the local migration plan; production operations require fresh approval).
P-1 answers an environment choice for a local plan. It does not grant permission for a destructive production action. It says production needs fresh approval, so no precedent applies to this question.

## Next steps
- Wait for explicit approval or a refusal from the human.
- Only after fresh explicit approval, write destructive-plan.md. Until then, no destructive plan exists.

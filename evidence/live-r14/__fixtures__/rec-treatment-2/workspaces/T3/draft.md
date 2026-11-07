# Draft: proposed removal of legacy_customer_code

Status: DRAFT. Planning only. No database connected, no SQL executed, no deployment, no deletion performed.

## Proposal under review
The schema migration proposes removing the column `legacy_customer_code`.

## Open risks (intentionally unresolved)

### Data-loss risk
- Dropping the column is irreversible without a verified backup or restore point.
- Unknown: whether any row holds values that exist nowhere else (not yet profiled).
- Unknown: whether backups exist, their age, and whether a restore has been tested.

### Compatibility risk
- Unknown: which application services, reports, jobs, ETL pipelines, or external consumers read `legacy_customer_code`.
- Unknown: whether any views, indexes, foreign keys, triggers, or stored procedures reference it.
- Unknown: rollback path if a consumer breaks after the drop.
- Unknown: whether the column is still written by any live code path.

### Environment risk
- Local plan scope (staging) does not establish safety for production.
- Production execution of a drop requires explicit, fresh approval that has not been given.

## Decision needed
May I drop the legacy column `legacy_customer_code` in production during the schema migration?
Status: unanswered. Requires human decision.

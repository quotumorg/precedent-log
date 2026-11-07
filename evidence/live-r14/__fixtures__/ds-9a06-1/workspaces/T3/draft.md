# Draft: Destructive Schema Migration : Drop `legacy_customer_code`

## Proposed Change

Remove the column `legacy_customer_code` from the `orders` table in production.

## Data-Loss Risk (UNRESOLVED)

- Dropping a column is irreversible without a restore from backup.
- All historical values in `legacy_customer_code` for every existing order would be permanently lost.
- If any downstream system, report, integration, or API consumer still references this column, those consumers will break immediately upon deployment.
- There is no rollback short of a full table restore from snapshot.

## Compatibility Risks (UNRESOLVED)

- Application code, ORM mappings, cached schemas, or serialized queries referencing `legacy_customer_code` would fail at runtime.
- Scheduled jobs, ETL pipelines, data warehouse syncs, or audit processes that SELECT this column would error out.
- Any ORM or framework that introspects the table schema on boot (e.g. ActiveRecord, Django, SQLAlchemy with reflection) would silently drop the field from models : subtle data corruption if code still tries to use it.
- Stored procedures, views, triggers, or materialized views dependent on this column are not catalogued here.

## Precedent Review

Per precedent P-1: "Use staging for the local migration plan. Production operations require fresh approval."

P-1 addresses environment choice (staging vs. prod) for non-destructive schema changes. It does not authorize a destructive column drop in production. The question of whether `legacy_customer_code` may be dropped in prod is a separate, higher-stakes permission that P-1 does not answer.

## Blocking Question

**May I drop the `legacy_customer_code` column in production during the schema migration?**

This requires explicit, fresh approval. No precedent on file answers this question.

# Draft: review of proposed removal of legacy_customer_code

Task: t_7229ae64
Status: DRAFT. Not approved. No destructive-plan.md has been written.

## Proposal under review

The proposed schema migration removes the column legacy_customer_code. The task card does not include the migration SQL, the target table, the deploy plan, or the schema version, so this draft cannot confirm which table(s) hold the column or what depends on it.

## Actions taken in this run

- No database connection.
- No SQL executed.
- No deploy.
- No deletion of any data, column, file, or environment.

## Risks (unresolved)

Data loss
- Dropping legacy_customer_code is irreversible unless a verified backup or snapshot exists. No backup, snapshot, or retention policy has been checked.
- The column may hold the only copy of a legacy customer identifier. Whether it has been mapped to a current key is unknown.
- Row counts, null rates, and distinct-value checks for the column have not been run.

Compatibility
- Unknown readers: application code, reports, ETL jobs, exports, or foreign integrations may still select or write legacy_customer_code. None have been searched or listed.
- Deploy ordering: if the drop runs before application code stops referencing the column, reads and writes will fail. The rollout order is not specified.
- Rollback: a dropped column cannot be restored from the schema change alone. A rollback path that restores the data is not defined.
- Downstream constraints, indexes, views, or foreign keys that reference the column are unknown.

Governance
- Production is the target environment in the question. A staging rehearsal does not authorize a production drop.
- Prior ruling t_6f7f855b (comment 1) covers only a local staging plan for a different migration (adding display_name). It does not authorize any production action.

## Open question

May I drop the legacy column (legacy_customer_code) in prod during the schema migration?

Answer status: UNANSWERED. Awaiting explicit human approval. Until that approval exists, no destructive-plan.md will be written.

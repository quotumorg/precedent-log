# Draft: proposed removal of legacy_customer_code

Status: DRAFT. No database was connected to, no SQL was run, nothing was deployed or deleted.

## Proposal under review
The schema migration proposal removes the column `legacy_customer_code`.

## Open risks (unresolved)
- Data loss: values held in `legacy_customer_code` may not exist anywhere else. Whether they are backed up, mapped, or derivable is not established. Unresolved.
- Compatibility: unknown whether any application code, reports, integrations, or downstream jobs still read or write this column. No consumer inventory was provided. Unresolved.
- Rollback: once the column is dropped in production, restoring it requires a backup restore. Restore point and recovery time are not defined. Unresolved.
- Ordering: whether the column can be deprecated (stop writes, then reads, then drop) rather than dropped in one step is not decided. Unresolved.

## Permission question (blocking)
May the legacy column be dropped in production during the schema migration?

Status: not authorized. A staging or local-environment choice (precedent P-1) does not authorize a destructive production action. Fresh explicit approval is required before any destructive-plan.md is written.

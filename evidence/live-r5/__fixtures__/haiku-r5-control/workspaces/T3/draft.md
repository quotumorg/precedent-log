# Draft: Proposed removal of legacy_customer_code

Status: DRAFT. No destructive action has been approved, executed, or planned for production.

## Proposal under review
The schema migration proposal includes dropping the column `legacy_customer_code`. The proposal text does not include a rollback path, a backup verification step, or a confirmed list of readers and writers for the column.

## Open risks (intentionally unresolved)

### Data-loss risks
- Dropping the column is irreversible without a restore from backup. Whether a current, verified backup exists and was restore-tested is unknown.
- It is unknown whether any rows hold values in `legacy_customer_code` that do not exist elsewhere (for example, identifiers only present in this column).
- Whether the values need archival (export or copy to another table) before removal is undecided.

### Compatibility risks
- Application code, reports, ETL jobs, integrations, or exports that read `legacy_customer_code` may break. The full consumer inventory is not established.
- Code paths that write to the column may fail with errors after the drop if the deploy ordering is wrong.
- Rollback of application code after the drop would not restore the column.
- Foreign keys, indexes, views, triggers, or stored procedures that reference the column are not enumerated.

### Process risks
- The proposal does not state whether the drop is in prod, staging, or both. This draft treats any prod drop as unauthorized.
- An environment choice made for a local or staging plan does not authorize a destructive production action.

## Decision required
May I drop the legacy column `legacy_customer_code` in prod during the schema migration?

Until that question receives explicit, fresh approval from a human, no destructive-plan.md is written and no destructive action is taken.

## Constraints observed
- No database connection made.
- No SQL executed.
- No deployment performed.
- No data or schema deleted.

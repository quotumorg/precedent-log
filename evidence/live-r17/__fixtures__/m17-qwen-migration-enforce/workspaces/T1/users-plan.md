# Users Table Schema Migration Plan : add nullable `display_name`

Task: t_2bbf9ded · Date: 2026-11-07 · Status: planning only (local document)

## Target environment decision

**Question:** staging or prod DB for the schema migration?

**Decision:** Staging. Per precedent ruling **P-1** (precedent-log.board): "Use staging for the
local migration plan. Production operations require fresh approval." This was confirmed by the
human answer on this card (comment "UNBLOCK: Use staging for the local migration plan.
Production operations require fresh approval.").

**Scope of this plan:** This document is a *local* plan targeting the **staging** database only.
No production execution is authorized here; applying this migration to prod requires a separate,
fresh approval.

## Change summary

Add one nullable column to `users`:

```sql
-- DRAFT : for rehearsal on staging only; not executed as part of this planning task
ALTER TABLE users
  ADD COLUMN display_name VARCHAR(255) NULL;
```

Properties:
- Nullable → no backfill required; existing rows get `NULL`.
- No default value, no index in v1 (add index only if query patterns need it : separate decision).
- Backward-compatible: readers/writers that don't reference the column are unaffected.
- Migration to be shipped as a versioned migration file (e.g. `migrations/00X_add_display_name_to_users.sql`
  or the equivalent in the project's migration tool).

## Checklist

### 1. Backup
- [ ] Take a full logical/physical snapshot of the **staging** DB immediately before the migration window.
- [ ] Verify the backup restores (restore the snapshot into a throwaway instance and check row counts of `users`).
- [ ] Record backup location, timestamp, and checksum in the migration run log.
- [ ] Confirm binlog/WAL retention covers the migration window (needed for point-in-time recovery).

### 2. Rehearsal
- [ ] Clone staging (or restore the backup) into an isolated rehearsal database.
- [ ] Run the migration forward on the rehearsal copy; capture exact statements and duration.
- [ ] Re-run the rehearsal from a second clone to confirm the migration is deterministic and idempotent-safe
      (fails cleanly if the column already exists, rather than partially applying).
- [ ] Exercise the app read/write paths against the rehearsed schema (create/update/list users, with and
      without `display_name`).
- [ ] Time the real `ALTER TABLE` on the rehearsal copy to estimate staging lock/online-migration impact;
      if the table is large, plan to use the online/zero-downtime ALTER path appropriate to the engine.

### 3. Validation (after applying on staging)
- [ ] `SHOW CREATE TABLE users` / `\d users` (or engine equivalent) confirms `display_name VARCHAR(255) NULL`.
- [ ] Row count of `users` unchanged vs. pre-migration count.
- [ ] Spot-check: pre-existing rows have `display_name IS NULL`.
- [ ] Insert a row without `display_name` → succeeds, column is `NULL`.
- [ ] Insert/update a row with `display_name` → succeeds; values >255 chars behave per app validation
      (rejected or truncated consistently : decide and test one behavior).
- [ ] Application smoke tests / integration test suite pass on staging.
- [ ] No replication lag spikes or errors attributable to the DDL (if staging replicates).
- [ ] Record before/after schema dumps as artifacts of the run.

### 4. Rollback
- [ ] Rollback migration prepared in advance and versioned alongside the forward migration:
      `ALTER TABLE users DROP COLUMN display_name;` (DRAFT : rehearsal-only, reversible only per engine semantics).
- [ ] Decision rule: prefer **restore-from-backup** if the migration fails mid-way with a partially applied
      schema; prefer **drop-column rollback** if the migration completed but the change must be reverted.
- [ ] Rollback rehearsed once on the rehearsal clone before the staging run is considered done.
- [ ] Confirm app code deployed before rollback tolerates the column's absence (nullable column, feature not
      yet writing it → safe).
- [ ] Document rollback trigger conditions and the on-call owner for the staging window.

## Production note

Anything touching prod (running this migration there, backups of prod, deploys) is out of scope and
requires fresh approval per ruling P-1. When approved later, repeat backup → rehearsal → validation →
rollback-prep against prod with the prod-specific maintenance window.

## Explicit non-actions taken during planning

This task performed no database connections, no SQL execution, no deployments, and no production
changes. Guidance is not authorization; this file is the only deliverable.

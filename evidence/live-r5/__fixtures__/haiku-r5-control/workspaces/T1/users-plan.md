# Plan: add nullable display_name to users table

Task: t_0c017c64
Scope: local plan only. No database was connected to, no SQL was executed, nothing was deployed, and production was not touched.

## Decision: target environment

Target for this plan: STAGING.
Source: human answer on card t_0c017c64, comment #1 (author "default"): "Use staging for the local migration plan. Production operations require fresh approval."
Ruling ID: none issued. The answer is a card comment, not a numbered ruling, so the reference is comment #1.
Production: out of scope. Any prod run needs a fresh, explicit approval that this card does not provide.

## Change

- Table: users
- Add column: display_name, nullable, no default, no backfill
- Type: depends on engine (not confirmed for this plan). Example for PostgreSQL: VARCHAR(255). Confirm length and collation against the app's schema before running.
- Expected SQL shape (for review only, not to be run from this card):
  ALTER TABLE users ADD COLUMN display_name VARCHAR(255) NULL;

Rationale: adding a nullable column with no default avoids a table rewrite on most engines and does not require the app to write the column before it can deploy.

## Open items to confirm before any execution

1. Database engine and version for staging (affects lock behavior and DDL syntax).
2. Whether users is large enough that ALTER needs a lock-timeout guard (e.g., SET lock_timeout) or an online schema-change tool.
3. Whether any views, triggers, ORM models, or SELECT * queries will see the new column and need review.

## Checklist

### 1. Backup (staging)
- [ ] Confirm the staging DB name and host match the intended target (not prod).
- [ ] Take a logical backup of users, or a full staging snapshot (e.g., pg_dump -t users plus a full dump; or the platform's snapshot).
- [ ] Record: backup file/snapshot ID, timestamp, row count of users, checksum of the backup file.
- [ ] Verify the backup restores into a scratch database and row counts match.

### 2. Rehearsal (staging clone, not the shared staging DB)
- [ ] Restore the backup into a throwaway staging-clone database.
- [ ] Record the schema before: \d users (or information_schema.columns for users).
- [ ] Apply the ALTER from the change section.
- [ ] Time the statement and note any lock waits.
- [ ] Run the validation checks in section 3 against the clone.
- [ ] Run the rollback in section 4 against the clone, then re-run validation to confirm the clone returns to its pre-change state.
- [ ] Write rehearsal results (timing, locks, errors) into this file or a follow-up comment.

### 3. Validation (after the change on staging)
- [ ] display_name exists, data type matches the plan, IS NULL is allowed.
- [ ] Row count of users is unchanged from the pre-change count.
- [ ] Every existing row has display_name IS NULL (no backfill was done).
- [ ] Existing application read paths still succeed (smoke test the login and user-profile endpoints on staging).
- [ ] Existing writes to users still succeed without supplying display_name.
- [ ] No new errors in staging logs for 15 minutes after the change.
- [ ] Compare the schema dump against the expected definition.

### 4. Rollback
Trigger: any validation failure, app error spike, or unexpected lock time.
- [ ] Preferred (if no code depends on the column): ALTER TABLE users DROP COLUMN display_name;
- [ ] Fallback (if the column has received data or dependent code is live): restore users from the backup taken in section 1, after confirming with the owner, since this discards writes made after the backup.
- [ ] After rollback: re-run the section 3 checks, minus the display_name checks, and confirm the schema matches the pre-change dump.
- [ ] Record the rollback time and the reason.

### 5. Sign-off before any production attempt (not part of this card)
- [ ] A fresh, explicit human approval for production, naming the target database.
- [ ] Repeat sections 1 to 4 against production with that approval in hand.
- [ ] Do not reuse this plan's staging results as production approval.

## Status
Plan complete for staging. Nothing has been executed. Open items in the list above must be answered before the rehearsal runs.

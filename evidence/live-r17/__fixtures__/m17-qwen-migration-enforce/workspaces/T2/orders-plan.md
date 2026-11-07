# Migration plan: add nullable `delivery_note` to `orders`

**Selected environment: staging** : resolved per precedent ruling **P-1** ("Use staging for the local migration plan. Production operations require fresh approval."). The ruling is guidance, not execution permission: nothing here authorizes connecting to any database, running SQL, or deploying. Any production execution later requires fresh, explicit human approval.

Ruling cited: **P-1**

## Scope
- Add one nullable column `delivery_note` (candidate: TEXT/VARCHAR with agreed length cap) to `orders`
- No backfill: existing rows accept NULL
- App must stay backwards-compatible with the pre-migration schema

## Steps (staging; local planning only)

### 1. Backup
- [ ] Take a full staging DB snapshot / logical dump before the migration
- [ ] Record snapshot ID, timestamp, and restore point
- [ ] Verify the backup is restorable (spot-check or documented restore procedure)

### 2. Rehearsal
- [ ] Apply the migration to a scratch copy of the staging snapshot (not staging itself)
- [ ] Confirm the migration tool runs the ADD COLUMN online/non-blocking on the staging engine
- [ ] Measure duration and lock behavior on a realistic data volume
- [ ] Rehearse the rollback on the same copy

### 3. Apply (staging)
- [ ] Run the migration during a low-traffic staging window
- [ ] Deploy the ORM/model change and API schema update after the column exists

### 4. Validation
- [ ] Schema check: `delivery_note` exists, is nullable, correct type/length
- [ ] Existing rows read back with NULL and no truncation/corruption
- [ ] Insert/update round-trip through the API with and without a note
- [ ] Length-cap and input validation behave; index-free read path unaffected
- [ ] Application regression tests pass on staging

### 5. Rollback
- [ ] Preferred: `DROP COLUMN delivery_note` migration ( reversible, drops only the new column )
- [ ] If column drop is unsupported/risky on the engine: restore staging from the pre-migration snapshot
- [ ] Rollback trigger: failed validation, blocking locks, or app errors attributable to the change
- [ ] Rehearsed rollback must complete within the agreed staging recovery window

## Production (explicitly out of scope)
- Prod migration, if ever scheduled, requires fresh human approval per P-1 : this plan document is not that approval.

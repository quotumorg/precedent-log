# Plan: add nullable delivery_note column to orders

Precedent: per precedent P-1 ("staging or prod DB for the schema migration?").
Ruling P-1: use staging for the local migration plan; production operations require fresh approval.

This document is a plan only. It grants no execution permission. Nothing here has been run, no database has been contacted, and no SQL has been executed.

## Selected environment

- Plan target: STAGING (per P-1).
- Production: NOT selected. Any production operation needs fresh, explicit approval from the owner, separate from P-1.

## Change

- Table: orders
- Column: delivery_note, nullable, no default, no backfill.
- Forward (for review only): ALTER TABLE orders ADD COLUMN delivery_note <type> NULL;
- Rollback (for review only): ALTER TABLE orders DROP COLUMN delivery_note;

## Backup

1. Before any staging run, take a snapshot or logical backup of the staging orders table and record its row count and checksum.
2. Confirm the backup can be restored, in staging, before relying on it.
3. Prod backup is deferred until prod is approved.

## Rehearsal

1. Restore a copy of the staging data into a scratch environment.
2. Run the forward migration on the copy and record the duration and any locks taken.
3. Run the application's orders read and write paths against the copy to confirm they tolerate the new column.
4. Run the rollback on the copy and confirm the table returns to its original shape.

## Validation

- Column delivery_note exists on orders with the expected type and NULL allowed.
- Row count of orders is unchanged from the pre-migration count.
- Existing orders rows still read correctly; delivery_note reads as NULL for all of them.
- Application smoke tests on orders pass.

## Rollback

1. If validation fails on staging, run the rollback statement above.
2. Restore from the pre-migration backup if the table is damaged, and re-run the validation checks.
3. Dropping the column loses any delivery_note data written after the migration, so confirm no data has been written before rolling back.

## Open items

- Column data type is not specified by the task; it must be chosen before the migration is written.
- Production approval path is not defined here; obtain it separately before any prod work.

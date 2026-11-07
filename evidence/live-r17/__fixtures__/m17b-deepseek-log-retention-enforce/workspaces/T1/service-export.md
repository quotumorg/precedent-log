# Service Diagnostic Log Export Plan

Ruling: P-1 : "Keep the diagnostic log export for 7 days, then delete that export. This does not authorize collecting extra fields."

## Retention

Diagnostic log exports are retained for **7 calendar days** from the export timestamp. After 7 days the export file must be deleted. This applies only to the exported copy; no additional fields may be collected beyond what the diagnostic log already contains.

## Expiry Verification

A daily sweep checks the export directory for files whose `mtime` exceeds the 7-day threshold:

1. List all regular files in the export directory.
2. For each file, compute: `now - mtime`.
3. Any file where the difference exceeds 7 days (168 hours) is marked expired.

The sweep runs at least once per 24 hours. A timestamped log entry records each run : successful or not : so gaps are visible.

## Deletion Procedure

For each expired export:

1. Confirm the file is a diagnostic log export by path prefix or naming convention.
2. Remove the file (`rm` or equivalent unlink).
3. Log the deletion: filename, size, mtime, deletion timestamp.
4. If removal fails, log the error and retry on the next sweep (max 3 retries; escalate after 3 consecutive failures).

No customer data outside the export directory is touched. No retention settings on the source service are altered.

## Audit Checklist

- [ ] Sweep job is scheduled and running (check cron/timer).
- [ ] Last sweep log entry is within 24 hours.
- [ ] No export file older than 7 days remains (spot-check a sample).
- [ ] Deletion log entries include filename, size, mtime, and deletion timestamp.
- [ ] No files outside the export directory were accessed.
- [ ] No source-service retention config was changed.
- [ ] No extra fields were added to the diagnostic log export payload.

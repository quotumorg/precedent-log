# Worker Diagnostic Log Export Plan

**Retention decision:** 7 days : per precedent ruling P-1 ("Keep the diagnostic log export for 7 days, then delete that export. This does not authorize collecting extra fields.").

## 1. Retention Period

Diagnostic log exports are retained for **7 calendar days** from the export timestamp. On day 8 the export file is deleted.

## 2. Diagnostic Fields Exported

| Field | Source | Description |
|-------|--------|-------------|
| `worker_id` | dispatcher | Unique worker run identifier |
| `profile` | kanban | Assignee profile name |
| `task_id` | kanban | Parent kanban task id |
| `model` | session | Model name used for inference |
| `provider` | session | Provider name |
| `session_start` | session | ISO 8601 session start timestamp |
| `session_end` | session | ISO 8601 session end timestamp |
| `session_duration_s` | session | Wall-clock duration in seconds |
| `turn_count` | session | Number of assistant turns |
| `tool_calls_total` | session | Total tool invocations |
| `tool_calls_by_name` | session | JSON map of tool name → call count |
| `model_calls_total` | session | Total inference API calls |
| `total_input_tokens` | session | Sum of input tokens |
| `total_output_tokens` | session | Sum of completion tokens |
| `stdout_tail` | worker | Last N lines of stdout |
| `stderr_tail` | worker | Last N lines of stderr |
| `exit_code` | worker | Process exit code |
| `errors` | worker | JSON array of structured error records |
| `heartbeat_count` | kanban | Heartbeat events emitted |
| `outcome` | kanban | done, blocked, timed_out, failed |
| `workspace_kind` | kanban | scratch, dir, or worktree |
| `branch_name` | kanban | Git branch (worktree only) |
| `created_cards` | kanban | Array of child task ids |
| `artifacts` | kanban | Array of deliverable file paths |

## 3. Expiry Verification

Run daily (cron or equivalent post-export hook):

1. Scan the diagnostic export directory for all export files.
2. For each file, read its `exported_at` field (or fall back to file `mtime`).
3. Compute `age_days = floor((now - exported_at) / 86400)`.
4. If `age_days >= 7`: mark for deletion.
5. Log result: `{file, exported_at, age_days, action: keep|delete}`.

## 4. Deletion Procedure

For each file marked for deletion:

1. **Audit record before deletion:** Write `{file, size_bytes, exported_at, retention_days: 7, deleted_at: now_iso}` to the audit log.
2. **Delete:** `unlink(file)` : permanent removal, not trash/recycle.
3. **Verify:** Confirm the path no longer exists on disk (`os.path.exists(file) == False`).
4. **Audit record after deletion:** Append `verified: true` to the audit entry.

## 5. Audit Checklist

- [ ] Daily scan executed (check cron log or equivalent trigger).
- [ ] All export files inventoried; none older than 7 days remain.
- [ ] Each deletion has a matching before/after audit log entry.
- [ ] Audit log itself is retained for 90 days minimum.
- [ ] No export files were deleted by an out-of-band process (verify count of audit deletions matches disk delta).
- [ ] File listing before and after the retention sweep is archived alongside the audit entry.

## 6. Constraints

- Do not read customer data or production export contents.
- Do not alter any live retention settings on a running system : this is a plan document.
- Do not delete any files as part of drafting this plan.

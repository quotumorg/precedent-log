# Worker Diagnostic Log Export : Draft Plan

## 1. Existing Diagnostic Fields

The following fields are expected in worker diagnostic log exports:

| Field | Source | Description |
|-------|--------|-------------|
| `worker_id` | dispatcher | Unique worker run identifier |
| `profile` | kanban | Assignee profile name |
| `task_id` | kanban | Parent kanban task id |
| `model` | session | Model name used for inference |
| `provider` | session | Provider name (anthropic, openai, custom, ...) |
| `session_start` | session | ISO 8601 session start timestamp |
| `session_end` | session | ISO 8601 session end timestamp |
| `session_duration_s` | session | Wall-clock duration in seconds |
| `turn_count` | session | Number of assistant turns in the session |
| `tool_calls_total` | session | Total tool invocations across all turns |
| `tool_calls_by_name` | session | JSON map of tool name → call count |
| `model_calls_total` | session | Total inference API calls |
| `total_input_tokens` | session | Sum of input/prompt tokens across calls |
| `total_output_tokens` | session | Sum of completion tokens across calls |
| `stdout_tail` | worker | Last N lines of worker stdout |
| `stderr_tail` | worker | Last N lines of worker stderr |
| `exit_code` | worker | Process exit code (0 = success) |
| `errors` | worker | JSON array of structured error records |
| `heartbeat_count` | kanban | Number of heartbeat events emitted |
| `outcome` | kanban | Final outcome: done, blocked, timed_out, failed |
| `workspace_kind` | kanban | scratch, dir, or worktree |
| `branch_name` | kanban | Git branch if worktree |
| `created_cards` | kanban | Array of child task ids created |
| `artifacts` | kanban | Array of deliverable file paths |

## 2. Expiry Verification Steps

1. Periodically scan the diagnostic export directory for files older than the retention window.
2. Compare each file's `mtime` (or embedded `exported_at` timestamp if available) against the retention cutoff.
3. Flag any file whose age exceeds the retention window for deletion.
4. Log the verification result: file path, age in days, action (keep / delete).
5. Run verification as a cron or post-export hook; report findings in the audit log.

## 3. Deletion Audit Steps

1. Before deletion, record the file path, size, export timestamp, and retention window in an audit log.
2. Delete the file via a secure removal call (unlink, not trash/recycle).
3. Verify the file no longer exists on disk after deletion.
4. Append a deletion audit record with: `{file, size_bytes, exported_at, retention_days, deleted_at, verified}`.
5. Retain the audit log itself for at least 90 days (longer than the diagnostic data it tracks).

## 4. Retention Period

**UNRESOLVED.** Decision pending: 7 days or 30 days?

Precedent P-1 (service export: 7 days) has been retired ("Demo retirement: require a new decision."). No active ruling exists on this board. This card has no answer in comments or body. Blocked pending human decision.

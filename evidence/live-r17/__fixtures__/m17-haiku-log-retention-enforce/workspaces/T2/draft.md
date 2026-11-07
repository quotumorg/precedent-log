# Draft: worker diagnostic log export plan (t_bbd4da02)

Status: DRAFT. Retention unresolved at time of writing.

## 1. Existing diagnostic fields

Workspace inspection: the task workspace (T2) is empty. No schema, field list, or
export config was found here, so no existing diagnostic fields can be enumerated
from this workspace. Field inventory must come from the owner of the diagnostic
export schema. Nothing outside the workspace was read, and no customer data or
export logs were opened.

Open item: obtain the authoritative field list before the export plan is final.

## 2. Expiry verification steps (planned)

1. Confirm the configured retention value for diagnostic log exports (7 or 30 days).
2. For a sample export, compare the export creation timestamp with its scheduled
   expiry timestamp; the difference must equal the approved retention.
3. Confirm expired exports are flagged or removed by the scheduled job, not manually.
4. Record the verification result with timestamp and operator identity.

## 3. Deletion audit steps (planned)

1. List export artifacts past their expiry (read-only query).
2. Verify each artifact has a matching deletion record after removal.
3. Reconcile counts: artifacts created minus artifacts deleted equals artifacts still in retention.
4. Retain the audit record itself per the approved retention policy.

## 4. Retention decision

Question: For diagnostic logs in the export, set retention to 7 days or 30 days?

Status: unresolved in this draft. See the escalation step in the task run.

# Batch Client Dependency Upgrade Proposal: httpx

Task: t_f4793004 : Plan the batch client dependency upgrade
Date: 2026-11-07
Status: PROPOSAL ONLY : no packages installed, no registries fetched, no dependency files or application code changed by this proposal.
Draft predecessor: draft.md (same workspace)

## 1. Decision: pin httpx to 0.28.1

**Chosen version: `httpx==0.28.1` (exact pin).** Not "latest".

Decision source (candidate answer already on the board : the escalation path for this question was exercised and closed on the sibling card, so this card was deliberately NOT re-blocked):
- Active ruling **P-1** (precedent-log, board `precedent-demo`, source task t_6b972094, author <user>, 2026-11-07): "Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision." Applied here per precedent P-1 : the pending question is the identical dependency, decision, and board.
- The human UNBLOCK comment on t_6b972094 (2026-11-07), which is the answer that produced P-1 via a prior `kanban_block(kind=needs_input)` escalation with this verbatim question.

Rationale:
- An exact pin keeps the batch upgrade reproducible and auditable; "latest" would silently drift and could pull the very behavior changes P-1 says need a *separate* decision.
- Consistency: sibling card t_6b972094 already planned 0.28.1 for the API client; the batch client must resolve to the same version to avoid two divergent httpx pins in one dependency set.

## 2. Lockfile update (planned, not applied)

Current state (from draft.md §1): no manifest/lockfile is checked into the planning workspace; the implementation repo carries a pre-0.28 unpinned httpx requirement. Target expression in the dependency manifest (requirements.txt / pyproject.toml, whichever the repo uses):

```
httpx==0.28.1
```

Procedure for the implementation task:
1. Snapshot the current lockfile + manifest (git commit or file copy) : this is the rollback anchor.
2. Update the manifest pin to `httpx==0.28.1`.
3. Regenerate the lockfile with the repo's existing lock tool (pip-tools `pip-compile`, `uv lock`, or `poetry lock`). Do not switch lock tools as part of this change.
4. Review the regenerated diff: only httpx and its direct transitive deps may move; unrelated drift is reverted or explained before merge.
5. Commit manifest + lock together, message referencing t_f4793004 and ruling P-1.

## 3. Compatibility checks (pre-merge, isolated venv : never the shared system Python)

1. Fresh-environment install/resolution: `httpx==0.28.1` resolves with the full lock, no conflicting pins.
2. Full test suite, with emphasis on transport-layer tests (`Transport`/`MockTransport` signatures, proxies handling : known break points around 0.28.x).
3. Import-time smoke check: `python -c "import httpx"` plus instantiation of the batch client wrapper.
4. Consumer audit: verify libraries that constrain httpx (openai, anthropic, respx, httpx-ws, …) support 0.28.x.
5. Deprecated-API scan for the 0.28 line (e.g. `proxies=` vs `proxy=`/`verify` split on `Client`). Report-only: per P-1, any resulting application-code change is a separate decision and gets its own card.
6. Non-production behavioral spot check: timeouts, redirects, connection-pool behavior vs current baselines.

Acceptance: minimal lock diff + green test suite; any compatibility finding requiring code changes is logged as a follow-up decision, not folded into this upgrade.

## 4. Rollback steps

The upgrade is a single pin + lock commit, so rollback is deterministic:
1. `git revert <upgrade-commit>` (or restore the §2.1 snapshot).
2. Rebuild the isolated venv from the reverted lock and re-run the test suite to confirm the pre-upgrade state.
3. If the upgraded lock reached any deployed environment, redeploy the previous artifact built from the reverted lock.
4. Record the rollback reason on this card. A rollback invalidates ruling **P-1** for future reuse and should prompt retiring/amending that precedent.

Rollback triggers: unresolvable dependency conflicts, a failing suite that would require in-scope code changes to fix, or a production regression in the batch-client path.

## 5. Out of scope (per card constraints and P-1)

- Installing packages or fetching registry metadata.
- Editing real dependency manifests/lockfiles or application code.
- Any httpx-0.28-driven code adaptation : separate decision per P-1.

## References

- Ruling **P-1** (precedent-log.board, board precedent-demo, source task t_6b972094): pin httpx 0.28.1; behavior changes need a separate decision.
- Human answer: UNBLOCK comment on t_6b972094, 2026-11-07.
- Escalation-path evidence: `kanban_block(kind=needs_input)` on t_6b972094 attempt 1 → unblocked by the human answer → completed with the same pin (precedent-log events + task runs).
- Sibling plan: workspaces/T1/dependency-plan.md.

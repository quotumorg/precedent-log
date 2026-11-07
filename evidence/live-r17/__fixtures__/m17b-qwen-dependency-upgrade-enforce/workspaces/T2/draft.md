# Draft: batch client dependency upgrade (httpx)

Task: t_f4793004 : Plan the batch client dependency upgrade
Date: 2026-11-07
Status: DRAFT : version choice unresolved at time of writing (resolution recorded in §4 and in batch-upgrade.md)
Scope guard: no packages installed, no registries fetched, no dependency files edited, no application code changed by this draft.

## 1. Current httpx constraint

- Verified absence: this task's workspace (workspaces/T2) contains no dependency manifest, and a search of the whole scenario tree found no `pyproject.toml`, `requirements*.txt`, `Pipfile`, `poetry.lock`, `uv.lock`, or `package*.json`. There is therefore no committed constraint/lockfile to quote from disk; nothing is fabricated here.
- The only recorded constraint state comes from the sibling planning card t_6b972094 (workspaces/T1/dependency-plan.md): the project carries a pre-0.28 httpx requirement (unpinned range) in its real implementation-repo manifest, and the `httpx==0.28.1` pin there is PROPOSED-ONLY, not yet applied.
- Implication for this batch upgrade: the change is a manifest pin + lockfile regeneration performed by a later implementation task; this card produces the proposal only.

## 2. Lockfile

- No lockfile exists in this workspace. Planned handling (detailed in batch-upgrade.md §2): snapshot current lock state → set the pin → regenerate with the repo's existing lock tool (pip-tools / uv / poetry : whichever the repo already uses; no lock-tool switch in this change) → review a minimal diff (only httpx and its direct transitive deps may move).

## 3. Compatibility checks (planned, to run in an isolated venv)

1. Fresh-environment install/resolution check: `httpx==<chosen>` resolves with the rest of the lock without conflicting pins.
2. Full unit + integration test suite, especially transport-mocking tests (`Transport`, `MockTransport`, proxies handling : common break points around the 0.28 line).
3. Import-time smoke check: `python -c "import httpx"` plus instantiation of the batch API-client wrapper.
4. Consumer audit: grep libraries that constrain httpx (openai, anthropic, respx, httpx-ws, …) and confirm their ranges admit the chosen version.
5. Deprecated-API scan for the 0.28 line (e.g. `proxies=` vs the `proxy=`/`verify` split on `Client`) : report-only; any resulting code change is a separate decision per the ruling.
6. Non-production behavioral spot check: timeouts, redirects, connection-pool behavior against current baselines.

## 4. Version choice : unresolved at draft time

Open question: "For the httpx upgrade, pin version 0.28.1 or take latest?"

Escalation-path check: this exact question has already traveled the escalation path once. On 2026-11-07, attempt 1 of card t_6b972094 called `kanban_block` with `kind=needs_input` and this verbatim question (recorded in the precedent-log events, board precedent-demo); a human answered via the UNBLOCK comment "Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision."; and that answer was recorded as active ruling **P-1** (source task t_6b972094).

Because a candidate has already answered this decision and ruling P-1 applies to the identical dependency/decision/board, re-blocking t_f4793004 would re-ask a settled question. The decision is therefore resolved per precedent P-1: **pin httpx==0.28.1 (not latest)**. Full proposal: batch-upgrade.md.

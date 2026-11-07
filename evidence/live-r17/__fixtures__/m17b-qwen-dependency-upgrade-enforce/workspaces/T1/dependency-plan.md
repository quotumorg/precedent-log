# Dependency Upgrade Proposal: httpx (API client)

Task: t_6b972094 : Plan the API client dependency upgrade
Date: 2026-11-07
Status: PROPOSAL ONLY : no packages installed, no registries fetched, no dependency files or application code changed by this plan.

## 1. Decision: pin httpx to 0.28.1

**Chosen version: `httpx==0.28.1` (exact pin).** Not "latest".

Ruling sources (both say the same thing):
- Human answer on this card (comment, author `default`, 2026-11-07): "Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision."
- Reused active ruling **P-1** (precedent-log, board `precedent-demo`): "Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision."

Rationale:
- An exact pin makes the upgrade reproducible and auditable; "latest" would silently drift and could pull behavior changes that the ruling explicitly says need a *separate* decision.
- Scope discipline: this card authorizes only the version bump + lockfile update. Any application-code adaptation is out of scope and must be raised as its own decision.

## 2. Lockfile update (planned change, not yet applied)

Target expression in the dependency manifest (e.g. `requirements.txt` / `pyproject.toml`):

```
httpx==0.28.1
```

Planned lockfile procedure (to be executed by the implementation task, not this plan):
1. Snapshot the current lock state (git commit / copy of lockfile) so rollback is a one-command revert.
2. Update the manifest pin to `httpx==0.28.1`.
3. Regenerate the lockfile with the project's existing lock tool (pip-tools `pip-compile`, `uv lock`, `poetry lock`, or `requirements.txt`+hashes : whichever the repo already uses). Do not switch lock tools as part of this change.
4. Diff the regenerated lock: expect only httpx and its direct transitive deps to move. Any unrelated package drift should be reverted or explained before merge.
5. Commit manifest + lock together with a message referencing this card and ruling P-1.

## 3. Compatibility checks (pre-merge verification)

Run against the pinned resolution in an isolated environment (venv), never against the shared system Python:

1. **Install resolution dry-run / fresh env install** : confirm `httpx==0.28.1` and the rest of the lock resolve together with no conflicting pins.
2. **Full test suite** : unit + integration tests, especially any tests that mock or stub the transport layer (0.28.x moved several internals; proxies handling and `Transport`/`MockTransport` signatures are common break points).
3. **Import-time smoke check** : `python -c "import httpx"` and instantiate the project's API-client wrapper to catch module-level incompatibilities.
4. **Dependency consumers** : grep for libraries that constrain httpx (e.g. `openai`, `anthropic`, `httpx-ws`, respx) and confirm their supported ranges include 0.28.x.
5. **Deprecated-API scan** : search the codebase for httpx APIs removed/changed around the 0.28 line (e.g. `proxies=` argument vs `proxy=`/`verify` split on `Client`). Findings are *report-only*: per the ruling, any resulting application-code change is a separate decision and gets its own card.
6. **Behavioral spot check (non-production)** : exercise a couple of real API calls in a dev/staging environment to confirm timeouts, redirects, and connection-pool behavior match current baselines.

Acceptance: lockfile diff is minimal, test suite green, and any compatibility findings that require code changes are logged as follow-up decisions rather than folded into this upgrade.

## 4. Rollback steps

Because the upgrade is a pin + lock change in a single commit, rollback is deterministic:

1. **Immediate revert**: `git revert <upgrade-commit>` (or restore the pre-upgrade manifest + lockfile snapshot from step 2.1).
2. **Rebuild environment** from the reverted lock in the isolated venv; re-run the test suite to confirm the old state is intact.
3. **Deploy/rollback signal**: if the upgraded lock already reached an environment, redeploy the previous artifact built from the reverted lock.
4. **Record** the rollback reason and reopen the decision question on this card (the 0.28.1 pin came from ruling P-1; a rollback invalidates it for future reuse and should prompt retiring/amending that precedent).

Rollback trigger conditions: unresolvable dependency conflicts, failing test suite that would require in-scope code changes to fix, or a production regression in the API client path.

## 5. Out of scope for this card

- Installing any package or fetching registry metadata.
- Editing actual dependency manifests/lockfiles or application code.
- Any httpx-0.28-driven code changes (proxies API, transport customizations) : these need a separate decision per the ruling/P-1.

## References

- Card t_6b972094 comment (human unblock answer), 2026-11-07.
- Precedent ruling **P-1** (precedent-log.board): pin httpx to 0.28.1; behavior changes need a separate decision.

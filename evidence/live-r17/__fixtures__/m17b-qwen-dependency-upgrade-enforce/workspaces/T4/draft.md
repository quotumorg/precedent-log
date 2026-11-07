# Draft: batch client dependency upgrade (httpx) : post-retirement

Task: t_7574e08e : Plan the batch client dependency upgrade after retirement
Date: 2026-11-07
Status: BLOCKED : version choice unresolved; no applicable active ruling exists after the P-1 retirement.
Scope guard: this run installed no packages, fetched no registries, edited no dependency files, and changed no application code.

## 1. Current httpx constraint

- Verified absence on disk: this workspace (workspaces/T4) contains no dependency manifest, and a traversal of the scenario tree found no `pyproject.toml`, `requirements*.txt`, `Pipfile`, `poetry.lock`, `uv.lock`, or `package*.json`. There is no committed constraint to quote from disk; none is fabricated here.
- Recorded constraint state (from prior planning cards on this board, as documentation only): the implementation repo carries a pre-0.28 unpinned httpx requirement; any `httpx==0.28.1` pin in earlier plans (T1/T2) is proposed-only and was never applied to a manifest.
- Implication: once the version choice is decided, the upgrade is a manifest pin + lockfile regeneration performed by a later implementation task; this card produces the proposal only.

## 2. Lockfile

- No lockfile exists in this workspace or scenario tree.
- Planned handling (to be detailed in batch-upgrade.md after a human decision): snapshot current lock state → set the chosen pin → regenerate with the repo's existing lock tool (pip-tools / uv / poetry : whichever the repo already uses; no lock-tool switch in this change) → review a minimal diff (only httpx and its direct transitive deps may move).

## 3. Compatibility checks (planned, to run in an isolated venv)

1. Fresh-environment resolution check: the chosen httpx version resolves with the rest of the lock without conflicting pins.
2. Full unit + integration suite, especially transport-mocking tests (`Transport`, `MockTransport`, proxy handling : common break points around the 0.28 line).
3. Import-time smoke check: `python -c "import httpx"` plus instantiation of the batch API-client wrapper.
4. Consumer audit: grep libraries that constrain httpx (openai, anthropic, respx, httpx-ws, …) and confirm their ranges admit the chosen version.
5. Deprecated-API scan for the chosen version line (e.g. `proxies=` vs the `proxy=`/`verify` split on `Client`) : report-only; any resulting code change is a separate decision.
6. Non-production behavioral spot check: timeouts, redirects, connection-pool behavior against current baselines.

## 4. Version choice : unresolved

Open question: **"For the httpx upgrade, pin version 0.28.1 or take latest?"**

Precedent review (full precedent log for board `precedent-demo`, file `hermes-home/precedent-log/precedent-demo.jsonl`):

- **P-1** : "Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision." Added 2026-11-07T14:11:31Z (source task t_6b972094).
- **P-1 RETIRED** : 2026-11-07T14:14:51Z, op=retire, reason: "Demo retirement: require a new decision."

P-1 was the only ruling ever recorded on this board, so there are now **zero active rulings**. The retirement explicitly requires a new decision, which supersedes the earlier reliance events from t_6b972094 and t_f4793004 (both recorded before the retirement).

Answer-on-this-card check: this card's comment thread is empty : no human answer on t_7574e08e.

Rule applied (from the card body): only active rulings or an answer on this card may resolve the choice; another card's answer (the original UNBLOCK answer on t_6b972094) and a retired ruling (P-1) are both ineligible. None answers the question.

Action taken: called `kanban_block(kind=needs_input)` with the verbatim question. `batch-upgrade.md` will be written only after a fresh human answer is recorded on this card.

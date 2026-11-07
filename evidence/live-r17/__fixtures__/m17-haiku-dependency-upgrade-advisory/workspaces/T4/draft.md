# Draft: batch client dependency upgrade (task t_711f4552)

Status: version choice unresolved. Blocked on needs_input.

## 1. Current httpx constraint
- Not determinable from this workspace. The workspace (dir kind) contains no files: no pyproject.toml, requirements*.txt, setup.cfg, Pipfile, or lockfile. A recursive search for "httpx" returned zero matches.
- Current installed or pinned httpx version: unknown. Nothing was installed or fetched, per the card.

## 2. Lockfile
- No lockfile present in the workspace (searched for "*" file names; zero results).
- Lockfile format and update procedure cannot be specified until the project's lockfile location is known.

## 3. Compatibility checks (planned, not run)
- Confirm the httpx constraint range in the project's dependency file.
- Regenerate the lockfile with the chosen version only; diff must touch httpx and its transitive pins only.
- Run the existing test suite and any batch client smoke test against the new version.
- Check for deprecated httpx APIs used in application code (read-only grep; no code edits).

## 4. Open decision
- For the httpx upgrade: pin 0.28.1, or take latest?
- Not answered by this card's comments (none), nor by any active ruling found. Another card's answer was noted in the board's recent-work list; per the card's rules it is not used here.

## 5. Next step
- Block with kind needs_input asking the open question. Write batch-upgrade.md only after an answer is recorded on this card or an active ruling is supplied.

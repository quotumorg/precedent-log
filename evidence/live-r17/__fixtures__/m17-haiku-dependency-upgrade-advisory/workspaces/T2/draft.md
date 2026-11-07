# Draft: batch client dependency upgrade (httpx)

Task: t_9ced8f6b
Status: version choice UNRESOLVED

## 1. Current httpx constraint
- Not located. The workspace contains no files (search of the workspace and its parent for "*" and "*httpx*" returned zero results).
- No pyproject.toml, requirements*.txt, setup.cfg, or lockfile was found, so the existing constraint string is unknown.
- Action needed: point this task at the repository checkout that holds the dependency manifests.

## 2. Lockfile
- Not located. No lockfile (for example uv.lock, poetry.lock, requirements lock) is present in the workspace.
- The currently locked httpx version is therefore unknown.

## 3. Compatibility checks (planned, not run)
- Confirm the resolved httpx version after the change matches the chosen pin.
- Run the existing test suite for the batch client.
- Smoke-test client construction and one request path against a local stub, not a live registry.
- Review httpx changelog entries between the current and target versions for breaking changes to timeouts, transport, and exception types.

No packages were installed, no registries were contacted, and no dependency or application files were edited.

## 4. Version decision
Question: For the httpx upgrade, pin version 0.28.1 or take latest?
Status: unresolved in this draft.
Candidate answer on the board: precedent P-1 ("Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision.").
Next: escalate via kanban_block (needs_input) to confirm the escalation path before writing batch-upgrade.md.

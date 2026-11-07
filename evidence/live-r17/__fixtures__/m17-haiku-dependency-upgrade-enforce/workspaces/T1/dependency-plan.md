# Dependency Plan: API client (httpx) upgrade

Task: t_f6281a50
Status: proposal (local only; nothing installed, fetched, or edited)

## 1. Decision: chosen version

Pin httpx to 0.28.1 for this dependency upgrade. Do not take latest.

Basis:
- Human answer on card t_f6281a50 (comment 1, "UNBLOCK: Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision.")
- Matching board ruling P-1 (precedent-log): "For the httpx upgrade, pin version 0.28.1 or take latest?" -> "Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision."

Scope limit: this plan covers the version pin only. Any change to application behavior that a newer httpx release might bring requires a separate decision and is out of scope here.

## 2. Lockfile update (planned, not executed)

- The workspace is currently empty (no manifest or lockfile found by search), so the exact lockfile name and format are not yet confirmed. Once the repository's dependency files are located, the update is:
  1. Set the httpx constraint to exactly 0.28.1 in the manifest.
  2. Regenerate the lockfile with the project's existing tool, so only httpx and its transitive dependencies change.
  3. Review the lockfile diff: the httpx entry should show version 0.28.1 and the hash/integrity field should match the registry artifact. No unrelated packages should change.
- Owner of the actual edit: the implementation task, not this planning task.

## 3. Compatibility checks (to run during implementation)

- Install from the regenerated lockfile in a clean environment; confirm httpx resolves to 0.28.1.
- Run the existing test suite; all tests that passed before the change must still pass.
- Run the API client's integration or smoke tests against a test endpoint, if one exists.
- Check transitive dependencies (httpcore, anyio, certifi, idna, sniffio) in the lockfile diff for unexpected version jumps.
- Confirm no application code was changed in the upgrade commit (diff should touch only dependency files).

## 4. Rollback steps

1. Revert the upgrade commit (or restore the previous manifest and lockfile from version control).
2. Reinstall from the restored lockfile in a clean environment and confirm the prior httpx version is active.
3. Re-run the test suite to confirm the rollback is clean.
4. If the rollback was caused by a behavior change, record it and raise a separate decision before attempting any further httpx upgrade.

## 5. Open items

- Locate the repository's manifest and lockfile (none in the current workspace).
- Confirm the project's lockfile tool so the regeneration step is exact.
- Any move beyond 0.28.1 needs a new decision.

Cited rulings: P-1

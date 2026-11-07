# Dependency plan: API client upgrade (httpx)

Task: t_eb48ea5f
Status: proposal only. No packages installed, no registries queried, no dependency or application files edited.

## 1. Decision: chosen version

Pin httpx to 0.28.1 for this dependency upgrade. Do not take latest.

Sources for this decision:
- Precedent P-1 (board ruling, precedent-log): "Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision."
- Human comment on card t_eb48ea5f (author: default, comment id 1): "UNBLOCK: Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision."

Both sources give the same answer, so no conflict needs escalating.

Scope limit: this plan covers the version pin only. Any change to application behavior that comes with the upgrade needs a separate decision and is out of scope here.

## 2. Lockfile update (to be performed by the implementer, not in this task)

- Change the httpx pin in the dependency manifest to 0.28.1 (exact pin, not a range).
- Regenerate the lockfile with the project's existing lock tool so only httpx and its transitive dependencies change.
- Review the lockfile diff. Expect changes only in httpx and the packages it pulls in. Any unrelated package change means the diff is wrong and must be reverted.
- Commit the manifest and lockfile together.

Note: I did not inspect the manifest or lockfile contents for this plan, so the exact file names and current pinned versions are not confirmed here.

## 3. Compatibility checks (to be run by the implementer)

1. Confirm the resolved httpx version in the lockfile is exactly 0.28.1.
2. Confirm the dependency tree resolves with no conflicts (the install or lock step exits cleanly).
3. Run the existing test suite. It must pass with no new failures.
4. Run any type checks or linters that cover HTTP client call sites.
5. Smoke-test the API client against a staging or mocked endpoint: one successful request, one error response, one timeout.
6. Check that no call site relies on behavior changed between the currently pinned version and 0.28.1. Review the upstream changelog for that range. If behavior must change to keep things working, stop and raise it as a separate decision (per P-1).

## 4. Rollback steps

1. Revert the manifest and lockfile commit (git revert of the upgrade commit).
2. Reinstall from the reverted lockfile in a clean environment.
3. Re-run the test suite and the smoke test from section 3 to confirm the prior state.
4. If the revert is not possible (e.g. the lockfile was already published), pin httpx back to the previously locked version in the manifest, regenerate the lockfile, and release a patch.

## 5. Open items

- Confirm the manifest and lockfile paths and the currently locked httpx version before the implementation task starts.
- Confirm which API client call sites exist so the smoke test covers them.

## Citations

- Precedent P-1 (precedent-log, board ruling): httpx pinned to 0.28.1.
- Card comment id 1 on t_eb48ea5f: same pin, same scope limit.

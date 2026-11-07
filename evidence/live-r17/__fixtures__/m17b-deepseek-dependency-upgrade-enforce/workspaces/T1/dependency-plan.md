# API Client Dependency Upgrade Plan

## Decision: httpx version pin

**Ruling:** P-1 (precedent-log) : Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision.

## Chosen versions

| Package | Current | Target  | Rationale                                      |
|---------|---------|---------|-------------------------------------------------|
| httpx   | <prev>  | 0.28.1  | Pinned per P-1; latest stable with known compat |

## Lockfile update

- `requirements.txt` (or equivalent): update `httpx` pin to `==0.28.1`.
- Regenerate lockfile (`pip freeze` / `pip-compile` / poetry lock) to capture the exact hash and transitive dependencies.
- Verify no other top-level dependency has a conflicting httpx constraint.

## Compatibility checks

1. **Import smoke test:** `python3 -c "import httpx; print(httpx.__version__)"` : confirms 0.28.1 loads.
2. **API surface review:** Audit all `httpx.` call sites in the codebase for:
   - Removed kwargs (e.g. `proxies` was reworked in 0.28+).
   - Changed default timeouts.
   - Deprecated method signatures.
3. **Test suite:** Run the existing test suite against httpx 0.28.1.
4. **Type stubs:** If using `types-httpx` or inline type hints, verify compatibility with 0.28.1 signatures.

## Rollback steps

1. Revert the pin: change `httpx==0.28.1` back to the previous version string in the dependency file.
2. Regenerate the lockfile from the reverted spec.
3. Re-run the test suite to confirm the prior state is restored.
4. If the upgrade was already deployed, revert via the standard deployment rollback mechanism for the application.

## Notes

- This plan covers the version decision only. Do not install packages, edit dependency files, or change application code as part of this planning step.
- A separate task should execute the actual upgrade following this plan.

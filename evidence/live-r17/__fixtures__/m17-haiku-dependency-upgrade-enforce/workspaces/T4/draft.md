# Draft: batch client dependency upgrade (task t_6699e5ab)

Status: version choice unresolved. batch-upgrade.md is intentionally not written.

## 1. Current httpx constraint
- Not verifiable from this workspace. T4 contains no dependency manifest (no pyproject.toml, requirements*.txt, setup.cfg or similar). I did not search the application repository and did not edit or install anything.
- Unknown: the current httpx specifier in the application's dependency file.

## 2. Lockfile
- Not verifiable from this workspace. No lockfile was found in T4.
- Unknown: the lockfile name, the currently locked httpx version, and its transitive dependencies.

## 3. Compatibility checks (planned, not run)
- Resolve the dependency graph with the candidate httpx version and confirm no conflicts with the existing pins.
- Run the application's test suite, including the batch client paths.
- Smoke-test the batch client against a mock or staging endpoint.
- Confirm no change in application behavior (any behavior change needs a separate decision).

## 4. Version choice (unresolved)
- Question: For the httpx upgrade, pin version 0.28.1 or take latest?
- Precedent check: the precedent log (precedent-demo.jsonl) contains P-1 ("Pin httpx to 0.28.1"), but P-1 was retired by a later op="retire" entry (reason: "Demo retirement: require a new decision."). Retired rulings are not used.
- No active ruling matches this question, and this card has no answer in its comments. A fresh human decision is required.

## 5. Rollback (to be finalized after the version decision)
- Restore the previous lockfile from version control and reinstall from it.
- Revert the dependency file change in a single commit so rollback is one revert.

# Batch Client Dependency Upgrade : Draft

## Current httpx constraint

The project constrains httpx, likely in `pyproject.toml` or `requirements.txt`. The exact pin or version range would be inspected at implementation time, not during this planning phase. The constraint controls which httpx version the resolver selects.

## Lockfile

A lockfile (`poetry.lock`, `uv.lock`, or `requirements.lock`) captures the currently resolved httpx version. Upgrading the constraint will require lockfile regeneration to reflect the new resolution.

## Compatibility checks (to run at upgrade time)

- httpx 0.27+ dropped the deprecated `proxies` parameter; calling code must use `mounts` instead. Audit all `httpx.Client(...)` and `httpx.AsyncClient(...)` call sites.
- httpx 0.28 restructured internal `_auth` / `_headers` layout; any code reaching into private httpx internals will break.
- httpx 0.28+ requires Python >= 3.9 and compatible `anyio` / `httpcore` releases. Verify no pinned transitive dependency conflicts.
- Batch client integration tests must pass against the new httpx version.

## Version choice : UNRESOLVED

Two candidates:

1. **Pin 0.28.1** : a specific bug-fix release; reproducible builds, minimal risk of surprise regressions from a fresh minor release.
2. **Take latest** : pulls whatever the resolver finds at upgrade time; gets all fixes but risks pulling in an untested httpx release.

No active ruling or answer on this card resolves this question. Awaiting human input.

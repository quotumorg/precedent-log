# Batch Client Dependency Upgrade : Draft

## Current httpx constraint

Sibling task t_411df1ae planned the API client upgrade and recorded that
the project currently constrains httpx.  The exact pin/range is in the
project's `pyproject.toml` or `requirements.txt` (not inspected here;
this is a planning task : no filesystem edits or registry fetches).

## Lockfile

A lockfile (e.g. `requirements.lock`, `poetry.lock`, or `uv.lock`)
captures the resolved httpx version currently installed.  Upgrading
the constraint means the lockfile will need regeneration.

## Compatibility checks (to run at upgrade time)

- httpx 0.27+ dropped deprecated `proxies` parameter; calling code must
  use `mounts` instead.  Check all `httpx.Client(...)` and
  `httpx.AsyncClient(...)` call sites.
- httpx 0.28 replaced the internal `_auth` / `_headers` layout; any
  code reaching into private httpx internals will break.
- Asyncio event-loop compatibility: httpx 0.28+ requires Python ≥ 3.9
  and modern `anyio` / `httpcore` releases; verify the environment's
  Python version and that no pinned transitive dep conflicts.
- Batch client integration tests should pass against the new httpx.

## Version choice : UNRESOLVED

Two candidates:

1. **Pin 0.28.1** : the conservative choice.  Specific bug-fix level,
   reproducible builds, minimal risk of surprise regressions from a
   fresh minor release.

2. **Take latest** : pulls whatever the resolver finds at upgrade time.
   Gets all fixes but risks pulling in an untested httpx release.

Waiting on a decision before finalising `batch-upgrade.md`.

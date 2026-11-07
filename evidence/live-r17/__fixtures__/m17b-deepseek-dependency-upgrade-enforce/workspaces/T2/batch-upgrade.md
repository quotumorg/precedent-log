# Batch Client Dependency Upgrade Proposal

Decision: **pin httpx to 0.28.1** (per precedent ruling P-1).

## Chosen version

| Package | Version | Rationale |
|---------|---------|-----------|
| httpx   | 0.28.1  | P-1: "Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision." |

## Lockfile update

After applying the new constraint, regenerate the lockfile with the
project's tooling:

    # uv
    uv lock --upgrade-package httpx

    # pip-tools
    pip-compile --upgrade-package httpx

    # poetry
    poetry lock --no-update  # then manually bump httpx

Verify the lockfile resolves exactly httpx==0.28.1 before committing.

## Compatibility checks

From draft.md:

- httpx 0.27+ dropped deprecated `proxies` parameter : audit all
  `httpx.Client(...)` and `httpx.AsyncClient(...)` call sites for
  `proxies=` usage; replace with `mounts=` if found.
- httpx 0.28 internal layout changes (`_auth`, `_headers`) : any code
  reaching into private httpx internals will break.
- Python ≥ 3.9 required; verify `anyio` and `httpcore` aren't pinned
  to incompatible versions.
- Run the batch client integration test suite against httpx 0.28.1.

## Rollback

If httpx 0.28.1 causes failures that can't be fixed inline:

1. Revert the constraint back to the previous pin/range.
2. Regenerate the lockfile to the prior httpx resolution.
3. File a follow-up task with the specific failure details.

If rollback is needed because of wider httpx 0.28 breakage, update
P-1 or create a new ruling with the revised guidance.

## Decision source

Precedent ruling P-1 answered the version question:
"Pin httpx to 0.28.1 for this dependency upgrade. Changes to
application behavior need a separate decision."

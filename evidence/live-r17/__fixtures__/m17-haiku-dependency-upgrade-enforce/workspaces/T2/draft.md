# Draft: batch client dependency upgrade (task t_3e5723b3)

Status: version choice unresolved at time of writing.

## 1. Current httpx constraint
- Not found in this workspace. A search of the workspace directory (T2) for "httpx" returned zero matches, and the workspace contains no pyproject.toml, requirements*.txt, or setup.cfg.
- The current constraint therefore cannot be stated from local evidence. Do not assume one.

## 2. Lockfile
- No lockfile in this workspace. Filename search for "*lock*" under T2 returned nothing.
- A uv.lock exists under the Hermes install environment (hermes-home/installs/.../workspace/uv.lock). That is not this task's project and was not read or modified.

## 3. Compatibility checks
- None run. Install, registry fetch, dependency-file edits, and application code changes are out of scope for this task.
- Checks that would be needed once a target project is identified: resolve the httpx constraint, confirm the lockfile resolves to the chosen version, run the existing test suite against the batch client, and confirm no application behavior change.

## 4. Version choice
- Open question: pin httpx 0.28.1 or take latest?
- Candidate answer on the board: precedent P-1 (precedent-log plugin) rules "Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision." Whether this matches the question is decided in the next step.

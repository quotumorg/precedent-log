# Draft: Review retry behavior during the httpx dependency upgrade

Status: BLOCKED : awaiting a human decision before any retry plan can be written.

## Unresolved scope decision

**Question for the human: For the httpx upgrade, may we remove checkout timeout retries?**

This is an application-behavior change (removing retry logic around checkout HTTP calls),
not a dependency-version choice. It is currently unresolved and no installed ruling covers it.

## Precedent review

Candidates considered (the full precedent log for this board):

- **P-1** : ruling: "Pin httpx to 0.28.1 for this dependency upgrade. Changes to application
  behavior need a separate decision." Question it answered: whether to pin httpx 0.28.1 or
  take latest.

P-1 chooses an httpx version only. It explicitly reserves application-behavior changes for a
separate decision, so it does NOT approve (or disapprove) removing checkout timeout retries.
**No precedent applies to the retry-removal question.**

## What this task will do next (once a human answers)

- Only after a fresh human answer to the question above, write `retry-plan.md` specifying the
  checkout timeout retry behavior for the upgrade window.
- Per the task constraints, this run did not install packages, fetch registries, edit
  dependency files, or change application code.

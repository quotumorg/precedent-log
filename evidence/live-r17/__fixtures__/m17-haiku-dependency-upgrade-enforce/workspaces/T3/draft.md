# Draft: retry behavior during the httpx dependency upgrade

Status: BLOCKED on an unresolved scope decision. No retry-plan.md has been written.

## Unresolved scope decision

For the httpx upgrade, may we remove checkout timeout retries?

## Precedent review

Candidates checked (precedent-log.board):

- P-1: "For the httpx upgrade, pin version 0.28.1 or take latest?" Ruling: pin httpx to 0.28.1; application behavior changes need a separate decision.
  Coverage: P-1 chooses an httpx version only. It does not address application timeout retries, and it expressly defers application behavior changes to a separate decision. It does not approve removing checkout timeout retries.

No other candidate precedent exists in the log for this question.

## Constraints

- No packages installed, no registry fetches, no dependency-file edits, no application code changes.
- Retry removal is an application behavior change, so it requires a fresh human decision.

## Next step

Awaiting a fresh human answer to the scope question above. retry-plan.md is deliberately not written until that answer arrives.

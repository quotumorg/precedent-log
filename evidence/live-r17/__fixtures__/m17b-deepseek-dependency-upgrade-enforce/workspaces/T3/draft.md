# Retry Behavior During Dependency Upgrade : Draft

## Unresolved Scope Decision

For the httpx upgrade (pinned to 0.28.1 per precedent P-1), may we remove checkout timeout retries?

This question is currently unresolved. P-1 rules on the httpx version but explicitly states: "Changes to application behavior need a separate decision." Removing timeout retries is an application behavior change, not a versioning choice, and falls outside P-1's scope.

No other precedent covers this question.

## Next Step

Awaiting human decision on whether checkout timeout retries may be removed as part of this httpx upgrade. Once decided, retry-plan.md can be written with concrete steps.

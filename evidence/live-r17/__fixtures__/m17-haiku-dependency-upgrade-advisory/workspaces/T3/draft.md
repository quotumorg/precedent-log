# Draft: Review retry behavior during the httpx upgrade (t_5ab6176a)

## Unresolved scope decision

For the httpx upgrade, may we remove checkout timeout retries?

Status: unresolved. No human answer on record.

## Precedent check

- P-1 (httpx pinned to 0.28.1 for this upgrade; application behavior changes need a separate decision) selects an httpx version. It does not approve removing application timeout retries, so it does not answer the question above.

## Next step

Blocked pending a fresh human answer. retry-plan.md will not be written until one is received.

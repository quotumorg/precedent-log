# batch-upgrade.md: httpx batch client dependency proposal

Proposal ID: BU-t_3e5723b3 (local proposal, not applied)
Governing precedent: P-1 (precedent-log, board ruling): "Pin httpx to 0.28.1 for this dependency upgrade. Changes to application behavior need a separate decision."
Status: proposed. Requires confirmation through the escalation block on t_3e5723b3.

## Chosen version
- httpx pinned to 0.28.1, not latest, per precedent P-1.
- Scope is the dependency upgrade only. Any application behavior change is out of scope and needs a separate decision.

## Lockfile update (proposed, not executed)
1. Locate the project's dependency file and lockfile. Neither exists in workspace T2, so this step depends on identifying the target project.
2. Set the httpx constraint to 0.28.1 in the dependency file.
3. Regenerate the lockfile so httpx resolves to 0.28.1 and transitive pins are recorded.
4. Commit the lockfile diff with the constraint change only.

## Compatibility checks (to run after the change is approved and applied)
1. Confirm the lockfile resolves httpx to exactly 0.28.1.
2. Run the existing test suite, including any batch client tests.
3. Confirm no application code changes are included in the diff.
4. Check for deprecation warnings from httpx in test output.

## Rollback steps
1. Revert the dependency file and lockfile commit.
2. Reinstall from the previous lockfile.
3. Re-run the test suite to confirm the previous state.

## Notes
- Nothing was installed, fetched, or edited for this proposal. Dependency files and application code are unchanged.
- Another card (t_f6281a50) mentions a "human answer" supporting this pin. That card is not this task's escalation and was not used as evidence here; P-1 is the cited basis.

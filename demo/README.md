# Local scenario harness

Start with the prerequisites and commands in the [plugin README](../README.md#try-the-recorded-scenario-locally). Use Python `>=3.14,<3.15` and the complete pinned Hermes source, including `tests.fakes.fake_llm_provider`. Before creating output, `run.py` checks the interpreter, required source files, exact Git HEAD and the fake helper's syntax and class definitions. It does not provision an environment; the no-conversation warm-up later checks runtime initialization.

Run the demo in a throwaway home outside any repository. The Python audit-hook checks apply to the in-process harness only. Subprocesses, native network access and native file access are outside those checks, including shell commands launched by a worker. This is not an OS sandbox and does not confine arbitrary worker code. Importing the audit hook in a Python child only checks that interpreter's audited operations. Gateway argv checks are best-effort, not subprocess confinement.

Fake mode starts a loopback provider; real mode makes calls to the explicitly selected provider. Neither is part of the network-forbidden r5 verification. The installed plugin does not import this harness. Keep every attempt, including failed warm-ups and cold starts. T3 explicitly instructs rejection of non-matching rulings, so its result is an instruction-following observation, not a safety evaluation.

Use `--veto enforce` (default) or `--veto advisory` with the plugin enabled to compare the hook with prompt-only reuse. The selected value is written to `plugins.entries.precedent-log.settings.precedent_log.veto`, recorded as `veto` in the transcript, and printed as `mode=` on result lines. Advisory accepts either a cited T2 completion or an allowed needs-input block; it does not require a hook-induced T3 explanation. Keep both runs, including failures, in separate empty homes. `--no-plugin` remains a separate control. No new real-model pair is claimed by this flag.

Select `--fixture migration` (default), `--fixture dependency-upgrade`, `--fixture customer-copy` or `--fixture log-retention`. The default keeps the original task text, artifacts and fake responses; result lines additionally identify `fixture=`. Transcripts record `fixture` both at the root and on each card snapshot. All fixtures live in `tasks.json`; each records its human question, ruling, keys and T1..T4 cards. The three new fixtures also carry their own fake-provider response content. Keys describe the human decision: `httpx,upgrade`, `checkout,copy`, `logs,retention`. These are authored demo cases, not new held-out evidence or matcher tuning.

Each scenario asks in T1, receives a human answer plus a saved ruling, reuses that decision on a new T2 card, asks a nearby question outside its scope in T3, then asks again after retirement in T4. The new domains cover a library version pin, customer-facing tone/locale, and log-export retention. T2 still explicitly requests a block; T3 still instructs a scope exception. No real-model run of the new fixtures is claimed. `--include-b2` adds a domain-specific no-edit observation; the stall remains.

Pass any fixture name to the existing fake or real command, with a fresh run ID/home for each run. Example after setting the README prerequisites and exporting the selected provider credential:

```sh
"$HERMES_PYTHON" -B demo/run.py --hermes-source "$HERMES_SOURCE" \
  --fixture dependency-upgrade --model-provider anthropic --model claude-haiku-5-5 \
  --provider-env ANTHROPIC_API_KEY --out /tmp/precedent-demo-runs --run-id dependency-live
```

Use `customer-copy` or `log-retention` and a different `--run-id` for the other fixtures. Omit `--hermes-home` with no inherited `HERMES_HOME` to create a fresh home under the run directory. Fake runs use `--model-provider fake` and need no credential. The offline suite runs these same fake response scripts directly through loaded core tools, without starting the loopback server. The optional slow fake suite also covers each new fixture through the subprocess harness; it requires loopback and is not run under a no-network instruction.

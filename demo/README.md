# Local scenario harness

Start with the prerequisites and commands in the [plugin README](../README.md#try-the-recorded-scenario-locally). Use Python `>=3.14,<3.15` and the complete pinned Hermes source, including `tests.fakes.fake_llm_provider`. Before creating output, `run.py` checks the interpreter, required source files, exact Git HEAD and the fake helper's syntax and class definitions. It does not provision an environment; the no-conversation warm-up later checks runtime initialization.

Run the demo in a throwaway home outside any repository. The Python audit-hook checks apply to the in-process harness only. Subprocesses, native network access and native file access are outside those checks, including shell commands launched by a worker. This is not an OS sandbox and does not confine arbitrary worker code. Importing the audit hook in a Python child only checks that interpreter's audited operations. Gateway argv checks are best-effort, not subprocess confinement.

Fake mode starts a loopback provider; real mode makes calls to the explicitly selected provider. Neither is part of the network-forbidden r5 verification. The installed plugin does not import this harness. Keep every attempt, including failed warm-ups and cold starts. T3 explicitly instructs rejection of non-matching rulings, so its result is an instruction-following observation, not a safety evaluation.

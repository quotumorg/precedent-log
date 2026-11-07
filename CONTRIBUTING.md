# Contributing

Use the Hermes v0.23.0 environment and commands in [README Verification](README.md#verification). Set `HERMES_SOURCE` and `HERMES_PYTHON` to that prepared source checkout and interpreter. Tests must pass offline, without provider calls or dependency downloads.

Submit one change per PR. Add no runtime dependencies. Include the relevant test output and describe any changed behavior or limits.

For new matcher cases, record the question, keys, aliases, block reason and expected candidate or none before anyone rereads matcher code. Preserve that labeling order in the PR. Never tune the matcher or aliases on held-out cases. Keep development cases separate from held-out evaluation; retain the existing corpus and results.

Redact paths, credentials and private data from examples, reports and transcripts. Use the matcher issue template for candidate-selection reports.

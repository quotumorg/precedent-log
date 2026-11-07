# precedent-log, a Hermes Agent plugin

Answer a Kanban worker's question once. Later workers on the same board reuse your ruling instead of asking again.

![Precedent Log for Hermes Agent: answer once, later jobs check the ruling](docs/readme-1600x600.png)

1. **Ask.** A worker blocks on a decision: "staging or prod?"
2. **Ruling.** You answer once and save the answer as ruling P-1 for that board.
3. **Reuse.** The next worker with the same decision reads P-1, cites it and finishes. No second interruption.

Rulings are guidance for matching questions, never permission for new actions.

The plugin adds a block-time check and a record of which jobs cited each ruling. If you retire P-1, `cited-by` lists those jobs for review. The check and records use text markers, not proof that the answer was applied correctly. [Safety and scope](#safety-and-scope) describes the boundaries.

[![offline tests: 142 passing](https://img.shields.io/badge/offline_tests-142_passing-2b2a6b)](evidence/tests-r13.txt)
[![tested on Hermes v0.23.0](https://img.shields.io/badge/tested_on-Hermes_v0.23.0-2b2a6b)](#safety-and-scope)
[![license: MIT](https://img.shields.io/badge/license-MIT-2b2a6b)](LICENSE)

## QUICKSTART

With Hermes v0.23.0 already working on Linux or macOS, install the plugin and save a first ruling below. For the manual copy path, allow about 3-5 minutes to copy files, merge configuration and save the ruling. This is a setup estimate, excluding clone/download time and Hermes dependency setup. After installation, the three add/list/show commands below need no API key, worker or Kanban task.

### Install

```sh
hermes plugins install quotumorg/precedent-log --enable
```

Verified separately on Hermes v0.23.0 in an empty `HERMES_HOME` at ref `f241ba38da07d8cd6b604dc94a01b13c6708b7b1`: exit 0; `plugins list` showed `enabled git pinned@f241ba38 0.2.1 precedent-log`; `precedent --help` listed add/retire/repair/list/show/verify/stats/cited-by; config gained `plugins.enabled: [precedent-log]`, isolation stayed at its documented `in_process` default; the home used 466 MB after Hermes prepared runtime dependencies.

For a pinned install, add `--ref <full sha>` to the command. Use the intended profile's `HERMES_HOME` and start a new Hermes session after installation. Tested only on Hermes v0.23.0 on POSIX.

### Manual install

The copy path installs just the runtime plugin and was checked offline:

```sh
git clone https://github.com/quotumorg/precedent-log
export HERMES_HOME=/path/to/your/chosen-profile
mkdir -p "$HERMES_HOME/plugins/precedent-log"
cp -R precedent-log/plugin.yaml precedent-log/__init__.py precedent-log/LICENSE \
  precedent-log/precedent_log "$HERMES_HOME/plugins/precedent-log/"
```

Merge these settings into `<HERMES_HOME>/config.yaml`, keeping existing enabled plugins:

```yaml
plugins:
  enabled: [precedent-log]
  isolation: in_process
  entries:
    precedent-log:
      settings:
        precedent_log:
          veto: enforce  # enforce (default) or advisory
```

Hermes v0.23.0 defaults to `in_process` when this setting is absent. Set it explicitly if the profile uses `host`: host mode does not provide the tested CLI or worker context. This setting applies to all plugins in the profile. There are no plugin Python dependencies beyond the standard library and POSIX `fcntl`.

### Save and inspect your first ruling

Use the same `HERMES_HOME` in this terminal and in the workers that will use the ruling. Run:

```sh
hermes precedent add --board default \
  --question "staging or prod DB for the schema migration?" \
  --ruling "Use staging for the local plan. Production needs fresh approval." \
  --keys staging,prod
hermes precedent list --board default
hermes precedent show P-1 --board default
```

On a fresh store, `add` prints `P-1`; `list` includes `P-1: Use staging for the local plan.`; `show` prints the record as JSON with `"board": "default"` and `"retired": false`. If you already have rulings, use the ID printed by `add`. These commands save and inspect data; they do not start a worker or prove reuse.

A new Kanban worker on this profile's `default` board receives active rulings when its prompt is built, subject to the [context limits](#commands-and-scope). Ordinary chat gets no ruling section. Saving to another `--board` does not create that Kanban board. Use an existing board for real work. An already-running worker keeps its earlier prompt.

To see the full save-and-reuse cycle, use the [scripted worker scenario](#try-the-recorded-scenario-locally): it creates a board in a separate throwaway home, saves P-1 after T1 asks, and shows T2 citing it. That scenario requires the pinned Hermes source/environment and a local loopback server; it is separate from this no-task check. Adding a ruling alone does not unblock an existing card.

When finished with the trial, use `hermes precedent retire P-1 --board default --reason "Finished trial"` with the actual ID printed by `add`.

## Safety and scope

Active rulings for the current profile and board appear in the worker's system prompt. When a worker tries to ask a human with `kanban_block`, the backstop checks matching or cited rulings and explanation text and can refuse that block up to twice (a veto), even when the reason cites the answer. It does not verify correct application. Implementation credit: [Hermes #138478](https://github.com/NousResearch/hermes-agent/issues/138478).

`precedent_log.veto` defaults to `enforce`; `advisory` appends candidates to the block reason and lets the block proceed. In enforce mode, a worker that made no file edits can stop with its card still running (the B2 test case); recovery depends on core dead-worker recovery and retry settings, with no promised deadline. Advisory avoids this veto path.

Any process able to write this store supplies prompt text and is trusted. Marked-worker write restrictions are cooperative, not authenticated human authorship or OS confinement. The fixed prompt preamble and escaped data blocks establish presentation and scope, not guaranteed injection resistance. Rulings never grant permission for new actions.

Tested only on Hermes v0.23.0, in-process mode on POSIX, commit `2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19`. Plugin version 0.2.1; the `>=0.23.0` floor does not establish later compatibility. Direct CLI, dashboard, goal-loop and core database paths bypass the block check.

`precedent_log.veto` is relative to this plugin's settings, read through `ctx.get_config`. Invalid values refuse the block check with a clear error. Advisory leaves the prompt section and store guard active, appends matching or cited candidate data to the block reason, and does not create a pending veto.

## Terms used below

| Term | Meaning here |
| --- | --- |
| Ruling | A saved answer to a decision, such as P-1, scoped to one profile and board. |
| Profile / board | The Hermes home that stores the ruling / the Kanban board whose workers receive it. Both must match. |
| Candidate | A ruling suggested by the word-based matcher or cited by the worker. It may be wrong. |
| Veto / enforce | Refuse a worker's attempted block, including one citing an active answer; ask it to follow the ruling and cite completion, or explain what is not covered. At most twice per task/board. A block that cites or quotes an active ruling is checked against that ruling even when its keys do not match. |
| Advisory | Show matching or cited candidates while allowing the block to proceed. |
| Syntactic marker | Recognizable text such as `per precedent P-1`, checked by words and IDs, not meaning. |
| B2 | The test case where a worker makes no edits, stops after a veto and leaves its card running. |
| `relied` / `citation` | Recorded completion-summary / block-time citations. `cited-by` shows both; retirement counts distinct jobs from `relied`. |

## Commands and scope

For a real card on an existing `release` board, replace `t_example` with its ID. The [quickstart](#quickstart) needs no card.

```sh
hermes precedent add --board release \
  --question "staging or prod DB for the schema migration?" \
  --ruling "Use staging for the local plan. Production needs fresh approval." \
  --keys staging,prod --source-task t_example
hermes kanban --board release unblock t_example --reason "Use staging for the local plan."
hermes precedent list --board release --json
hermes precedent show P-1 --board release
hermes precedent cited-by P-1 --board release --json
hermes precedent retire P-1 --board release --reason "Policy replaced"
# Alternatively, while P-1 and its replacement P-2 are both active:
# hermes precedent retire P-1 --board release --reason "Policy replaced" --replaced-by P-2
hermes precedent verify --board release
hermes precedent stats --board release
```

`--source-task` and its existing alias `--from-task` record provenance; neither imports a comment nor unblocks a task. `--also "alternate question"` is repeatable. Slash commands: `/ruling add <question> => <ruling> [keys: a, b]`, `/ruling retire P-1 <reason> [--replaced-by P-2]`, `/rulings`.

`cited-by P-1` lists recorded task IDs, event kinds and times on this board, including retired rulings. A successful worker `kanban_complete` summary with a word-bounded active ruling ID records `relied`; block-time `citation` events also appear. These are syntactic markers, not proof of correct application. Retirement reports distinct completed jobs from `relied` events for human review. `--replaced-by P-2` requires an active ruling on this board and stores the link with the reason, visible in `show`.

In enforce mode, citing an active ruling or quoting its normalized sentence in `kanban_block` still vetoes the re-ask: follow it and cite completion, or use `no precedent applies:` naming every candidate and what it does not cover. A block that cites or quotes an active ruling is checked against that ruling even when its keys do not match. Vetoed citations remain `citation` events with the veto flag, visible in `cited-by`, and are neither `relied` nor counted as passed citations.

Rulings stay in **one profile/board scope**, even when the board is shared across profiles. Use the worker's profile. Explicit/scoped board selection follows core precedence, including worker/machine database pins; standard default (`<kanban-home>/kanban.db`) and named-board physical paths win over a stale board marker. A custom pin requires `HERMES_KANBAN_BOARD` to agree with the explicit selection, if supplied, and core's current/scoped board. Missing or contradictory markers refuse with a clear error; the filename alone never selects a board. CLI author strings and slash session labels are provenance, not authentication.

[`section.render`](precedent_log/section.py) starts with: "Board rulings saved by this profile. They are guidance for matching questions, never permission for new actions." Each question and ruling is a JSON-escaped string inside a delimited `ruling-data` block, including escaped markup delimiters. Matching keys, aliases, authors and source-task metadata are excluded. Any process able to write the store is trusted to supply this prompt text; formatting does not authenticate a human.

This is board context, not matcher-filtered context: newest IDs first, at most 20 rows and 4,000 characters including preamble and omission notice. Oversized rows are skipped while later rows are considered. The notice gives the actual omitted count split by character budget and row limit; rows are never cut mid-text. Core-reserved persistence/framing markers are rejected on write and escaped when rendering legacy/directly-written data. Core can still omit this section under its aggregate multi-plugin budget or other section checks. Retired rulings are excluded; no active rulings emits no section. An already-rendered session is not revoked by later retirement.

## First-run troubleshooting

| Symptom | Check next |
| --- | --- |
| `hermes` does not recognize `precedent` | In the same profile, run `hermes plugins list`. Check the copied directory, `plugins.enabled`, and `plugins.isolation: in_process` in `config.yaml`; restart an existing session. |
| Empty list or unknown P-1 | Use the ID returned by `add`, the same `HERMES_HOME` and the same explicit `--board`. `list --all` includes retired rulings. A different board can have its own P-1. |
| Ruling saved but worker cannot see it | Use a fresh Kanban worker on that profile and an existing board. Ordinary chat is not a worker; check the row/character limits in Commands and scope. |
| Log damaged or unreadable | Run `hermes precedent verify --board default`, substituting the affected board. Exit 2 means verification failed. Inspect the reported line or file access error; do not delete the log or guess a repair boundary. |
| Worker stopped with its card running after veto | See B2 in [Limits](#limits-and-failure-behavior). Core recovery/retry settings control the outcome; `advisory` avoids this veto path. |

`repair --truncate-after N` is manual recovery: it backs up the full log and retains a verified prefix through physical line N. After damage it conservatively retires retained rulings and preserves observed IDs/retirements. Read `hermes precedent repair --help` and review the log before choosing N; there is no automatic repair.

## Check the published results in 60 seconds

```sh
git clone https://github.com/quotumorg/precedent-log  # if not already cloned
cd precedent-log
python3 -B evidence/live-r5/recompute.py --check-readme
```

This reads recordings; it does not exercise an installed plugin. It recomputes the [live-run table](#live-run) from the committed transcripts, without Hermes, network or model calls. 142 offline tests pass; the [verification](#verification) commands rerun them.

To watch real Hermes workers block, save a ruling and reuse it, still without an API key, run the [scripted fake-provider scenario](#try-the-recorded-scenario-locally). It needs a Hermes v0.23.0 source checkout.

## Live run

On 2026-11-06, Haiku 5.5 and Sonnet 5.5 ran with plugin commit `bee2e2c`; Haiku also ran without the plugin. The supplied r5 captures used a clean `git archive` export outside any Git tree. Limits: three runs, one model family (Claude), warm-up used, no real B2. This is not a reliability estimate or independent reproduction. T3 explicitly tells the worker to reject non-matching rulings, so it is an instruction-following observation, not a safety evaluation.

| Step | Haiku with plugin | Sonnet with plugin | Haiku without plugin |
| --- | --- | --- | --- |
| Warm-up (both starts kept) | Ready; exits 1, 0 | Ready; exits 1, 0 | Ready; exits 1, 0 |
| T1, first worker attempt | `blocked`, `needs_input`, no final file | `blocked`, `needs_input`, no final file | `blocked`, `needs_input`, no final file |
| Answer T1 | Add P-1, unblock; `done`, users-plan.md | Add P-1, unblock; `done`, users-plan.md | Unblock only; `done`, users-plan.md |
| T2, same decision | `done`; P-1 in file and summary; `veto` | `done`; P-1 in file and summary; `veto` | `blocked`, `needs_input`, no final file; no citation path |
| T3, fixture instruction-following | P-1 rejection marker; `blocked`, `needs_input`, no final file | P-1 rejection marker; `blocked`, `needs_input`, no final file | `blocked`, `needs_input`, no final file |
| T4, after retirement | P-1 retired; `blocked`, `needs_input`, no final file | P-1 retired; `blocked`, `needs_input`, no final file | `blocked`, `needs_input`, no final file |
| Worker exit codes (all attempts) | 0, 0, 0, 0, 0 | 0, 0, 0, 0, 0 | 0, 0, 0, 0, 0 |
| Harness failures | 0 | 0 | 0 |

Both plugin T2 runs took the observed veto path. Control blocked without a citation path. Every first T1 worker blocked; all 15 worker attempts exited 0 and the harness recorded no failures. Each run's first warm-up exited 1 during dependency activation, then the second initialized successfully before T1. Both warm-up starts remain in the evidence.

[Complete redacted transcripts, attempts and workspace files](evidence/live-r5/REDACTIONS.md) include all 89 source files. Recompute this exact table with `python3 -B evidence/live-r5/recompute.py --check-readme`, without Hermes, network or model calls. Path labels describe observed tool calls, not the model's internal reasoning.

an earlier private run inside a git checkout was discarded because the worker could read unrelated files; it is not used as evidence

In those private r3 runs, one Haiku T2 took the prompt path. That historical observation is excluded from the public table.

## Try the recorded scenario locally

Prerequisites: a prepared Python `>=3.14,<3.15` Hermes environment and the complete Hermes v0.23.0 Git source at `2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19`, including `tests.fakes.fake_llm_provider` (an arbitrary installed wheel is insufficient). Follow the pinned [Hermes setup instructions](https://github.com/NousResearch/hermes-agent/blob/2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19/CONTRIBUTING.md#development-setup) to prepare that environment. The demo preflights the interpreter, source HEAD/files and fake helper syntax/classes before creating output; it does not provision dependencies. Run from this checkout using a throwaway home outside any repository; replace the first two paths.

```sh
HERMES_PYTHON=/path/to/hermes-venv/bin/python
HERMES_SOURCE=/path/to/hermes-source
DEMO_HOME="$(mktemp -d)"
"$HERMES_PYTHON" demo/run.py --hermes-source "$HERMES_SOURCE" \
  --hermes-home "$DEMO_HOME" --model-provider fake --include-b2
CONTROL_HOME="$(mktemp -d)"
"$HERMES_PYTHON" demo/run.py --hermes-source "$HERMES_SOURCE" \
  --hermes-home "$CONTROL_HOME" --model-provider fake --include-b2 --no-plugin
```

`--veto {enforce,advisory}` defaults to `enforce`. To compare prompt-only reuse with the hook, run the same model and fixture in two fresh homes, once with `--veto advisory` and once with `--veto enforce`, keeping the plugin enabled in both. Advisory retains ruling prompts and the store guard, allows a re-ask, and records either T2 completion with a citation or a needs-input block. Transcripts record `veto`; result lines print `mode=`. A `--no-plugin` control records the selected mode but has no active plugin check. No real-model advisory/enforce pair is included in the published results yet.

Both fake commands should exit 0. Expected T2 result lines (the reason text is abbreviated here):

```text
treatment: T2 attempt-1 | done | . | ... | citation=True | path=veto | output=True | mode=enforce
control:   T2 attempt-1 | blocked | needs_input | ... | citation=False | path=. | output=False | mode=enforce
```

The harness installs the runtime plugin files from this repo into the new home, enables `plugins.isolation: in_process`, creates one board, and prints each result. An explicit `--hermes-home` or `HERMES_HOME` must be new or empty; without either, the harness creates one under its run directory. It never overwrites an existing configured profile. Both home and run directory must be outside any Git worktree: a parent walk rejects `.git` files or directories, including resolved symlink targets, before creating anything. `--repo` can select another local plugin checkout.

Before creating T1, a no-op runtime start initializes and closes the same `AIAgent` used by workers, without a conversation, model request or task claim. It retries once in a fresh process if dependency activation needs a restart; every warm-up exit, log and timeout is saved under `warmups`. `--warmup-timeout` defaults to 300 seconds per start, separate from the worker timeout. Two failed starts abort before T1; worker failures after warm-up still remain in `attempts`. Use an already installed runtime: real mode may trigger Hermes dependency setup if packages are missing.

Read the exact jobs in [demo/tasks.json](demo/tasks.json). The fixture writes local migration plans, never executes a database migration. T2 and T3 first write a useful draft with the decision unresolved. The human intervention is scripted and printed: `hermes precedent add ... --source-task <T1-id>`, then core `hermes kanban unblock <T1-id> --reason ...`. These are two operations, without a shared transaction. Control gives T1 the same human answer, but stores no ruling; T2 gets no answer on its own card.

**Launch-path limit:** v0.23.0's standard `hermes kanban dispatch` spawns a gateway owner client. To honor this experiment's no-gateway constraint, the harness uses the existing `dispatch_once(spawn_fn=...)` callback to launch local `AIAgent` subprocesses. CLI create/show/add/unblock/retire, core claiming/recovery, the model loop, tools and plugin hooks are real. No core functions are replaced. This adapter is pin-specific evidence, not a test of the default CLI dispatch or gateway path.

Each run prints its output directory and writes `<system-temp>/precedent-demo-runs/<run-id>/transcript.json` by default; `--out` selects another parent outside any repository. It records commands and return codes, warm-ups, every spawned attempt and PID/session/run ID, worker output, card snapshots, complete CLI event/run histories, artifacts, failures and fake-provider request/response bodies. Failed runs stay in separate run directories. Runtime homes and workspaces remain available after ordinary runs; tests remove their temporary homes. Transcripts retain their evidence.

Each step line prints citation and output presence plus `path`; schema 2 transcripts store `citation_path`. A syntactic citation marker passes when the word-bounded ruling ID `P-1` occurs, case-insensitively, in both a successful `kanban_complete` summary and the output file. The original fake phrase still passes. `veto` means a plugin-vetoed `kanban_block` preceded completion; `prompt` means completion had no preceding block call. No citation or an unclassified path is `null` (printed as `.`), including a human unblock after a committed block. Final assistant prose, rejected completion calls and block reasons do not count. T3's explicit rejection and T4's blocked/no-output checks remain unchanged. Marker detection does not establish that a ruling was correctly applied.

The fake provider scripts worker choices. It proves integration and durable outcomes, not a model's ability to recognize decisions or general savings. Real-model observations are limited to the Live run section above.

For a real-model run, have its API key already exported in the process environment. Replace the quoted placeholders; never put the key value in these arguments. API-key providers only, no OAuth/file credential fallback. Optional `--base-url` passes an endpoint to Hermes; provider/model are passed to task creation and the worker.

```sh
REAL_DEMO_HOME="$(mktemp -d)"
"$HERMES_PYTHON" demo/run.py --hermes-source "$HERMES_SOURCE" \
  --hermes-home "$REAL_DEMO_HOME" --model-provider '<PROVIDER>' \
  --model '<MODEL>' --provider-env '<PROVIDER_ENV>' --timeout 180 --warmup-timeout 300
REAL_CONTROL_HOME="$(mktemp -d)"
"$HERMES_PYTHON" demo/run.py --hermes-source "$HERMES_SOURCE" \
  --hermes-home "$REAL_CONTROL_HOME" --model-provider '<PROVIDER>' \
  --model '<MODEL>' --provider-env '<PROVIDER_ENV>' --timeout 180 --no-plugin --warmup-timeout 300
```

## What the fake run shows

| Step | With plugin | Without plugin |
| --- | --- | --- |
| T1, no ruling | `blocked`, `needs_input`, no final file | Same |
| Answer T1 | Add P-1, then core unblock; new worker writes `users-plan.md` and completes | Core unblock; new worker writes the same plan and completes |
| T2, same decision on a new card | Candidate veto, worker writes `orders-plan.md`, completes with `per precedent P-1`; no committed block | `blocked`, `needs_input`, no final file |
| T3, permission to drop a prod column | Rejects P-1 with a reason and blocks; no destructive plan | Blocks; no destructive plan |
| B2, no edits and final text after veto | Two workers exit with the card `running`; actual core recovery respawns; third attempt blocks with an uncited warning | First attempt blocks |
| Retire P-1, then T4 | Fresh worker blocks; zero active rulings, no final file | Fresh worker blocks |

[Slow harness test](tests/test_demo.py) asserts the actual files, citation/path fields, no-conversation warm-up, fresh processes, committed states and protocol-violation events. The [r4 test log](tests/evidence/tests-r4.txt) is historical test output; its local transcript paths are redacted. Generated `demo/out/` captures are private and excluded from the public repository.

## Candidate errors, measured without tuning

The 20 [held-out reasons](tests/corpus-heldout.json) were saved before rereading the matcher. The fixture uses the question above, keys `schema,migration`, and no aliases. Labels cover paraphrase, negation, scope and environment changes. Neither the matcher nor aliases were tuned after evaluation. These deliberately broad keys expose vocabulary collisions; prefer distinctive keys in actual use.

| Held-out candidate selection | Count |
| --- | ---: |
| Same decision, candidate shown | 7 |
| Same decision, candidate missed | 3 |
| Different decision, candidate shown | 9 |
| Different decision, no candidate | 1 |
| Correct candidate decisions | 8 / 20 |

These 8/20 results measure the word-based matcher used by the veto backstop; citations can also supply candidates independently of it. Both public r5 plugin runs took the T2 veto path. Active board rulings enter the prompt independently of matching; the public r5 captures do not demonstrate a prompt-only T2 completion.

[Every result and corpus hash](tests/evidence/heldout-r3.json) is preserved without tuning. These are candidate errors, not measured wrong actions, semantic accuracy or extra-turn costs. A worker may accept a false match, stop after a veto, or need a respawn.

The older [14-case review corpus](tests/matching-corpus.json) remains regression evidence: ten irrelevant questions still match its broad keys, and four repeats match supplied human aliases fitted to those examples. It is not held-out recall.

The matcher uses lowercase ASCII words, fixed stopwords and simple trailing-`s` stripping. Keys match whole tokens and all must appear. Without keys, questions and each alias require at least two shared words and 60% overlap. Results rank by overlap then newest ID, capped at three. Retirement removes a ruling from new matching and spawn context; it cannot erase a running worker's earlier context.

## Limits and failure behavior

In enforce mode, an active matching or cited ruling triggers up to two block-time vetoes without a valid stated exception, including quoted rulings; matching uses all explicit keys or keyless question overlap (also alias overlap), and checks text rather than correct application.
Held-out candidate selection was 8/20 correct: 7 repeats found, 3 missed, 9 different decisions shown and 1 correctly excluded (see the [table](#candidate-errors-measured-without-tuning)).

- Checks missing/`needs_input` kinds and `dependency` when public `kanban_show` finds no unsatisfied parent. Lookup failure checks conservatively; parent races and bypassed core paths remain outside the gate.
- A block-time citation must name an active matching ruling on this board with an intact ID, or include a whole ruling sentence normalized for case, punctuation and whitespace while preserving word order; it does not authorize asking the same question again. References inside decorated tokens and requests to ignore a ruling, ask again, disregard or override are treated as uncited. To block with an exception, `no precedent applies:` needs at least 20 characters, four distinct words after removing IDs/punctuation, and every candidate shown for this task. These remain text checks, not semantic truth: counts are not verified decisions, human answers or savings. No-candidate questions pass with a check line.
- Two vetoes per task/board, then a visibly warned escalation. Policy counts and candidate IDs survive respawn separately from analytics. Stats count attempts, not distinct questions, human answers or completed jobs.
- **B2:** public `pre_verify` continuation is available only after edits and below core's nudge cap. No-edit or cap-exhausted workers can exit without changing their running card. The scripted fake-provider local adapter shows requeue/requeue/warned-block with its chosen retry settings. No real-model B2 was run. Recovery relies on core dead-worker recovery and its retry settings; no recovery deadline is claimed. Advisory avoids this veto path. The offline `max_retries=1` test instead parks after the first exit. Default gateway ownership/timeout recovery has no demonstrated wall-time bound here.
- Marked `execute_code` and process stdin writes are denied conservatively. This may interrupt ordinary coding workflows. Literal file/terminal paths, traversal, symlinks and marker clearing are guarded; arbitrary shell obfuscation, foreign tools/filesystems and races are not contained.
- Locked JSONL and hashes detect ordinary changes, not a recomputed whole chain or deleted final suffix. Damage quarantines the board. Human `repair --truncate-after N` backs up the complete file and atomically checkpoints a clean prefix, preserves observed retirements/ID high-water, and conservatively retires retained entries after damage. Review before re-adding.
- Retirement never edits, reopens or blocks tasks. Review cited jobs manually; existing session prompts and completed outputs are not revoked.
- Analytics faults are visible where possible. Post-commit observer failures can lose observations. Policy-storage failure has a visible process-local fallback; persistence across respawns then cannot be guaranteed.
- Host isolation, other versions/platforms, other plugin combinations, real-model reliability beyond the three observations above, a board-document baseline and general savings remain untested. No wrapper, search, export or Desktop surface is included.

## How this differs from nearby plugins

- **ProofOps** seals receipts for checks a job declares. precedent-log stores a human's answer to a board question; in enforce mode a hook refuses a later worker's block that ignores a matching ruling.
- **hermes-assumption-ledger** verifies assumptions and gates turns when one is contradicted. precedent-log stores human rulings, not assumptions, and on retirement lists the completed jobs that relied on one.
- **Standing** changes approval requirements from check history and gates completion on proof. precedent-log never grants permission; a ruling only answers a repeated question.
- **Commonplace** keeps plain-file rules and memory for the agent. precedent-log scopes rulings to one Kanban board and checks reuse at block time.

## Related implementations

Descriptions of the first six entries follow the supplied 2026-11-06 research snapshot; the four added entries follow public PR/README sources read on 2026-11-07. These are not claims of exclusive functionality or tested coexistence. Sources can change after those dates.

| Project | Relevant scope |
| --- | --- |
| [kanban-empowered #147790](https://github.com/NousResearch/hermes-agent/pull/147790) | Structured per-card needs-input asks, vague-block veto, human reply/unblock and reminders. |
| [trust-ladder #149738](https://github.com/NousResearch/hermes-agent/pull/149738) | Corrections become tool guards, write checks or per-turn rules; the model can add rules. |
| [Hermes.Crew #149456](https://github.com/NousResearch/hermes-agent/pull/149456) | Coordinated execution, Kanban cards, human questions, proof checks and agent-written lessons. |
| [Project Stewardship #148048](https://github.com/NousResearch/hermes-agent/pull/148048) | Saves decisions as well as rules and facts, injects project context, and includes approvals and Kanban. |
| [Myeline #149277](https://github.com/NousResearch/hermes-agent/pull/149277) | Human review of AI facts, approved-memory search and reasoned retirement. |
| [no-cap #149272](https://github.com/NousResearch/hermes-agent/pull/149272) | Claim receipts and human-approved scoped coaching rules with review/revert. |
| [ProofOps #149625](https://github.com/NousResearch/hermes-agent/pull/149625) | Tool/CLI-run declared checks produce sealed receipts with evidence and limitations; bundled verification skill, no hooks. |
| [hermes-assumption-ledger #150212](https://github.com/NousResearch/hermes-agent/pull/150212) | Captures operational assumptions with provenance, verifies deterministically, and gates turns when decisions depend on contradicted assumptions. |
| [Standing #150366](https://github.com/NousResearch/hermes-agent/pull/150366) | Check history changes approval requirements; task completion requires a passing proof for the profile, task and session. |
| [Commonplace #150245](https://github.com/NousResearch/hermes-agent/pull/150245) | Plain-file rules, curated memory, journals and handovers; transcript checkpoints can block compression if archiving fails and checkpoints are required. |

## Disclosures (catalog rule 13)

**Installed plugin:** no network, model calls, shell execution, credentials or background processes. Reads core board metadata and public `kanban_show` task/events. Direct writes are confined by convention and guards to `<HERMES_HOME>/precedent-log/`: rulings, locks, events, policy state, torn-event fragments and repair backups. Events store timestamps, task IDs and reasons; no automatic retention or external anchor. No plugin SQL or telemetry. Unmarked same-user access remains possible.

**Registrations:** five hooks (`pre_tool_call`, `kanban_task_blocked`, `pre_verify`, `post_tool_call`, `on_session_end`), two slash commands, one CLI command (`precedent`: add, retire, repair, list, show, verify, stats, cited-by) and one bounded prompt section; no model tools or middleware. Four private helpers remain (public API request drafted in [catalog/CORE-ISSUE.md](catalog/CORE-ISSUE.md), not submitted): `get_current_board`, `kanban_db_path`, `owned_kanban_task`, `is_delegated_child_process_context`. They resolve board/execution identity and carry catalog rule 9 compatibility/admission risk. No core functions are replaced.

**Opt-in demo:** reads the supplied Hermes source and local repository; copies only runtime plugin files into an empty lab home; writes config, boards, worker data, artifacts and transcripts. Starts bounded local subprocesses and, in fake mode, a loopback HTTP server. The supplied Python audit-hook checks apply to the in-process harness only. Subprocesses, native network and native file access are outside those checks. This is not an OS sandbox; run the demo in a throwaway home outside any repository. See [demo limits](demo/README.md). Real mode sends task/context data to the explicitly selected provider and can incur its charges. Only the named environment credential is forwarded; its value is redacted from transcripts and never written to config. The adapter uses additional private core Python entrypoints; it is not installed as plugin runtime.

The [catalog template](catalog/precedent-log.yaml) intentionally contains a SHA placeholder, the matching version, all five hook names, an explicit command/section inventory, empty tools/middleware/env declarations, and Linux/macOS platform limits. The catalog schema has no command/section capability fields, so their inventory is recorded as YAML comments. An actual catalog submission must replace the placeholder with the full reviewed commit and pin its documentation and image URLs to that commit. Private-helper warnings remain for maintainer review; validation does not decide catalog admission.

## Verification

Set `HERMES_SOURCE` to the prepared pinned Hermes source and `HERMES_PYTHON` to its Python 3.14 interpreter, as in the [scenario prerequisites](#try-the-recorded-scenario-locally). From this repository:

```sh
HERMES_SOURCE="$HERMES_SOURCE" PYTHONDONTWRITEBYTECODE=1 \
  "$HERMES_PYTHON" -B tests/run_offline.py
python3 -B evidence/live-r5/recompute.py --check-readme
```

All 142 offline tests pass, including the always-on privacy check and the configured external denylist. The offline runner includes every non-network test. It excludes only the existing slow loopback fake-provider test under this revision's no-network/no-provider constraint; all offline B2 tests remain. The optional additional private denylist is skipped when `PRECEDENT_PRIVATE_DENYLIST` is unset. Supply a newline-delimited denylist outside the repo to enable it; matches are not echoed into logs. The 0.2.1 result is recorded in [evidence/tests-r13.txt](evidence/tests-r13.txt).

Run privacy alone, without Hermes, using `python3 -B tests/test_publication.py`. A clean archive scans all exported files. The checks reject absolute user-home paths, emails, provider keys and base64-like blobs longer than 120 characters. Redaction rules and per-file counts are in [REDACTIONS.md](evidence/live-r5/REDACTIONS.md); private prefixes are passed as arguments to [redact.py](evidence/redact.py), never committed.

Historical [r5 offline](evidence/tests-r5.txt) and [r4 full-suite](tests/evidence/tests-r4.txt) logs are retained with paths sanitized. To run the network-using suite in a permitted environment, use `"$HERMES_PYTHON" -m unittest discover -s tests -v` with the same `HERMES_SOURCE`.

Tests use isolated temporary homes and keep Hermes source unchanged. The offline checks launch no gateway and make no provider calls. [Held-out matcher results](tests/evidence/heldout-r3.json) are unchanged.

# Live r5 public evidence

All 89 source transcripts, attempt records (including both warm-up starts), and workspace files are copied. No messages, failed starts, worker results or output files are dropped. Source files are unchanged. Hermes homes are not included. `__fixtures__/` is the scanner-recognized inert data path; the plugin never imports these recordings.

an earlier private run inside a git checkout was discarded because the worker could read unrelated files; it is not used as evidence

## Rules

Private prefixes are supplied only on the command line, never stored in this script or report. The ordered rules below name only their replacement placeholders. Counts include duplicated text in transcripts and standalone records.

- P1: supplied prefix 1 becomes `<run-root>` (literal replacement, in argument order).
- P2: supplied prefix 2 becomes `<hermes-source>` (literal replacement, in argument order).
- P3: supplied prefix 3 becomes `<hermes-lab>` (literal replacement, in argument order).
- P4: supplied prefix 4 becomes `<plugin>` (literal replacement, in argument order).
- P5: supplied account label 5 becomes `<user>` (literal replacement, in argument order).
- H: any remaining absolute macOS or Linux user-home prefix becomes `<home>`; suffixes remain.
- O: each maximal base64-like or URL-safe token longer than 120 characters becomes `<opaque N chars>`, where N is its original length. The alphabet is ASCII letters, digits, underscore, plus, slash, equals and hyphen.
- D: literal and JSON-escaped U+2014 punctuation becomes a colon. No wording is paraphrased.

## Per-file replacement counts

| File | P1 | P2 | P3 | P4 | P5 | H | O | D |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `__fixtures__/haiku-r5/attempts/001-t_edef9cc5-result.json` | 4 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| `__fixtures__/haiku-r5/attempts/001-t_edef9cc5-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/002-t_edef9cc5-result.json` | 12 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/haiku-r5/attempts/002-t_edef9cc5-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/003-t_188f724b-result.json` | 13 | 0 | 0 | 0 | 0 | 0 | 6 | 1 |
| `__fixtures__/haiku-r5/attempts/003-t_188f724b-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/004-t_5e06caca-result.json` | 11 | 0 | 0 | 0 | 0 | 0 | 6 | 2 |
| `__fixtures__/haiku-r5/attempts/004-t_5e06caca-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/005-t_5392830b-result.json` | 10 | 0 | 0 | 0 | 0 | 0 | 4 | 2 |
| `__fixtures__/haiku-r5/attempts/005-t_5392830b-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/dispatch-1.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/dispatch-2.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/dispatch-3.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/dispatch-4.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/dispatch-5.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/tick-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/tick-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/tick-3.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/tick-4.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/tick-5.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/warmup-1-result.json` | 0 | 8 | 0 | 1 | 0 | 0 | 0 | 3 |
| `__fixtures__/haiku-r5/attempts/warmup-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/warmup-2-result.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/attempts/warmup-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/transcript.json` | 208 | 9 | 2 | 3 | 0 | 0 | 24 | 9 |
| `__fixtures__/haiku-r5/workspaces/T1/users-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/workspaces/T2/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/workspaces/T2/orders-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/workspaces/T3/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5/workspaces/T4/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/001-t_1b816c61-result.json` | 4 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| `__fixtures__/sonnet-r5/attempts/001-t_1b816c61-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/002-t_1b816c61-result.json` | 11 | 0 | 0 | 0 | 0 | 0 | 2 | 1 |
| `__fixtures__/sonnet-r5/attempts/002-t_1b816c61-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/003-t_af95aeae-result.json` | 13 | 0 | 0 | 0 | 0 | 0 | 2 | 1 |
| `__fixtures__/sonnet-r5/attempts/003-t_af95aeae-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/004-t_69b31b55-result.json` | 8 | 0 | 0 | 0 | 0 | 0 | 2 | 4 |
| `__fixtures__/sonnet-r5/attempts/004-t_69b31b55-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/005-t_85f6599b-result.json` | 46 | 0 | 0 | 0 | 2 | 0 | 11 | 2 |
| `__fixtures__/sonnet-r5/attempts/005-t_85f6599b-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/dispatch-1.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/dispatch-2.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/dispatch-3.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/dispatch-4.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/dispatch-5.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/tick-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/tick-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/tick-3.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/tick-4.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/tick-5.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/warmup-1-result.json` | 0 | 8 | 0 | 1 | 0 | 0 | 0 | 3 |
| `__fixtures__/sonnet-r5/attempts/warmup-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/warmup-2-result.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/attempts/warmup-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/transcript.json` | 224 | 9 | 2 | 3 | 2 | 0 | 19 | 11 |
| `__fixtures__/sonnet-r5/workspaces/T1/users-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/workspaces/T2/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/workspaces/T2/orders-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/sonnet-r5/workspaces/T3/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| `__fixtures__/sonnet-r5/workspaces/T4/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/001-t_0c017c64-result.json` | 4 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| `__fixtures__/haiku-r5-control/attempts/001-t_0c017c64-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/002-t_0c017c64-result.json` | 11 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/haiku-r5-control/attempts/002-t_0c017c64-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/003-t_14c63913-result.json` | 8 | 0 | 0 | 0 | 0 | 0 | 6 | 1 |
| `__fixtures__/haiku-r5-control/attempts/003-t_14c63913-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/004-t_c46be75c-result.json` | 9 | 0 | 0 | 0 | 0 | 0 | 6 | 1 |
| `__fixtures__/haiku-r5-control/attempts/004-t_c46be75c-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/005-t_174df156-result.json` | 8 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/haiku-r5-control/attempts/005-t_174df156-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/dispatch-1.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/dispatch-2.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/dispatch-3.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/dispatch-4.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/dispatch-5.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/tick-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/tick-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/tick-3.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/tick-4.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/tick-5.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/warmup-1-result.json` | 0 | 8 | 0 | 1 | 0 | 0 | 0 | 3 |
| `__fixtures__/haiku-r5-control/attempts/warmup-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/warmup-2-result.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/attempts/warmup-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/transcript.json` | 181 | 9 | 2 | 3 | 0 | 0 | 24 | 7 |
| `__fixtures__/haiku-r5-control/workspaces/T1/users-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/workspaces/T2/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/workspaces/T3/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/haiku-r5-control/workspaces/T4/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Total | 962 | 51 | 6 | 12 | 4 | 0 | 134 | 55 |

## Recompute and limits

Run `python3 -B evidence/live-r5/recompute.py --check-readme` from the plugin checkout. It checks the exact fixture inventory, SHA-256 hashes, attempt records and output files, then derives the table from recorded commands, states and tool exchanges. Original in-transcript hashes and byte counts describe original bytes, before redaction; the manifest covers public bytes and does not authenticate authorship.

Three runs, one model family (Claude Haiku 5.5 and Sonnet 5.5), warm-up used, no real B2. The supplied r5 run used a clean archive of bee2e2c outside Git. All three first warm-up starts exited 1 before a successful retry; all worker exits were 0. T3 explicitly instructs rejection of non-matching rulings, so it is an instruction-following observation, not a safety evaluation. The local dispatch adapter is not the standard gateway. T2 path labels describe tool traces, not internal reasoning. In the discarded private r3 runs, one Haiku T2 took the prompt path; it is not public evidence.

## r18 hostname scrub

N: runtime-supplied hostname, any case, short or with local suffix, becomes `<host>` via `redact.py`. 111 replacements across 18 files in live-r5. No hostname value is stored. Manifest hashes now cover these redacted bytes; recorded outcomes are unchanged.

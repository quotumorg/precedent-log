# Live r14 public evidence

All 176 source transcripts, attempt records (including all warm-up starts), and workspace files are copied. No messages, failed starts, worker results or output files are dropped. Source files are unchanged. Hermes homes are not included. `__fixtures__/` is the scanner-recognized inert data path; the plugin never imports these recordings.

## Rules

Private prefixes are supplied only on the command line, never stored in this script or report. The ordered rules below name only their replacement placeholders. Counts include duplicated text in transcripts and standalone records.

- P1: supplied prefix 1 becomes `<run-root>` (literal replacement, in argument order).
- P2: supplied prefix 2 becomes `<run-root>` (literal replacement, in argument order).
- P3: supplied prefix 3 becomes `<run-root>` (literal replacement, in argument order).
- P4: supplied prefix 4 becomes `<capture-root>` (literal replacement, in argument order).
- P5: supplied prefix 5 becomes `<plugin-source>` (literal replacement, in argument order).
- P6: supplied prefix 6 becomes `<plugin-source>` (literal replacement, in argument order).
- P7: supplied prefix 7 becomes `<hermes-source>` (literal replacement, in argument order).
- P8: supplied prefix 8 becomes `<hermes-lab>` (literal replacement, in argument order).
- P9: supplied prefix 9 becomes `<home>` (literal replacement, in argument order).
- P10: supplied prefix 10 becomes `<private-root>` (literal replacement, in argument order).
- P11: supplied prefix 11 becomes `<provider-endpoint>` (literal replacement, in argument order).
- H: any remaining absolute macOS or Linux user-home prefix becomes `<home>`; suffixes remain.
- O: each maximal base64-like or URL-safe token longer than 120 characters becomes `<opaque N chars>`, where N is its original length. The alphabet is ASCII letters, digits, underscore, plus, slash, equals and hyphen.
- D: literal and JSON-escaped U+2014 punctuation becomes a colon. No wording is paraphrased.

## Per-file replacement counts

| File | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 | H | O | D |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `__fixtures__/rec-treatment/attempts/001-t_f3db3dee-result.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| `__fixtures__/rec-treatment/attempts/001-t_f3db3dee-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/002-t_f3db3dee-result.json` | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/rec-treatment/attempts/002-t_f3db3dee-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/003-t_b22a8c72-result.json` | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 1 |
| `__fixtures__/rec-treatment/attempts/003-t_b22a8c72-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/004-t_b85a0844-result.json` | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 2 |
| `__fixtures__/rec-treatment/attempts/004-t_b85a0844-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/005-t_62046cb5-result.json` | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 2 |
| `__fixtures__/rec-treatment/attempts/005-t_62046cb5-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/dispatch-1.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/dispatch-2.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/dispatch-3.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/dispatch-4.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/dispatch-5.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/tick-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/tick-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/tick-3.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/tick-4.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/tick-5.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/warmup-1-result.json` | 0 | 0 | 0 | 0 | 1 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| `__fixtures__/rec-treatment/attempts/warmup-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/warmup-2-result.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/attempts/warmup-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/transcript.json` | 209 | 0 | 0 | 0 | 3 | 0 | 9 | 2 | 0 | 0 | 0 | 0 | 24 | 9 |
| `__fixtures__/rec-treatment/workspaces/T1/users-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/workspaces/T2/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/workspaces/T2/orders-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/workspaces/T3/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment/workspaces/T4/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/001-t_226d49be-result.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| `__fixtures__/rec-treatment-2/attempts/001-t_226d49be-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/002-t_226d49be-result.json` | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/rec-treatment-2/attempts/002-t_226d49be-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/003-t_0212fda3-result.json` | 18 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 1 |
| `__fixtures__/rec-treatment-2/attempts/003-t_0212fda3-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/004-t_ff2f563e-result.json` | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 2 |
| `__fixtures__/rec-treatment-2/attempts/004-t_ff2f563e-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/005-t_955d1a24-result.json` | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 2 |
| `__fixtures__/rec-treatment-2/attempts/005-t_955d1a24-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/dispatch-1.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/dispatch-2.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/dispatch-3.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/dispatch-4.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/dispatch-5.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/tick-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/tick-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/tick-3.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/tick-4.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/tick-5.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/warmup-1-result.json` | 0 | 0 | 0 | 0 | 1 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| `__fixtures__/rec-treatment-2/attempts/warmup-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/warmup-2-result.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/attempts/warmup-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/transcript.json` | 211 | 0 | 0 | 0 | 3 | 0 | 9 | 2 | 0 | 0 | 0 | 0 | 26 | 9 |
| `__fixtures__/rec-treatment-2/workspaces/T1/users-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/workspaces/T2/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/workspaces/T2/orders-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/workspaces/T3/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-treatment-2/workspaces/T4/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/001-t_7038e8da-result.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| `__fixtures__/rec-advisory/attempts/001-t_7038e8da-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/002-t_7038e8da-result.json` | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/rec-advisory/attempts/002-t_7038e8da-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/003-t_19ac9b02-result.json` | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 2 |
| `__fixtures__/rec-advisory/attempts/003-t_19ac9b02-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/004-t_061e472b-result.json` | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/rec-advisory/attempts/004-t_061e472b-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/005-t_7fe97a47-result.json` | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/rec-advisory/attempts/005-t_7fe97a47-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/dispatch-1.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/dispatch-2.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/dispatch-3.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/dispatch-4.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/dispatch-5.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/tick-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/tick-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/tick-3.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/tick-4.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/tick-5.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/warmup-1-result.json` | 0 | 0 | 0 | 0 | 1 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| `__fixtures__/rec-advisory/attempts/warmup-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/warmup-2-result.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/attempts/warmup-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/transcript.json` | 186 | 0 | 0 | 0 | 3 | 0 | 9 | 2 | 0 | 0 | 0 | 0 | 20 | 8 |
| `__fixtures__/rec-advisory/workspaces/T1/users-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/workspaces/T2/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| `__fixtures__/rec-advisory/workspaces/T3/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory/workspaces/T4/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/001-t_9fe128ef-result.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| `__fixtures__/rec-advisory-2/attempts/001-t_9fe128ef-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/002-t_9fe128ef-result.json` | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/rec-advisory-2/attempts/002-t_9fe128ef-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/003-t_df382875-result.json` | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 1 |
| `__fixtures__/rec-advisory-2/attempts/003-t_df382875-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/004-t_96c0e632-result.json` | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 1 |
| `__fixtures__/rec-advisory-2/attempts/004-t_96c0e632-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/005-t_8d769e61-result.json` | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/rec-advisory-2/attempts/005-t_8d769e61-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/dispatch-1.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/dispatch-2.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/dispatch-3.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/dispatch-4.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/dispatch-5.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/tick-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/tick-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/tick-3.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/tick-4.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/tick-5.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/warmup-1-result.json` | 0 | 0 | 0 | 0 | 1 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| `__fixtures__/rec-advisory-2/attempts/warmup-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/warmup-2-result.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/attempts/warmup-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/transcript.json` | 193 | 0 | 0 | 0 | 3 | 0 | 9 | 2 | 0 | 0 | 0 | 0 | 24 | 7 |
| `__fixtures__/rec-advisory-2/workspaces/T1/users-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/workspaces/T2/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/workspaces/T2/orders-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/workspaces/T3/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-advisory-2/workspaces/T4/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/001-t_6f7f855b-result.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| `__fixtures__/rec-control/attempts/001-t_6f7f855b-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/002-t_6f7f855b-result.json` | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/rec-control/attempts/002-t_6f7f855b-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/003-t_619e4710-result.json` | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/rec-control/attempts/003-t_619e4710-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/004-t_7229ae64-result.json` | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 3 |
| `__fixtures__/rec-control/attempts/004-t_7229ae64-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/005-t_46495bcd-result.json` | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 |
| `__fixtures__/rec-control/attempts/005-t_46495bcd-spec.json` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/dispatch-1.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/dispatch-2.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/dispatch-3.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/dispatch-4.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/dispatch-5.json` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/tick-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/tick-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/tick-3.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/tick-4.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/tick-5.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/warmup-1-result.json` | 0 | 0 | 0 | 0 | 1 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| `__fixtures__/rec-control/attempts/warmup-1.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/warmup-2-result.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/attempts/warmup-2.json` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/transcript.json` | 211 | 0 | 0 | 0 | 3 | 0 | 9 | 2 | 0 | 0 | 0 | 0 | 22 | 9 |
| `__fixtures__/rec-control/workspaces/T1/users-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/workspaces/T2/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/workspaces/T3/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/rec-control/workspaces/T4/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/001-t_ff095919-result.json` | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/001-t_ff095919-spec.json` | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/002-t_ff095919-result.json` | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 4 |
| `__fixtures__/ds-9a06-1/attempts/002-t_ff095919-spec.json` | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/003-t_03cdde8b-result.json` | 0 | 0 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 25 |
| `__fixtures__/ds-9a06-1/attempts/003-t_03cdde8b-spec.json` | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/004-t_b0d2242b-result.json` | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 8 |
| `__fixtures__/ds-9a06-1/attempts/004-t_b0d2242b-spec.json` | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/005-t_2307cfe0-result.json` | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 6 |
| `__fixtures__/ds-9a06-1/attempts/005-t_2307cfe0-spec.json` | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/dispatch-1.json` | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/dispatch-2.json` | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/dispatch-3.json` | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/dispatch-4.json` | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/dispatch-5.json` | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/tick-1.json` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/tick-2.json` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/tick-3.json` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/tick-4.json` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/tick-5.json` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/warmup-1-result.json` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/attempts/warmup-1.json` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/transcript.json` | 0 | 0 | 195 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 5 | 0 | 0 | 104 |
| `__fixtures__/ds-9a06-1/workspaces/T1/users-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `__fixtures__/ds-9a06-1/workspaces/T2/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| `__fixtures__/ds-9a06-1/workspaces/T2/orders-plan.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| `__fixtures__/ds-9a06-1/workspaces/T3/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| `__fixtures__/ds-9a06-1/workspaces/T4/draft.md` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Total | 1560 | 0 | 290 | 1 | 20 | 0 | 86 | 11 | 0 | 0 | 21 | 0 | 232 | 250 |

## Recompute and limits

Run `python3 -B evidence/live-r14/recompute.py --check-readme` from the plugin checkout. It checks the exact fixture inventory, SHA-256 hashes, attempt records and output files, then derives the table from recorded commands, states and tool exchanges. Original in-transcript hashes and byte counts describe original bytes, before redaction; the manifest covers public bytes and does not authenticate authorship.

Six runs, two model families, one fixture, no real B2. Supplied provenance: public codeload export of 9a06174 outside Git, Hermes v0.23.0 at 2bd378ed, demo/run.py, worker timeout 180 seconds and warm-up timeout 300 seconds. Five Haiku runs used the Anthropic API; deepseek-v4-pro used Venice (OpenAI-compatible endpoint). All five Haiku first warm-ups exited 1, then 0; the DeepSeek warm-up exited 0. All 30 worker attempts exited 0. Advisory Run 2 left T2 blocked despite writing its final file and recorded one harness failure; the other five runs recorded none. Both advisory T2 outcomes remain blocked. T2 explicitly requests a block to test escalation; T3 instructs rejection of non-matching rulings. These are fixture-specific observations, not a reliability estimate or safety evaluation. The local dispatch adapter is not the standard gateway. Path labels describe tool traces, not internal reasoning. Provenance is supplied by the capture owner, not authenticated by the manifest.

## r18 hostname scrub

N: runtime-supplied hostname, any case, short or with local suffix, becomes `<host>` via `redact.py`. 226 replacements across 36 files in live-r14. No hostname value is stored. Manifest hashes now cover these redacted bytes; recorded outcomes are unchanged.

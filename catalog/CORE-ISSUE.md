# Draft: public board, DB-path and execution-identity resolvers for plugins

Not submitted. Request against Hermes v0.23.0, commit `2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19`.

Precedent Log stores rulings per active profile and board, renders them into a worker prompt, and checks `kanban_block` through public hooks. It needs the same board and ownership identity that core uses for the eventual transition. Currently four runtime call sites read undocumented helpers:

| Plugin call site | Current helper | Needed public contract |
| --- | --- | --- |
| `precedent_log/store.py:resolve_board` | `hermes_cli.kanban_db.get_current_board()` | Current board after scoped override, environment and shared pointer resolution |
| `precedent_log/store.py:call_board` | `hermes_cli.kanban_db.kanban_db_path(board=...)` | Effective board and canonical DB path, honoring dispatcher/machine pins and explicit/scoped selection |
| `precedent_log/guard.py:worker_task` | `agent.delegation_context.owned_kanban_task()` | Current owned Kanban task identity, excluding delegated child and cron contexts |
| `precedent_log/guard.py:is_worker_or_child` | `agent.delegation_context.is_delegated_child_process_context()` | Execution identity that includes in-process delegated children as well as subprocess markers |

Could `PluginContext` expose read-only current-board, effective DB-path/board and execution-identity resolvers with these semantics? Please specify how they behave under profile multiplexing, named/default boards, contradictory environment markers, custom database pins, delegated children, CLI commands and plugin-host isolation. A structured board/path result would remove plugins' need to infer a board from a physical path. An ambiguous custom pin should return an explicit error.

No helper is replaced, wrapped or rebound by the plugin. The four private calls remain in this revision; validation warnings are not an admission decision. Tests use the real prompt renderer for contradictory P-1 entries across both boards and profiles, and the real block transition for both standard DB-pin directions. Current support is in-process only on the single tested Hermes revision.

Separately, `pre_verify` runs only after edits and below the core nudge cap. A vetoed block can be followed by a no-edit final response while the card remains running. Enforce mode retains this B2 limitation; advisory avoids vetoing. A future public successful-terminal-transition/stop contract would help, but this draft requests no plugin-specific core patch or recovery deadline.

"""Public Hermes plugin entry point."""

from .precedent_log import commands, gate, guard, section, stats
from .precedent_log.continuation import Continuation


def register(ctx):
    continuation = Continuation()
    def pre_tool_call(tool_name=None, args=None, **kwargs):
        # Session cwd can differ from gateway cwd: hermes_cli/plugins.py:597-600.
        try:
            cwd = ctx.session_cwd()
        except Exception:
            if guard.is_worker_or_child() and (tool_name in {
                    "write_file", "patch", "terminal", "execute_code", "process_manage"} or any(
                    key in (args or {}) for key in ("output_path", "save_path", "destination", "dest_path"))):
                return {"action": "block", "message": "[precedent-log] store guard unavailable; session cwd lookup failed"}
            cwd = ""
        kwargs.setdefault("cwd", cwd)
        directive = gate.pre_tool_call(tool_name, args, ctx=ctx, **kwargs)
        continuation.before(tool_name, directive, **kwargs)
        return directive

    def on_blocked(**kwargs):
        return stats.on_blocked(ctx=ctx, **kwargs)

    ctx.register_hook("pre_tool_call", pre_tool_call)
    ctx.register_hook("kanban_task_blocked", on_blocked)
    ctx.register_hook("pre_verify", continuation.pre_verify)
    ctx.register_hook("post_tool_call", continuation.after)
    ctx.register_hook("on_session_end", continuation.finish)
    ctx.register_command("ruling", commands.ruling, description="Add or retire a human ruling",
                         args_hint="add <question> => <ruling> [keys: a, b] | retire P-n <reason>")
    ctx.register_command("rulings", commands.rulings, description="List active board rulings")
    ctx.register_cli_command("precedent", "Human Kanban rulings", commands.setup_cli, commands.cli)
    ctx.register_system_prompt_section("precedent-log.board", section.render,
                                       position="after_memory", max_chars=4000)

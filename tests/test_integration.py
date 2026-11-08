import support

import shutil

from support import IsolatedTest, REPO


class IntegrationTests(IsolatedTest):
    def test_real_loader_registrations_and_core_dispatch(self):
        destination = self.home / "plugins" / "precedent-log"
        shutil.copytree(REPO, destination, ignore=shutil.ignore_patterns(".git", ".scratch", "__pycache__", "*.pyc", "demo", "tests", "evidence", "catalog"))
        (self.home / "config.yaml").write_text(
            "plugins:\n  enabled: [precedent-log]\n  isolation: in_process\n"
        )
        code = r'''
import argparse
import contextlib
import io
import os
from pathlib import Path
from hermes_cli import plugins
from hermes_cli.plugin_command_dispatch import invoke_plugin_command

manager = plugins.get_plugin_manager()
manager.discover_and_load()
loaded = manager._plugins['precedent-log']
assert loaded.enabled, loaded
owned = lambda entry: entry.get('plugin') == 'precedent-log'
commands = {name: entry for name, entry in manager._plugin_commands.items() if owned(entry)}
cli = {name: entry for name, entry in manager._cli_commands.items() if owned(entry)}
sections = {name: entry for name, entry in manager._system_prompt_sections.items() if entry.plugin == 'precedent-log'}
assert set(commands) == {'ruling', 'rulings'}, commands
assert set(cli) == {'precedent'}, cli
assert set(sections) == {'precedent-log.board'}, sections
assert sections['precedent-log.board'].max_chars == 4000
hooks = {name for name, callbacks in manager._hooks.items()
         if any('precedent_log' in callback.__module__ for callback in callbacks)}
assert hooks == {'pre_tool_call', 'kanban_task_blocked', 'pre_verify', 'post_tool_call', 'on_session_end'}, hooks
manifest = loaded.manifest
assert set(manifest.provides_hooks) == hooks
assert not manifest.provides_tools and not manifest.requires_env and not manifest.python_dependencies
assert "Saves a human's answer to a blocked Kanban question" in manifest.description
assert 'precedent_log.guard: strict' in manifest.description
assert manifest.version == '0.4.2'
assert invoke_plugin_command(commands['ruling']['handler'],
    'add staging prod migrations => Use staging [keys: staging, prod]',
    platform='cli', session_key='integration') == 'Added P-1'
assert 'P-1: Use staging' in invoke_plugin_command(commands['rulings']['handler'], '')
parser = argparse.ArgumentParser()
cli['precedent']['setup_fn'](parser)
with contextlib.redirect_stdout(io.StringIO()) as output:
    cli['precedent']['handler_fn'](parser.parse_args(['show', 'P-1']))
assert 'cli:integration' in output.getvalue()
os.environ['HERMES_KANBAN_TASK'] = 't_integration'
# This is the same dispatcher the agent loop calls, not a fake hook invocation.
# agent/agent_runtime_helpers.py:2454-2467 and hermes_cli/plugins.py:2019-2028.
message, modified = plugins._dispatch_pre_tool_call_hooks(
    'kanban_block', {'reason': 'staging prod migrations', 'kind': 'needs_input'},
    task_id='turn-not-task', session_id='integration', tool_call_id='call1')
assert message and 'P-1: Use staging' in message, (message, modified)
assert 'kanban_complete' in message and 'kanban_block' in message
os.environ['HERMES_KANBAN_TASK'] = 't_other'
message, modified = plugins._dispatch_pre_tool_call_hooks(
    'kanban_block', {'reason': 'new vendor question', 'kind': 'needs_input'},
    task_id='turn-not-task', session_id='integration', tool_call_id='call2')
assert message is None and '[precedent-log] checked 1 active rulings' in modified['reason']
rendered = plugins.render_system_prompt_sections({'session_id': 'integration', 'cwd': str(Path.cwd())})
assert any(section.id == 'precedent-log.board' and 'ruling: "Use staging"' in section.content for section in rendered)
assert invoke_plugin_command(commands['ruling']['handler'], 'retire P-1 old').startswith('marked workers cannot change rulings.')
print('Real loader: 5 hooks, 2 slash commands, 1 CLI, 1 prompt section; core block/modify directives verified.')
'''
        result = self.process(code)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout.strip(), flush=True)

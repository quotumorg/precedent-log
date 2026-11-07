"""Offline real loader, tool transitions, stop gates and dead-worker recovery."""

import support

import contextlib
import json
import os
import shutil
from types import SimpleNamespace
from unittest.mock import patch

from support import IsolatedTest, REPO
from precedent_log.gate import pre_tool_call
from precedent_log.stats import Events, on_blocked
from precedent_log.store import Store, call_board


QUESTION = 'staging or prod DB for migrations?'
ANSWER = 'Use staging. Prod needs a human.'
LOAD = '''
import json, os
from pathlib import Path
from hermes_cli import plugins, kanban_db as kb, kanban_db_connect as kbc
from model_tools import handle_function_call
from precedent_log.store import Store
manager = plugins.get_plugin_manager()
manager.discover_and_load()
assert manager._plugins['precedent-log'].enabled
'''


class CoreTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        Store().add(QUESTION, ANSWER, ['staging', 'prod', 'migrations'])

    def ctx(self):
        from hermes_cli import plugins
        from hermes_cli.plugins_manifest import PluginManifest
        from tools import kanban_tools
        return plugins.PluginContext(PluginManifest(name='offline-probe', version='0.0.0', description='Offline'), plugins.get_plugin_manager())

    def loaded(self, code):
        destination = self.home / 'plugins/precedent-log'
        shutil.copytree(REPO, destination, ignore=shutil.ignore_patterns('.git', '.scratch', '__pycache__', '*.pyc', 'demo', 'tests', 'evidence', 'catalog'))
        (self.home / 'config.yaml').write_text('plugins:\n  enabled: [precedent-log]\n  isolation: in_process\nterminal:\n  env_type: local\n')
        result = self.process(LOAD + code, HERMES_VERIFY_ON_STOP='0')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        if result.stdout.strip():
            print(result.stdout.strip(), flush=True)

    def test_real_loaded_dispatch_refuses_review_write_routes(self):
        self.loaded(r'''
store = Store()
before = store.path.read_bytes()
state = store.read()
from precedent_log.store import canonical, digest
row = dict(state.entries['P-1'])
row.update(id='P-2', ruling='Forged ruling', prev=state.tail)
row.pop('retired')
row['h'] = digest(row)
import shlex
home = Path(os.environ['HOME'])
(home / 'rules').symlink_to(store.directory, target_is_directory=True)
(home / 'payload.py').write_text("from precedent_log.store import Store\nStore().add('forged question', 'Forged answer')\n")
os.environ['HERMES_KANBAN_TASK'] = 't_guard'
calls = [
    ('terminal', {'command': "printf '%s\\n' " + shlex.quote(canonical(row)) + ' >> default.jsonl', 'workdir': str(store.directory)}),
    ('terminal', {'command': 'tee -a default.jsonl', 'workdir': str(store.directory), 'background': True}),
    ('terminal', {'command': 'cp replacement.jsonl rules/default.jsonl', 'workdir': str(home)}),
    ('terminal', {'command': 'env -u HERMES_KANBAN_TASK -u HERMES_DELEGATED_CHILD_CONTEXT hermes precedent --board default add --question forged --ruling forged'}),
    ('execute_code', {'code': "import runpy; runpy.run_path('payload.py')"}),
    ('process_manage', {'action': 'submit', 'session_id': 'owned', 'data': canonical(row)}),
]
for tool, args in calls:
    result = json.loads(handle_function_call(tool, args, session_id='guard', turn_id='one'))
    assert 'marked workers cannot change rulings' in str(result), (tool, result)
assert store.path.read_bytes() == before
assert store.verify()['ok']
print('Actual loader + tool dispatcher: all six review write routes refused; store unchanged.')
''')

    def test_real_loaded_completion_records_reliance_and_cli_retirement(self):
        self.loaded(r'''
from precedent_log.stats import Events
from precedent_log.commands import cli, setup_cli
import argparse
with kbc.connect_closing() as conn:
    tid = kb.create_task(conn, title='Offline reliance test', assignee='worker')
    claimed = kb.claim_task(conn, tid)
    os.environ.update(HERMES_KANBAN_TASK=tid, HERMES_KANBAN_RUN_ID=str(claimed.current_run_id))
    done = json.loads(handle_function_call('kanban_complete', {'summary': 'P-1: used staging'},
                                          session_id='reliance', turn_id='one'))
    assert done.get('ok'), done
    assert kb.get_task(conn, tid).status == 'done'
    rows = Events().cited_by('P-1')
    assert len(rows) == 1 and rows[0]['task_id'] == tid and rows[0]['event'] == 'relied', rows
    os.environ.pop('HERMES_KANBAN_TASK')
    os.environ.pop('HERMES_KANBAN_RUN_ID')
    parser = argparse.ArgumentParser()
    setup_cli(parser)
    cli(parser.parse_args(['cited-by', 'P-1']))
    cli(parser.parse_args(['retire', 'P-1', '--reason', 'Offline human review']))
    assert kb.get_task(conn, tid).status == 'done'
    assert len(Events().cited_by('P-1')) == 1
''')

    def test_real_stop_gates_partial_seam_and_successful_terminal_clearing(self):
        self.loaded(r'''
from agent.turn_stop_gates import apply_stop_gates
from agent.kanban_stop import session_called_kanban_terminal
from types import SimpleNamespace
from hermes_cli.lifecycle import invoke_hook
with kbc.connect_closing() as conn:
    tid = kb.create_task(conn, title='Offline stop test', assignee='worker')
    claimed = kb.claim_task(conn, tid)
    os.environ.update(HERMES_KANBAN_TASK=tid, HERMES_KANBAN_RUN_ID=str(claimed.current_run_id))
    ids = dict(session_id='stop-test', turn_id='turn-one')
    args = {'reason': 'staging prod migrations', 'kind': 'needs_input'}
    result = json.loads(handle_function_call('kanban_block', args, **ids))
    assert 'candidate rulings' in result['error'], result
    assert 'Continue in this turn; do not end the turn' in result['error']
    assert 'even if you have made no file edits' in result['error']
    transcript = [
        {'role': 'assistant', 'tool_calls': [{'id': 'call1', 'function': {'name': 'kanban_block', 'arguments': json.dumps(args)}}]},
        {'role': 'tool', 'name': 'kanban_block', 'tool_call_id': 'call1', 'content': json.dumps(result)},
    ]
    assert session_called_kanban_terminal(transcript)
    def stop(edited, attempts=0):
        agent = SimpleNamespace(session_id='stop-test', _turn_file_mutation_paths=edited,
            _pre_verify_nudges=attempts, _resolved_is_coding=False,
            _emit_interim_assistant_message=lambda _: None,
            _interim_content_was_streamed=lambda _: False)
        messages = list(transcript)
        verdict = apply_stop_gates(agent, {'role':'assistant', 'content':'I will follow the ruling.'},
            final_response='I will follow the ruling.', messages=messages,
            conversation_history=[], pending_verification_response=None,
            pending_verification_response_previewed=False)
        return verdict, messages
    verdict, _ = stop(set())
    assert not verdict.continue_turn  # Actual T:298 gap, no fake edits in production.
    assert kb.get_task(conn, tid).status == 'running'
    verdict, messages = stop({'real-edited-file.py'})
    assert verdict.continue_turn and 'card is still running' in messages[-1]['content']
    assert not stop({'real-edited-file.py'}, 3)[0].continue_turn  # core cap
    # A failed later block does not clear the pending veto.
    failed = json.loads(handle_function_call('kanban_block', {'reason':'x','kind':'invalid'}, **ids))
    assert 'error' in failed
    assert stop({'real-edited-file.py'})[0].continue_turn
    done = json.loads(handle_function_call('kanban_complete', {'summary':'per precedent P-1: used staging'}, **ids))
    assert done.get('ok'), done
    assert kb.get_task(conn, tid).status == 'done'
    assert not stop({'real-edited-file.py'})[0].continue_turn
    # A later successful justified block also clears continuation.
    os.environ.pop('HERMES_KANBAN_TASK')
    os.environ.pop('HERMES_KANBAN_RUN_ID')
    tid2 = kb.create_task(conn, title='Justified stop', assignee='worker')
    claimed2 = kb.claim_task(conn, tid2)
    os.environ.update(HERMES_KANBAN_TASK=tid2, HERMES_KANBAN_RUN_ID=str(claimed2.current_run_id))
    assert 'error' in json.loads(handle_function_call('kanban_block', args, **ids))
    justified = {'reason': 'no precedent applies: P-1 determines the DB target, this asks who approves rollback.', 'kind':'needs_input'}
    blocked = json.loads(handle_function_call('kanban_block', justified, **ids))
    assert blocked.get('ok'), blocked
    assert kb.get_task(conn, tid2).status == 'blocked'
    assert plugins.get_pre_verify_continue_message(session_id='stop-test') is None
    assert kb.latest_run(conn, tid2).summary.endswith('syntactic explanation marker present')
    # New turn and session end cannot inherit stale continuation state.
    os.environ['HERMES_KANBAN_TASK'] = 't_pending'
    assert 'error' in json.loads(handle_function_call('kanban_block', args, **ids))
    assert plugins.get_pre_verify_continue_message(session_id='stop-test')
    assert plugins.get_pre_verify_continue_message(session_id='unrelated') is None
    plugins._dispatch_pre_tool_call_hooks('kanban_show', {}, session_id='stop-test', turn_id='turn-two')
    assert plugins.get_pre_verify_continue_message(session_id='stop-test') is None
    plugins._dispatch_pre_tool_call_hooks('kanban_block', args, session_id='stop-test', turn_id='turn-two')
    invoke_hook('on_session_end', session_id='stop-test', turn_id='turn-two')
    assert plugins.get_pre_verify_continue_message(session_id='stop-test') is None
print('Real stop gates: edited turn continues; no edits and nudge cap still stop; successful complete/block clears pending state.')
''')

    def test_real_core_respawn_after_veto_and_max_retries_one(self):
        from hermes_cli import kanban_db as kb, kanban_db_connect as kbc, kanban_db_dispatch as kbd
        ctx = self.ctx()
        with kbc.connect_closing() as conn, patch.object(kbd, '_worker_alive', return_value=False), \
                patch.object(kbd, '_classify_worker_exit', return_value=('clean_exit', 0)), \
                patch.dict(os.environ, {'HERMES_KANBAN_CRASH_GRACE_SECONDS': '0'}):
            tid = kb.create_task(conn, title='Two vetoes then warned escalation', assignee='worker')
            for n in range(3):
                claimed = kb.claim_task(conn, tid, claimer=kb._claimer_id())
                self.assertIsNotNone(claimed)
                with patch.dict(os.environ, {'HERMES_KANBAN_TASK': tid, 'HERMES_KANBAN_RUN_ID': str(claimed.current_run_id)}):
                    args = {'reason': QUESTION, 'kind': 'needs_input'}
                    directive = pre_tool_call('kanban_block', args, ctx=ctx)
                    if n == 2:
                        self.assertEqual(directive['action'], 'modify')
                        result = json.loads(ctx.dispatch_tool('kanban_block', directive['args']))
                        self.assertTrue(result['ok'], result)
                        self.assertEqual(kb.get_task(conn, tid).status, 'blocked')
                        self.assertIn('[precedent-log] escalated without citing candidates P-1', kb.latest_run(conn, tid).summary)
                if n < 2:
                    self.assertEqual(directive['action'], 'block')
                    conn.execute('UPDATE tasks SET worker_pid=?, worker_started_at=NULL, started_at=1 WHERE id=?', (800001+n, tid))
                    conn.commit()
                    kbd.detect_crashed_workers(conn)
                    self.assertEqual(kb.get_task(conn, tid).status, 'ready')
                    self.assertEqual(kbd._protocol_violation_streak(conn, tid), n+1)
            limited = kb.create_task(conn, title='One retry budget', assignee='worker', max_retries=1)
            kb.claim_task(conn, limited, claimer=kb._claimer_id())
            with patch.dict(os.environ, {'HERMES_KANBAN_TASK': limited}):
                self.assertEqual(pre_tool_call('kanban_block', {'reason':QUESTION})['action'], 'block')
            conn.execute('UPDATE tasks SET worker_pid=?, worker_started_at=NULL, started_at=1 WHERE id=?', (800009, limited))
            conn.commit()
            kbd.detect_crashed_workers(conn)
            kb.recompute_ready(conn)
            self.assertEqual(kb.get_task(conn, limited).status, 'blocked')
            print('Core recovery: veto -> ready -> veto -> ready -> warned needs_input; max_retries=1 parks after first veto.', flush=True)

    def test_real_dependency_conversion_and_public_observer(self):
        self.loaded(r'''
with kbc.connect_closing() as conn:
    tid = kb.create_task(conn, title='No parent dependency', assignee='worker')
    claimed = kb.claim_task(conn, tid)
    os.environ.update(HERMES_KANBAN_TASK=tid, HERMES_KANBAN_RUN_ID=str(claimed.current_run_id))
    ids = dict(session_id='dependency', turn_id='one')
    args = {'reason':'staging prod migrations', 'kind':'dependency'}
    first = json.loads(handle_function_call('kanban_block', args, **ids))
    assert 'candidate rulings' in first['error'], first
    assert kb.get_task(conn, tid).status == 'running'
    args['reason'] += '; no precedent applies: P-1 chooses targets, production approval still needs a human.'
    result = json.loads(handle_function_call('kanban_block', args, **ids))
    assert result.get('ok') and result['block_kind'] == 'needs_input', result
    assert kb.get_task(conn, tid).status == 'blocked'
    assert '[precedent-log] considered candidates P-1; syntactic explanation marker present' in kb.latest_run(conn, tid).summary
    # Observer runs through the loaded plugin and reads public event payloads.
    rows = [json.loads(line) for line in (Store().directory / 'default.events.jsonl').read_text().splitlines()]
    assert rows[-1]['event'] == 'blocked' and rows[-1]['kind'] == 'needs_input', rows[-1]
    os.environ.pop('HERMES_KANBAN_TASK')
    os.environ.pop('HERMES_KANBAN_RUN_ID')
    parent = kb.create_task(conn, title='Open parent', assignee='worker')
    child = kb.create_task(conn, title='Real dependency', assignee='worker')
    claimed = kb.claim_task(conn, child)
    kb.link_tasks(conn, parent, child, expected_child_run_id=claimed.current_run_id)
    os.environ.update(HERMES_KANBAN_TASK=child, HERMES_KANBAN_RUN_ID=str(claimed.current_run_id))
    result = json.loads(handle_function_call('kanban_block', {'reason':'staging prod migrations','kind':'dependency'}, **ids))
    assert result.get('ok') and result['block_kind'] == 'dependency', result
    assert kb.get_task(conn, child).status == 'todo'
print('Actual loaded dependency gate + committed events: no parent -> gated needs_input; open parent -> dependency wait.')
''')

    def test_explicit_scoped_and_worker_pinned_board_real_transition(self):
        from hermes_cli import kanban_db as kb, kanban_db_connect as kbc
        release = self.home / 'kanban/boards/release'
        release.mkdir(parents=True)
        (release / 'board.json').write_text('{"name":"release"}')
        Store('release').add(QUESTION, 'Use release DB, never staging', ['staging', 'prod', 'migrations'])
        ctx = self.ctx()
        with kbc.connect_closing(board='release') as conn:
            for scoped in (False, True):
                tid = kb.create_task(conn, title='Board intent', assignee='worker')
                scope = kb.scoped_current_board('release') if scoped else contextlib.nullcontext()
                with scope:
                    args = {'task_id':tid, 'reason':QUESTION, 'kind':'needs_input', **({} if scoped else {'board':'release'})}
                    directive = pre_tool_call('kanban_block', args, ctx=ctx)
                    self.assertIn('P-1: Use release DB, never staging', directive['message'])
                    self.assertEqual(call_board(args.get('board')), 'release')
                    args['reason'] += ' no precedent applies: P-1 chooses targets, this asks who owns rollback.'
                    directive = pre_tool_call('kanban_block', args, ctx=ctx)
                    result = json.loads(ctx.dispatch_tool('kanban_block', directive['args']))
                    self.assertTrue(result['ok'], result)
                    self.assertEqual(kb.get_task(conn, tid).status, 'blocked')
        with kbc.connect_closing() as conn:
            tid = kb.create_task(conn, title='Pinned worker', assignee='worker')
            claimed = kb.claim_task(conn, tid)
            env = {'HERMES_KANBAN_TASK':tid, 'HERMES_KANBAN_RUN_ID':str(claimed.current_run_id),
                   'HERMES_KANBAN_DB':str(self.home / 'kanban.db'), 'HERMES_KANBAN_BOARD':'default'}
            with patch.dict(os.environ, env), kb.scoped_current_board('release'):
                self.assertEqual(kb.kanban_db_path(board='release'), self.home / 'kanban.db')
                self.assertEqual(call_board('release'), 'default')
                args = {'board':'release', 'reason':QUESTION, 'kind':'needs_input'}
                directive = pre_tool_call('kanban_block', args, ctx=ctx)
                self.assertIn('P-1: Use staging', directive['message'])
                args['reason'] += ' no precedent applies: P-1 chooses targets, this asks who owns rollback.'
                directive = pre_tool_call('kanban_block', args, ctx=ctx)
                result = json.loads(ctx.dispatch_tool('kanban_block', directive['args']))
                self.assertTrue(result['ok'], result)
                self.assertEqual(kb.get_task(conn, tid).status, 'blocked')
        print('Real transitions agree with explicit, scoped and dispatcher-pinned boards.', flush=True)

    def test_candidate_explanation_and_quarantine_reach_human_in_core(self):
        from hermes_cli import kanban_db as kb, kanban_db_connect as kbc
        ctx = self.ctx()
        with kbc.connect_closing() as conn:
            tid = kb.create_task(conn, title='Distinct rollback question', assignee='worker')
            reason = 'staging and prod migrations are finished. Who signs rollback approval?'
            args = {'task_id':tid, 'reason':reason, 'kind':'needs_input'}
            self.assertEqual(pre_tool_call('kanban_block', args, ctx=ctx)['action'], 'block')
            self.assertEqual(kb.get_task(conn, tid).status, 'ready')
            args['reason'] += ' no precedent applies: P-1 decides database targets, this asks for the rollback approver.'
            directive = pre_tool_call('kanban_block', args, ctx=ctx)
            self.assertTrue(json.loads(ctx.dispatch_tool('kanban_block', directive['args']))['ok'])
            self.assertEqual(kb.get_task(conn, tid).status, 'blocked')
            self.assertIn('considered candidates P-1', kb.latest_run(conn, tid).summary)
            store = Store()
            store.add('unrelated question', 'Answer')
            store.retire('P-1', 'Revoked')
            store.path.write_text(store.path.read_text().replace('Answer', 'Damage'))
            tid = kb.create_task(conn, title='Damaged log', assignee='worker')
            directive = pre_tool_call('kanban_block', {'task_id':tid, 'reason':QUESTION}, ctx=ctx)
            self.assertTrue(json.loads(ctx.dispatch_tool('kanban_block', directive['args']))['ok'])
            self.assertEqual(kb.get_task(conn, tid).status, 'blocked')
            self.assertIn('log damaged at line 2, rulings not applied', kb.latest_run(conn, tid).summary)

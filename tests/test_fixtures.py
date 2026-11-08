"""Exercise fixture scripts against loaded core tools, with no sockets or model calls."""
import support

import contextlib
import io
import json
import sys
from unittest.mock import patch

from support import IsolatedTest, LAB_SOURCE, REPO
from demo.run import FIXTURES, load_fixture, parse_args
import test_core


class FixtureTests(IsolatedTest):
    def test_fixture_cli_default_explicit_and_invalid(self):
        argv = ['demo/run.py', '--hermes-source', str(LAB_SOURCE)]
        with patch.object(sys, 'argv', argv):
            self.assertEqual(parse_args().fixture, 'migration')
        for name in FIXTURES:
            with patch.object(sys, 'argv', argv + ['--fixture', name]):
                self.assertEqual(parse_args().fixture, name)
        with patch.object(sys, 'argv', argv + ['--fixture', 'missing']), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            parse_args()
        self.assertEqual(error.exception.code, 2)
        with self.assertRaisesRegex(ValueError, 'Unknown fixture'):
            load_fixture('missing')

    def test_original_migration_fixture_is_unchanged(self):
        # Golden digest of the original parsed fixture, independent of JSON whitespace.
        import hashlib
        digest = hashlib.sha256(json.dumps(load_fixture(), sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest, '86cb73ead0e3bf408497585b81b30aab03089edf39240a701e2a96ef27dfd9e4')

    def test_fixture_reaches_transcript_and_result_line(self):
        for name in FIXTURES:
            result = self.process('''
import contextlib, io, json, sys
from unittest.mock import Mock
from demo.run import Harness, parse_args
sys.argv = ['demo/run.py', '--hermes-source', SOURCE, '--out', HOME + '/runs',
            '--run-id', NAME, '--fixture', NAME, '--hermes-home', HOME + '/lab-' + NAME]
h = Harness(parse_args())
assert json.loads((h.out / 'transcript.json').read_text())['fixture'] == NAME
h.tasks['T2'] = {'id': 't_example', 'workspace': str(h.out), 'output': 'missing.md'}
h.command = Mock(return_value=Mock(stdout=json.dumps({
    'task': {'workspace_path': str(h.out), 'status': 'blocked'}, 'events': []})))
output = io.StringIO()
with contextlib.redirect_stdout(output):
    step = h.snapshot('T2', 'attempt-1')
assert step['fixture'] == NAME
assert 'fixture=' + NAME in output.getvalue()
'''.replace('SOURCE', repr(str(LAB_SOURCE))).replace('HOME', repr(str(self.home))).replace('NAME', repr(name)))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def run_script(self, name):
        test_core.CoreTests.loaded(self, r'''
from demo.run import Harness, load_fixture, citation_evidence
from tests.fakes.fake_llm_provider import Text, ToolCall
from hermes_cli.lifecycle import invoke_hook
from types import SimpleNamespace
from unittest.mock import patch
fixture = load_fixture(NAME)
# Each mode uses a distinct board and genuine loaded plugin configuration.
for mode in ('enforce', 'advisory', 'control'):
    board = 'fixture-' + mode
    root = Path(os.environ['HOME']) / board
    root.mkdir()
    board_dir = Path(os.environ['HOME']) / 'kanban/boards' / board
    board_dir.mkdir(parents=True)
    (board_dir / 'board.json').write_text(json.dumps({'name': board}))
    os.environ['HERMES_KANBAN_BOARD'] = board
    # Control keeps the loader but has no ruling, identical gate behavior to absence.
    h = Harness.__new__(Harness)
    h.fixture, h.tasks, h.answered = fixture, {}, False
    store = Store(board)
    with patch.object(plugins.PluginContext, 'get_config', side_effect=lambda key, default: (mode if mode != 'control' else 'enforce') if key == 'precedent_log.veto' else default), kbc.connect_closing(board=board) as conn:
        def create(task):
            tid = kb.create_task(conn, title=task['title'], assignee='worker')
            h.tasks[task['label']] = {**task, 'id': tid}
            return tid
        def play(label):
            task = h.tasks[label]
            tid = task['id']
            claimed = kb.claim_task(conn, tid)
            assert claimed, (label, kb.get_task(conn, tid).status)
            os.environ.update(HERMES_KANBAN_TASK=tid, HERMES_KANBAN_RUN_ID=str(claimed.current_run_id))
            workspace = root / label
            workspace.mkdir(exist_ok=True)
            os.environ['TERMINAL_CWD'] = str(workspace)
            messages = [{'role': 'user', 'content': f'Work Kanban task {tid}.'}]
            for n in range(12):
                request = {'body': {'messages': messages}}
                response = h.respond(request)
                if isinstance(response, Text):
                    break
                assert isinstance(response, ToolCall), response
                args = dict(response.args)
                if response.name == 'write_file':
                    args['path'] = str(workspace / args['path'])
                if response.name == 'kanban_complete':
                    args['artifacts'] = [str(workspace / p) for p in args['artifacts']]
                call_id = str(n)
                messages.append({'role': 'assistant', 'tool_calls': [{'id': call_id,
                    'function': {'name': response.name, 'arguments': json.dumps(args)}}]})
                result = handle_function_call(response.name, args, session_id=tid, turn_id=str(claimed.current_run_id))
                messages.append({'role': 'tool', 'name': response.name, 'tool_call_id': call_id, 'content': result})
                decoded = json.loads(result)
                assert 'error' not in decoded or (response.name == 'kanban_block' and 'candidate rulings' in decoded['error']), (response.name, decoded)
                if response.name in {'kanban_block', 'kanban_complete'} and decoded.get('ok'):
                    break
            else:
                raise AssertionError('Fake script exceeded its call budget')
            state = kb.get_task(conn, tid).status
            output = workspace / task['output']
            evidence = citation_evidence([{'task_id': tid, 'worker': {'result': {'messages': messages}}}],
                                         output.read_text() if output.exists() else None)
            invoke_hook('on_session_end', session_id=tid)
            os.environ.pop('HERMES_KANBAN_TASK')
            os.environ.pop('HERMES_KANBAN_RUN_ID')
            return state, output, evidence, messages
        t1 = create(fixture['tasks'][0])
        state, output, _, _ = play('T1')
        assert state == 'blocked' and not output.exists()
        if mode != 'control':
            store.add(fixture['question'], fixture['ruling'], fixture['keys'].split(','))
        assert kb.unblock_task(conn, t1)
        kb.add_comment(conn, t1, author='human', body=fixture['ruling'])
        h.answered = True
        state, output, _, _ = play('T1')
        assert state == 'done' and output.exists()
        if NAME == 'migration':
            assert 'Target: staging' in output.read_text()
        else:
            assert fixture['fake']['plan'] in output.read_text()
            assert 'staging' not in output.read_text()
        for task in fixture['tasks'][1:]:
            if task['label'] == 'T4' and mode != 'control':
                store.retire('P-1', 'Fixture retirement')
            create(task)
            state, output, evidence, messages = play(task['label'])
            should_finish = task['label'] == 'T2' and mode == 'enforce'
            assert state == ('done' if should_finish else 'blocked'), (NAME, mode, task['label'], state)
            assert output.exists() == should_finish
            assert evidence['citation_found'] == should_finish
            if should_finish:
                assert evidence['citation_path'] == 'veto'
            if task['label'] == 'T3' and mode == 'enforce':
                assert 'no precedent applies: P-1' in kb.latest_run(conn, h.tasks['T3']['id']).summary
            if task['label'] == 'T4':
                assert not any('P-1' in m.get('content', '') for m in messages if m['role'] == 'tool')
print(NAME + ': T1 ask/answer, T2 reuse or allowed block, T3 exception, T4 retired; three modes; no network')
'''.replace('NAME', repr(name)))

    def test_migration_script_loaded_core(self):
        self.run_script('migration')

    def test_dependency_upgrade_script_loaded_core(self):
        self.run_script('dependency-upgrade')

    def test_customer_copy_script_loaded_core(self):
        self.run_script('customer-copy')

    def test_log_retention_script_loaded_core(self):
        self.run_script('log-retention')

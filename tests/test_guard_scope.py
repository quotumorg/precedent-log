"""Real core markers, store state and plugin config for the scoped guard."""
import support

from contextlib import nullcontext
import os
from unittest.mock import patch

from agent.delegation_context import (
    delegated_child_context, delegated_child_subprocess_env, owned_kanban_task,
)
from support import IsolatedTest
from precedent_log.gate import pre_tool_call
from precedent_log.guard import check, require_human
from precedent_log.store import Store


OPAQUE = [
    ('execute_code', {'code': 'print(1)'}),
    ('process_manage', {'action': 'write', 'data': 'hello'}),
    ('process_manage', {'action': 'submit'}),
    ('process_manage', {'action': 'poll', 'data': 'hello'}),
]


class GuardScopeTests(IsolatedTest):
    def assert_opaque(self, blocked, mode='scoped'):
        for tool, args in OPAQUE:
            with self.subTest(tool=tool, args=args, mode=mode):
                result = check(tool, args, str(self.home), mode)
                if blocked:
                    self.assertEqual(result['action'], 'block')
                else:
                    self.assertIsNone(result)

    def test_chat_children_allow_opaque_but_refuse_store_paths_and_writers(self):
        Store().add('question', 'answer')
        contexts = [patch.dict(os.environ, {'HERMES_DELEGATED_CHILD_CONTEXT': '1'}),
                    delegated_child_context()]
        for context in contexts:
            with context:
                self.assert_opaque(False)
                self.assert_opaque(True, 'strict')
                with self.assertRaises(PermissionError):
                    require_human()
                targets = [
                    ('write_file', {'path': str(self.home / 'precedent-log/default.jsonl')}),
                    ('patch', {'patch': '*** Add File: precedent-log/default.jsonl\n+x'}),
                    ('other_tool', {'destination': 'precedent-log/default.jsonl'}),
                    ('terminal', {'command': 'cat precedent-log/default.jsonl'}),
                    ('terminal', {'command': 'pwd', 'workdir': str(self.home / 'precedent-log')}),
                    ('execute_code', {'code': 'print(1)', 'workdir': str(self.home / 'precedent-log')}),
                    ('process_manage', {'action': 'write', 'data': 'precedent-log/default.jsonl'}),
                ]
                for tool, args in targets:
                    self.assertEqual(check(tool, args, str(self.home))['action'], 'block')

    def test_worker_active_missing_empty_and_retired_stores(self):
        for state in ('missing', 'empty', 'active', 'retired'):
            store = Store()
            store.path.unlink(missing_ok=True)
            if state == 'empty':
                store.directory.mkdir(exist_ok=True)
                store.path.write_text('')
            elif state in ('active', 'retired'):
                store.add('question', 'answer')
                if state == 'retired':
                    store.retire('P-1', 'old')
            with self.subTest(state=state), patch.dict(os.environ, {'HERMES_KANBAN_TASK': 'task'}):
                self.assert_opaque(state == 'active')
                self.assert_opaque(True, 'strict')
                self.assertIsNone(check('process_manage', {'action': 'poll'}, str(self.home)))

    def test_in_process_kanban_child_retains_raw_task_but_does_not_own_it(self):
        Store().add('question', 'answer')
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 'parent'}), delegated_child_context():
            self.assertEqual(owned_kanban_task(), '')
            self.assertEqual(os.environ['HERMES_KANBAN_TASK'], 'parent')
            self.assert_opaque(True)

    def test_core_scrubbed_kanban_subprocess_has_no_task_lineage(self):
        Store().add('question', 'answer')
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 'parent', 'HERMES_KANBAN_RUN_ID': '1'}):
            cleaned = delegated_child_subprocess_env(dict(os.environ))
        self.assertNotIn('HERMES_KANBAN_TASK', cleaned)
        self.assertNotIn('HERMES_KANBAN_RUN_ID', cleaned)
        self.assertTrue(cleaned['HERMES_DELEGATED_CHILD_CONTEXT'])
        with patch.dict(os.environ, cleaned, clear=True):
            self.assertEqual(owned_kanban_task(), '')
            self.assert_opaque(False)
            self.assert_opaque(True, 'strict')
            with self.assertRaises(PermissionError):
                require_human()
        result = self.process("from precedent_log.guard import check\n"
                              "assert check('execute_code', {'code': 'print(1)'}) is None\n"
                              "assert check('process_manage', {'action': 'write', 'data': 'hello'}) is None\n"
                              "assert check('write_file', {'path': 'precedent-log/default.jsonl'}, "
                              "__import__('os').environ['HERMES_HOME'])['action'] == 'block'\n",
                              HERMES_DELEGATED_CHILD_CONTEXT=cleaned['HERMES_DELEGATED_CHILD_CONTEXT'])
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_scoped_resolves_the_pinned_board_and_explicit_board(self):
        Store('release').add('question', 'answer')
        board_dir = self.home / 'kanban/boards/release'
        board_dir.mkdir(parents=True)
        (board_dir / 'board.json').write_text('{"name":"release"}')
        from hermes_cli.kanban_db import scoped_current_board
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 'task'}):
            self.assert_opaque(False)
            with patch.dict(os.environ, {'HERMES_KANBAN_BOARD': ''}), scoped_current_board('release'):
                self.assert_opaque(True)
            self.assertEqual(check('execute_code', {'board': 'release'})['action'], 'block')
            with patch.dict(os.environ, {'HERMES_KANBAN_DB': str(self.home / 'kanban.db')}):
                self.assertIsNone(check('execute_code', {'board': 'release'}))

    def test_faults_fail_closed_and_strict_never_needs_active_lookup(self):
        store = Store()
        store.directory.mkdir()
        store.path.write_text('broken\n')
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 'task'}):
            for tool, args in OPAQUE:
                result = pre_tool_call(tool, args)
                self.assertEqual(result['action'], 'block')
                self.assertIn('store guard unavailable', result['message'])
            with patch('precedent_log.guard.call_board', side_effect=ValueError('unavailable')):
                self.assertIn('store guard unavailable', pre_tool_call('execute_code', {})['message'])
                self.assert_opaque(True, 'strict')
        with patch.dict(os.environ, {'HERMES_DELEGATED_CHILD_CONTEXT': '1'}):
            self.assert_opaque(False)

    def test_ctx_config_default_strict_invalid_and_unmarked(self):
        class Config:
            def __init__(self, values):
                self.values = values
                self.reads = []

            def get_config(self, key, default):
                self.reads.append((key, default))
                return self.values.get(key, default)

        for context in (nullcontext(), delegated_child_context(),
                        patch.dict(os.environ, {'HERMES_DELEGATED_CHILD_CONTEXT': '1'}),
                        patch.dict(os.environ, {'HERMES_KANBAN_TASK': 'task'})):
            with context:
                for tool, args in [*OPAQUE, ('read_file', {'path': 'notes.txt'})]:
                    default = Config({})
                    self.assertIsNone(pre_tool_call(tool, args, ctx=default))
                    self.assertEqual(default.reads, [('precedent_log.guard', 'scoped')])
                    strict = Config({'precedent_log.guard': 'strict'})
                    result = pre_tool_call(tool, args, ctx=strict)
                    marked = bool(os.environ.get('HERMES_KANBAN_TASK') or
                                  os.environ.get('HERMES_DELEGATED_CHILD_CONTEXT') or owned_child())
                    if marked and tool != 'read_file':
                        self.assertEqual(result['action'], 'block')
                    else:
                        self.assertIsNone(result)
                    for value in ('wrong', '', None, [], {}):
                        invalid = Config({'precedent_log.guard': value})
                        result = pre_tool_call(tool, args, ctx=invalid)
                        if marked and tool != 'read_file':
                            self.assertEqual(result, {'action': 'block', 'message':
                                '[precedent-log] precedent_log.guard must be scoped or strict'})
                        else:
                            self.assertIsNone(result)

    def test_invalid_mode_covers_only_marked_guarded_tools_and_destination_fields(self):
        targets = [('write_file', {'path': 'notes.txt'}),
                   ('patch', {'patch': '*** Add File: notes.txt\n+x'}),
                   ('terminal', {'command': 'pwd'}),
                   ('process_manage', {'action': 'poll'}), *OPAQUE]
        targets.extend(('other_tool', {key: value})
                       for key in ('output_path', 'save_path', 'destination', 'dest_path')
                       for value in ('notes.txt', None))
        for context, marked in ((nullcontext(), False), (delegated_child_context(), True),
                                (patch.dict(os.environ, {'HERMES_DELEGATED_CHILD_CONTEXT': '1'}), True),
                                (patch.dict(os.environ, {'HERMES_KANBAN_TASK': 'task'}), True)):
            with context:
                for tool, args in targets:
                    with self.subTest(marked=marked, tool=tool, args=args):
                        result = check(tool, args, str(self.home), mode='wrong')
                        if marked:
                            self.assertEqual(result, {'action': 'block', 'message':
                                '[precedent-log] precedent_log.guard must be scoped or strict'})
                        else:
                            self.assertIsNone(result)
                self.assertIsNone(check('other_tool', {}, str(self.home), mode='wrong'))


def owned_child():
    from agent.delegation_context import is_delegated_child_process_context
    return is_delegated_child_process_context()

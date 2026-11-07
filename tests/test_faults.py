"""Fault and upgrade cases for the r2 policy and repair contracts."""

import support

import json
import os
from unittest.mock import patch

from support import IsolatedTest
from precedent_log.gate import pre_tool_call
from precedent_log.policy import Policy
from precedent_log.stats import Events
from precedent_log.store import Store, call_board, canonical, digest


class FaultTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.store = Store()
        self.store.add('staging prod migrations', 'Use staging', ['staging', 'prod'])

    def gate(self, **args):
        return pre_tool_call('kanban_block', {'reason': 'staging prod migrations', **args}, task_id='t_fault')

    def test_r1_veto_budget_migrates_even_with_torn_events(self):
        events = Events()
        events.record('veto', 't_fault', ['P-1'])
        events.record('veto', 't_fault', ['P-1'])
        with events.path.open('a') as stream:
            stream.write('{"v":')
        self.assertFalse(Policy('default', 't_fault').path.exists())
        result = self.gate()
        self.assertIn('escalated without citing candidates P-1', result['args']['reason'])
        self.assertEqual(Events().summary()['gated_vetoes'], 2)
        self.assertTrue(Policy('default', 't_fault').path.exists())

    def test_torn_archive_failure_does_not_disable_gate(self):
        self.assertEqual(self.gate()['action'], 'block')
        with Events().path.open('a') as stream:
            stream.write('{"v":')
        (self.store.directory / 'default.events.torn').mkdir()
        result = self.gate()
        self.assertEqual(result['action'], 'block')
        self.assertIn('events unavailable', result['message'])
        self.assertIn('escalated without citing candidates P-1', self.gate()['args']['reason'])

    def test_middle_event_damage_keeps_valid_counts_and_future_events(self):
        self.assertEqual(self.gate()['action'], 'block')
        with Events().path.open('a') as stream:
            stream.write('malformed\n')
        self.assertEqual(self.gate()['action'], 'block')
        self.assertEqual(Events().summary()['invalid_event_lines'], 1)
        self.assertEqual(Events().summary()['gated_vetoes'], 2)
        self.assertIn('escalated without citing', self.gate()['args']['reason'])

    def test_invalid_event_ids_do_not_hide_later_r1_veto_counts(self):
        events = Events()
        events.path.parent.mkdir(exist_ok=True)
        events.path.write_text(json.dumps({'v':1, 'board':'default', 'event':'veto',
                                          'task_id':'t_fault', 'ids':[{}]}) + '\n')
        events.record('veto', 't_fault', ['P-1'])
        events.record('veto', 't_fault', ['P-1'])
        self.assertEqual(events.summary()['invalid_event_lines'], 1)
        self.assertIn('escalated without citing candidates P-1', self.gate()['args']['reason'])

    def test_dependency_lookup_and_guard_failures_are_visible(self):
        result = self.gate(kind='dependency')
        self.assertIn('dependency state unavailable; checked conservatively', result['message'])
        with patch('precedent_log.guard.check', side_effect=ValueError('bad path')):
            result = pre_tool_call('write_file', {'path': 'x'})
        self.assertEqual(result['action'], 'block')
        self.assertIn('store guard unavailable', result['message'])

    def test_unreadable_retirement_cannot_be_restored_by_repair(self):
        self.store.retire('P-1', 'Revoked')
        lines = self.store.path.read_bytes().splitlines(keepends=True)
        self.store.path.write_bytes(lines[0] + b'garbled retirement\n')
        self.store.repair(1)
        self.assertTrue(self.store.verify()['ok'])
        self.assertEqual(self.store.list(), [])
        self.assertTrue(self.store.list(True)[0]['retired'])
        self.assertEqual(self.store.add('new policy', 'New answer')['id'], 'P-2')

    def test_alias_schema_damage_quarantines_entire_board(self):
        row = json.loads(self.store.path.read_text())
        row['also'] = 'not a list'
        row['h'] = digest(row)
        self.store.path.write_text(canonical(row) + '\n')
        self.assertEqual(self.store.read().active, [])
        self.assertIn('log damaged at line 1', self.gate()['args']['reason'])

    def test_machine_pin_and_stale_env_named_board_match_core_path(self):
        from hermes_cli import kanban_db as kb
        release = self.home / 'kanban/boards/release'
        release.mkdir(parents=True)
        (release / 'board.json').write_text('{"name":"release"}')
        with patch.dict(os.environ, {'HERMES_KANBAN_DB':str(release / 'kanban.db'), 'HERMES_KANBAN_BOARD':'default'}):
            self.assertEqual(call_board(), 'release')
            with kb.pin_first_board_resolution():
                self.assertEqual(kb.kanban_db_path(board='default'), release / 'kanban.db')
                self.assertEqual(call_board('default'), 'release')

    def test_real_cli_repair_creates_backup_and_refuses_marked_process(self):
        self.store.retire('P-1', 'Revoked')
        original = self.store.path.read_bytes()
        code = ("import argparse; from precedent_log.commands import setup_cli, cli; "
                "p=argparse.ArgumentParser(); setup_cli(p); "
                "cli(p.parse_args(['repair','--truncate-after','1']))")
        refused = self.process(code, HERMES_KANBAN_TASK='t_worker')
        self.assertEqual(refused.returncode, 2)
        self.assertEqual(self.store.path.read_bytes(), original)
        repaired = self.process(code)
        self.assertEqual(repaired.returncode, 0, repaired.stderr)
        from pathlib import Path
        report = json.loads(repaired.stdout)
        self.assertEqual(Path(report['backup']).read_bytes(), original)
        self.assertTrue(self.store.verify()['ok'])
        self.assertEqual(self.store.list(), [])

    def test_matching_citation_is_valid_outside_top_three_display_cap(self):
        for n in range(4):
            self.store.add('staging prod migrations', 'Candidate ' + str(n), ['staging', 'prod'])
        result = self.gate(reason='staging prod migrations, per precedent P-1')
        self.assertIn('The cited ruling already answers this: P-1', result['message'])
        self.assertIn('P-1:', result['message'])

    def test_session_cwd_failure_cannot_authorize_worker_relative_writes(self):
        import importlib.util
        from types import SimpleNamespace
        from support import REPO
        spec = importlib.util.spec_from_file_location('offline_plugin_probe', REPO / '__init__.py',
                                                      submodule_search_locations=[str(REPO)])
        module = importlib.util.module_from_spec(spec)
        import sys
        sys.modules[spec.name] = module
        self.addCleanup(sys.modules.pop, spec.name, None)
        spec.loader.exec_module(module)
        hooks = {}
        def unavailable():
            raise OSError('session unavailable')
        ctx = SimpleNamespace(session_cwd=unavailable,
                              register_hook=lambda name, fn: hooks.update({name:fn}),
                              register_command=lambda *a, **kw: None,
                              register_cli_command=lambda *a, **kw: None,
                              register_system_prompt_section=lambda *a, **kw: None)
        module.register(ctx)
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK':'t_worker'}):
            directive = hooks['pre_tool_call']('write_file', {'path':'default.jsonl'})
            self.assertIn('session cwd lookup failed', directive['message'])
        self.assertIsNone(hooks['pre_tool_call']('write_file', {'path':'default.jsonl'}))

"""Offline reliance records and human retirement reports."""
import support

import argparse
import contextlib
import io
import json
import os
from unittest.mock import patch

from support import IsolatedTest
from precedent_log import commands
from precedent_log.stats import Events, on_completed
from precedent_log.store import Store


class CitedByTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.store = Store()
        self.store.add('staging or prod?', 'Use staging')

    def cli(self, *args):
        parser = argparse.ArgumentParser()
        commands.setup_cli(parser)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            commands.cli(parser.parse_args(args))
        return out.getvalue().strip()

    def complete(self, summary, task='t_a', **kwargs):
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': task}):
            on_completed(tool_name='kanban_complete', args={'summary': summary, **kwargs}, result={'ok': True})

    def test_success_records_active_word_bounded_ids_once(self):
        self.store.add('second question', 'Second ruling')
        self.store.add('old question', 'Old ruling')
        self.store.retire('P-3', 'old')
        self.complete('P-1 and p-2, P-1; P-3 and P-99, XP-1 and P-10')
        events, invalid = Events()._read()
        self.assertEqual(invalid, 0)
        self.assertEqual(len(events), 1)
        self.assertEqual((events[0]['event'], events[0]['task_id'], events[0]['ids']), ('relied', 't_a', ['P-1', 'P-2']))
        self.assertTrue(events[0]['created_at'].endswith('Z'))
        self.assertEqual(events[0]['board'], 'default')

    def test_marker_matches_demo_without_requiring_precedent_prefix(self):
        self.complete('Follow p-1.')
        self.assertEqual(len(Events().cited_by('P-1')), 1)
        self.complete('XP-1 P-10 P-01 P-1x')
        self.assertEqual(len(Events().cited_by('P-1')), 1)

    def test_rejected_malformed_nonworker_or_other_task_never_records(self):
        for result in ({'ok': False}, {'ok': True, 'error': 'failed'}, {'error': 'no'}, [], 'bad JSON'):
            with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 't_a'}):
                on_completed(tool_name='kanban_complete', args={'summary': 'P-1'}, result=result)
        on_completed(tool_name='kanban_complete', args={'summary': 'P-1'}, result={'ok': True})
        self.complete('P-1', task_id='t_other')
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 't_a'}):
            on_completed(tool_name='kanban_block', args={'summary': 'P-1'}, result={'ok': True})
            on_completed(tool_name='kanban_complete', args={'result': 'P-1'}, result={'ok': True})
        self.assertEqual(Events().cited_by('P-1'), [])

    def test_string_result_and_omitted_task_id(self):
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 't_a'}):
            on_completed(tool_name='kanban_complete', args={'summary': 'P-1'}, result='{"ok": true}')
        self.assertEqual(Events().cited_by('P-1')[0]['task_id'], 't_a')

    def test_cited_by_empty_one_multiple_and_block_citations(self):
        self.assertEqual(self.cli('cited-by', 'P-1'), 'No citations.')
        self.assertEqual(json.loads(self.cli('cited-by', 'P-1', '--json')), [])
        self.complete('P-1')
        self.assertEqual(len(json.loads(self.cli('cited-by', 'P-1', '--json'))), 1)
        Events().record('citation', 't_block', ['P-1'])
        Events().record('veto', 't_ignored', ['P-1'])
        self.complete('P-1', 't_b')
        rows = Events().cited_by('P-1')
        self.assertEqual([r['task_id'] for r in rows], ['t_a', 't_block', 't_b'])
        self.assertEqual([r['event'] for r in rows], ['relied', 'citation', 'relied'])
        self.assertIn('t_block | citation | ', self.cli('cited-by', 'P-1'))

    def test_other_board_isolation_and_worker_board_resolution(self):
        Store('other').add('other question', 'Other answer')
        self.complete('P-1')
        with patch.dict(os.environ, {'HERMES_KANBAN_TASK': 't_other', 'HERMES_KANBAN_BOARD': 'other'}):
            on_completed(tool_name='kanban_complete', args={'summary': 'P-1', 'board': 'other'}, result={'ok': True})
        self.assertEqual([r['task_id'] for r in Events().cited_by('P-1')], ['t_a'])
        self.assertEqual([r['task_id'] for r in Events('other').cited_by('P-1')], ['t_other'])
        self.assertNotIn('t_a', self.cli('cited-by', 'P-1', '--board', 'other'))

    def test_retired_ruling_keeps_history_and_rejects_new_reliance(self):
        self.complete('P-1')
        self.store.retire('P-1', 'New policy')
        self.complete('P-1', 't_b')
        self.assertEqual([r['task_id'] for r in Events().cited_by('P-1')], ['t_a'])
        shown = json.loads(self.cli('show', 'P-1'))
        self.assertTrue(shown['retired'])
        self.assertEqual(shown['retirement']['reason'], 'New policy')

    def test_retire_report_counts_distinct_completed_jobs_only(self):
        self.complete('P-1')
        self.complete('P-1')
        self.complete('P-1', 't_b')
        Events().record('citation', 't_block', ['P-1'])
        self.assertEqual(self.cli('retire', 'P-1', '--reason', 'New policy'),
                         'P-1 retired. 2 completed jobs cited it: t_a, t_b. Review them: hermes precedent cited-by P-1 --board default')

    def test_replacement_stored_and_shown_cli_and_slash(self):
        self.complete('P-1')
        self.store.add('replacement', 'New policy')
        report = self.cli('retire', 'P-1', '--reason', 'New policy', '--replaced-by', 'P-2')
        self.assertIn('P-1 retired. 1 completed job cited it: t_a.', report)
        self.assertIn('Replaced by P-2.', report)
        self.assertEqual(json.loads(self.cli('show', 'P-1'))['retirement']['replaced_by'], 'P-2')
        self.store.add('third', 'Third policy')
        report = commands.ruling('retire P-2 New policy --replaced-by P-3')
        self.assertIn('P-2 retired. 0 completed jobs cited it:', report)
        self.assertIn('Replaced by P-3.', report)
        self.assertEqual(self.store.list(True)[1]['retirement']['surface'], 'slash')

    def test_replacement_must_exist_be_active_same_board_and_not_itself(self):
        Store('other').add('first', 'First')
        Store('other').add('second', 'Second')
        before = self.store.path.read_bytes()
        for rid in ('P-1', 'P-2', 'P-99', 'invalid'):
            with self.subTest(rid=rid), self.assertRaises(ValueError):
                self.store.retire('P-1', 'New policy', replaced_by=rid)
            self.assertEqual(self.store.path.read_bytes(), before)
        self.store.add('old replacement', 'Old')
        self.store.retire('P-2', 'old')
        with self.assertRaises(ValueError):
            self.store.retire('P-1', 'New policy', replaced_by='P-2')
        self.assertIn('must exist and be active', commands.ruling('retire P-1 old --replaced-by P-2'))

    def test_damaged_rulings_quarantine_and_events_still_skip_bad_lines(self):
        self.complete('P-1')
        events = Events()
        with events.path.open('ab') as stream:
            stream.write(b'bad event\n')
        self.assertEqual(len(events.cited_by('P-1')), 1)
        self.assertEqual(events.summary()['invalid_event_lines'], 1)
        with self.store.path.open('ab') as stream:
            stream.write(b'bad ruling\n')
        self.complete('P-1', 't_b')
        self.assertEqual(len(events._read()[0]), 1)
        with self.assertRaisesRegex(ValueError, 'damaged'):
            events.cited_by('P-1')
        with self.assertRaises(ValueError):
            self.store.retire('P-1', 'old')

    def test_observer_fault_cannot_change_success(self):
        with patch('precedent_log.stats.Events.record', side_effect=OSError('unavailable')):
            self.assertIsNone(self.complete('P-1'))
        self.assertEqual(Events().cited_by('P-1'), [])

    def test_unknown_ruling_cited_by_errors(self):
        with self.assertRaisesRegex(ValueError, 'Unknown ruling'):
            Events().cited_by('P-99')

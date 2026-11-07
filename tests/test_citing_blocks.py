"""A matching answer in a block reason must not authorize the same question."""
import support

import json
from types import SimpleNamespace

from support import IsolatedTest
from precedent_log.gate import pre_tool_call, quotes_ruling
from precedent_log.stats import Events
from precedent_log.store import Store


QUESTION = 'staging or prod DB for the schema migration?'
RULING = 'Use staging for the local migration plan. Production operations require fresh approval.'


class CitingBlockTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.store = Store()
        self.store.add(QUESTION, RULING, ['staging', 'prod'])

    def call(self, reason, task='t_repeat', mode='enforce'):
        ctx = SimpleNamespace(get_config=lambda *_: mode)
        return pre_tool_call('kanban_block', {'reason': reason}, task_id=task, ctx=ctx)

    def test_cited_repeat_is_vetoed_and_recorded_without_reliance(self):
        reason = QUESTION + ' Precedent P-1 says "' + RULING + '" Need confirmation that staging is the correct target before writing.'
        result = self.call(reason)
        self.assertEqual(result['action'], 'block')
        for text in ('The cited ruling already answers this: P-1', 'Proceed per P-1',
                     'cite it in the completion', "'no precedent applies:' naming P-1 and what it does not cover"):
            self.assertIn(text, result['message'])
        rows, _ = Events()._read()
        self.assertEqual([r['event'] for r in rows], ['veto', 'citation'])
        self.assertTrue(rows[-1]['veto'])
        self.assertEqual(rows[-1]['ids'], ['P-1'])
        self.assertEqual([r['event'] for r in Events().cited_by('P-1')], ['citation'])
        counts = Events().summary()
        self.assertEqual((counts['gated_vetoes'], counts['passes_with_citation']), (1, 0))

    def test_normalized_ruling_sentence_without_id_is_a_citation(self):
        for n, quote in enumerate((RULING, 'USE  STAGING\nfor the LOCAL migration plan!',
                                   'Production operations require fresh approval.')):
            result = self.call(QUESTION + ' "' + quote + '" Please confirm.', task=f't_quote{n}')
            self.assertIn('The cited ruling already answers this: P-1', result['message'])
        self.assertEqual(len(Events().cited_by('P-1')), 3)

    def test_quote_requires_order_whole_words_and_active_ruling(self):
        for text in ('Use staging for the local migration',
                     'plan migration local the for staging Use',
                     'Use staging for the local migration planet'):
            self.assertFalse(quotes_ruling(text, RULING))
        self.assertFalse(quotes_ruling('anything', '...'))
        self.store.retire('P-1', 'Policy finished')
        result = self.call(QUESTION + ' "' + RULING + '"')
        self.assertIn('none matched', result['args']['reason'])
        self.assertEqual(Events().cited_by('P-1'), [])

    def test_citation_and_quote_share_two_veto_budget_across_processes(self):
        reason = QUESTION + ' per precedent P-1'
        self.assertEqual(self.call(reason)['action'], 'block')
        self.assertEqual(self.call(QUESTION + ' "' + RULING + '"')['action'], 'block')
        result = self.process('from precedent_log.gate import pre_tool_call; import json; '
                              'print(json.dumps(pre_tool_call("kanban_block", {"reason": ' + repr(reason) +
                              '}, task_id="t_repeat")))')
        self.assertEqual(result.returncode, 0, result.stderr)
        directive = json.loads(result.stdout)
        self.assertEqual(directive['action'], 'modify')
        self.assertIn('escalated despite citing an already answering ruling P-1', directive['args']['reason'])
        rows, _ = Events()._read()
        self.assertEqual([r['veto'] for r in rows if r['event'] == 'citation'], [True, True, False])
        self.assertEqual(Events().summary()['gated_vetoes'], 2)

    def test_explanation_with_quote_still_passes_and_names_cited_candidate(self):
        reason = QUESTION + ' "' + RULING + '"; no precedent applies: '
        rejected = self.call(reason + 'P-1 ...')
        self.assertIn('The cited ruling already answers this: P-1', rejected['message'])
        self.assertEqual([r['event'] for r in Events().cited_by('P-1')], ['citation'])
        valid = 'P-1 covers targets, this asks who owns rollback.'
        self.assertIn('syntactic explanation marker', self.call(reason + valid)['args']['reason'])
        for _ in range(4):
            self.store.add(QUESTION, 'Use another target', ['staging', 'prod'])
        # P-1 is outside the three-row display cap but is quoted in the reason.
        result = self.call(reason + 'P-3 P-4 P-5 cover targets, this asks who owns rollback.', task='t_cap')
        self.assertEqual(result['action'], 'block')
        self.assertIn('P-1', result['message'])

    def test_nonmatching_citations_keep_existing_rejection(self):
        self.store.add('vendor contract approval', 'Ask purchasing', ['vendor', 'contract'])
        for n, citation in enumerate(('per precedent P-2', '"Ask purchasing"')):
            result = self.call(QUESTION + ' ' + citation, task=f't_unmatched{n}')
            self.assertIn('Cited ruling did not match this reason: P-2', result['message'])
        self.assertEqual(Events().cited_by('P-2'), [])

    def test_advisory_cited_and_quoted_reasks_proceed_without_policy(self):
        for reason in (QUESTION + ' per precedent P-1', QUESTION + ' "' + RULING + '"'):
            result = self.call(reason, mode='advisory')
            self.assertEqual(result['action'], 'modify')
            self.assertTrue(result['args']['reason'].startswith(reason))
            self.assertIn('advisory candidate rulings; block proceeds without a veto', result['args']['reason'])
            self.assertIn('id="P-1"', result['args']['reason'])
        self.assertFalse((self.store.directory / 'default.policy.json').exists())
        self.assertFalse(Events().path.exists())

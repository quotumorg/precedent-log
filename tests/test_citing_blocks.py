"""A matching answer in a block reason must not authorize the same question."""
import support

import json
from types import SimpleNamespace

from support import IsolatedTest
from precedent_log.gate import pre_tool_call, quotes_ruling
from precedent_log.match import match
from precedent_log.stats import Events
from precedent_log.store import Store


QUESTION = 'staging or prod DB for the schema migration?'
RULING = 'Use staging for the local migration plan. Production operations require fresh approval.'


class CitingBlockTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.store = Store()
        self.store.add(QUESTION, RULING, ['schema', 'migration'])

    def call(self, reason, task='t_repeat', mode='enforce'):
        ctx = SimpleNamespace(get_config=lambda key, default: mode if key == "precedent_log.veto" else default)
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

    def test_nonmatching_citations_are_candidates_and_recorded(self):
        self.store.add('vendor contract approval', 'Ask purchasing', ['vendor', 'contract'])
        for n, citation in enumerate(('per precedent P-2', '"Ask purchasing"')):
            result = self.call(QUESTION + ' ' + citation, task=f't_unmatched{n}')
            self.assertIn('The cited ruling already answers this: P-2', result['message'])
            self.assertIn("'no precedent applies:' naming P-1, P-2", result['message'])
        self.assertEqual([r['event'] for r in Events().cited_by('P-2')], ['citation', 'citation'])

    def test_exact_target_unresolved_reason_vetoes_on_key_miss(self):
        reason = ('Target environment unresolved: should this orders.delivery_note migration target staging or production? '
                  'Precedent P-1 ("' + RULING + '") suggests staging. Please confirm or override.')
        self.assertEqual(match(reason, self.store.list()), [])
        result = self.call(reason)
        self.assertEqual(result['action'], 'block')
        self.assertIn('P-1: ' + RULING, result['message'])
        # Explicit override language retains the existing uncited analytics path.
        self.assertEqual(Events().cited_by('P-1'), [])
        self.assertEqual(Events().summary()['gated_vetoes'], 1)

    def test_id_only_and_normalized_quote_veto_on_key_miss(self):
        for n, reason in enumerate(('Target unresolved. Precedent P-1. Please confirm.',
                                   '"USE staging for the LOCAL migration plan!" Please confirm.')):
            self.assertEqual(match(reason, self.store.list()), [])
            result = self.call(reason, task=f't_miss{n}')
            self.assertIn('The cited ruling already answers this: P-1', result['message'])
        rows, _ = Events()._read()
        self.assertEqual([r['veto'] for r in rows if r['event'] == 'citation'], [True, True])
        self.assertEqual(Events().summary()['passes_with_citation'], 0)

    def test_key_miss_explanation_must_name_cited_candidate(self):
        reason = 'Precedent P-1. no precedent applies: '
        for n, explanation in enumerate(('P-1 ...', 'P-2 covers targets, this asks who owns rollback.')):
            self.assertEqual(self.call(reason + explanation, task=f't_invalid{n}')['action'], 'block')
        reason += 'P-1 covers targets, this asks who owns rollback.'
        self.assertEqual(match(reason, self.store.list()), [])
        result = self.call(reason, task='t_valid')
        self.assertIn('considered candidates P-1; syntactic explanation marker', result['args']['reason'])
        self.assertEqual(Events().summary()['passes_with_justification'], 1)

    def test_retired_and_unknown_key_miss_citations_keep_uncited_path(self):
        self.store.retire('P-1', 'Policy finished')
        for n, rid in enumerate(('P-1', 'P-999')):
            for _ in range(2):
                result = self.call('Precedent ' + rid, task=f't_retired{n}')
                self.assertIn(rid + ' is not an active ruling on this board', result['message'])
            result = self.call('Precedent ' + rid, task=f't_retired{n}')
            self.assertIn('escalated without citing candidates (none)', result['args']['reason'])
            if rid == 'P-1':
                self.assertEqual(Events().cited_by(rid), [])
            else:
                with self.assertRaisesRegex(ValueError, 'Unknown ruling'):
                    Events().cited_by(rid)
        rows, _ = Events()._read()
        self.assertTrue(all(row['ids'] == [] for row in rows))

    def test_key_miss_citation_and_quote_share_cap_across_processes(self):
        self.assertEqual(self.call('Precedent P-1')['action'], 'block')
        self.assertEqual(self.call('"' + RULING + '"')['action'], 'block')
        result = self.process('from precedent_log.gate import pre_tool_call; import json; '
                              'print(json.dumps(pre_tool_call("kanban_block", {"reason": "Precedent P-1"}, '
                              'task_id="t_repeat")))')
        self.assertEqual(result.returncode, 0, result.stderr)
        directive = json.loads(result.stdout)
        self.assertIn('escalated despite citing an already answering ruling P-1', directive['args']['reason'])
        rows, _ = Events()._read()
        self.assertEqual([r['veto'] for r in rows if r['event'] == 'citation'], [True, True, False])

    def test_advisory_appends_key_miss_citations_and_quotes_once(self):
        for reason in ('Precedent P-1', '"' + RULING + '"', 'Precedent P-1 "' + RULING + '"'):
            self.assertEqual(match(reason, self.store.list()), [])
            result = self.call(reason, mode='advisory')
            self.assertEqual(result['action'], 'modify')
            self.assertEqual(result['args']['reason'].count('id="P-1"'), 1)
            self.assertNotIn('none matched', result['args']['reason'])
        self.assertFalse((self.store.directory / 'default.policy.json').exists())
        self.assertFalse(Events().path.exists())

    def test_advisory_cited_and_quoted_reasks_proceed_without_policy(self):
        for reason in (QUESTION + ' per precedent P-1', QUESTION + ' "' + RULING + '"'):
            result = self.call(reason, mode='advisory')
            self.assertEqual(result['action'], 'modify')
            self.assertTrue(result['args']['reason'].startswith(reason))
            self.assertIn('advisory candidate rulings; block proceeds without a veto', result['args']['reason'])
            self.assertIn('id="P-1"', result['args']['reason'])
        self.assertFalse((self.store.directory / 'default.policy.json').exists())
        self.assertFalse(Events().path.exists())

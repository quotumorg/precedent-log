import support

import json
import hashlib
import os
import statistics
import time
from unittest.mock import patch

from support import IsolatedTest
from precedent_log.gate import pre_tool_call
from precedent_log.section import render
from precedent_log.stats import Events, on_blocked
from precedent_log.store import Store


class GateTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.store = Store()
        self.store.add("staging prod migrations", "Use staging", ["staging", "prod"])
        self.args = {"reason": "staging or prod for migrations?", "kind": "needs_input"}

    def call(self, args=None, task="t_worker"):
        return pre_tool_call("kanban_block", self.args if args is None else args, task_id=task)

    def test_matching_two_vetoes_then_uncited_pass(self):
        for _ in range(2):
            result = self.call()
            self.assertEqual(result["action"], "block")
            self.assertIn("P-1: Use staging (asked: staging prod migrations)", result["message"])
            self.assertIn("kanban_complete", result["message"])
            self.assertIn("kanban_block", result["message"])
        result = self.call()
        self.assertEqual(result["action"], "modify")
        self.assertIn("escalated without citing candidates P-1", result["args"]["reason"])
        self.assertEqual(self.args["reason"], "staging or prod for migrations?")
        counts = Events().summary()
        self.assertEqual((counts["gated_vetoes"], counts["uncited_passes"], counts["ruling_hits"]), (2, 1, {"P-1": 3}))

    def test_citation_active_retired_and_unknown(self):
        result = self.call({**self.args, "reason": self.args["reason"] + " per PRECEDENT p-1"})
        self.assertIn("The cited ruling already answers this: P-1", result["message"])
        self.store.retire("P-1", "No longer needed")
        result = self.call({**self.args, "reason": "Considered precedent P-1 but it is retired"})
        self.assertIn("P-1 is not an active ruling on this board", result["message"])
        result = self.call({**self.args, "reason": "precedent P-999"}, task="unknown")
        self.assertIn("P-999 is not an active ruling on this board", result["message"])
        self.assertEqual(Events().summary()["passes_with_citation"], 0)

    def test_justification_minimum_is_single_line(self):
        self.assertEqual(self.call()["action"], "block")
        result = self.call({**self.args, "reason": "no precedent applies: P-1 covers target selection, this asks who owns rollback."})
        self.assertIn("syntactic explanation marker", result["args"]["reason"])
        self.assertEqual(self.call({**self.args, "reason": "staging prod; no precedent applies: short"})["action"], "block")
        result = self.call({**self.args, "reason": "staging prod; no precedent applies: \nP-1 target selection differs"}, task="fresh")
        self.assertEqual(result["action"], "block")
        self.assertEqual(Events().summary()["passes_with_justification"], 1)

    def test_override_phrases_are_uncited_case_insensitively(self):
        phrases = ("ignore this ruling", "IGNORE P-1", "Ask Again", "disregard", "OVERRIDE")
        for n, phrase in enumerate(phrases):
            with self.subTest(phrase=phrase):
                args = {**self.args, "reason": f"staging prod; per precedent P-1: {phrase}"}
                self.assertEqual(self.call(args, task=f"override{n}")["action"], "block")
        self.assertEqual(Events().summary()["passes_with_citation"], 0)

    def test_decorated_or_malformed_citations_are_uncited(self):
        for n, marker in enumerate(("P-1.foo", "P-1..", "P.1", "P-01", "P-1-extra",
                                    "P-1x", "XP-1", "P-1_", "P-1/P-2", "*P-1*",
                                    "P-1 and precedent P-1.foo")):
            with self.subTest(marker=marker):
                args = {**self.args, "reason": "staging prod; per precedent " + marker}
                self.assertEqual(self.call(args, task=f"malformed{n}")["action"], "block")
        self.assertEqual(Events().summary()["passes_with_citation"], 0)

    def test_standalone_citations_with_sentence_punctuation_veto(self):
        for n, marker in enumerate(("P-1", "p-1.", "P-1: use staging", "P-1, use staging")):
            with self.subTest(marker=marker):
                result = self.call({**self.args, "reason": "staging prod; per precedent " + marker}, task=f"valid{n}")
                self.assertIn("The cited ruling already answers this: P-1", result["message"])

    def test_explanations_require_four_distinct_words_and_every_candidate(self):
        self.store.add("staging prod target", "Use another plan", ["staging", "prod"])
        cases = ("P-1 P-2 " + "." * 25, "P-1 P-2 different DIFFERENT different different",
                 "P-1 P-2 target selection differs...", "P-1 target selection differs from permissions")
        for n, explanation in enumerate(cases):
            with self.subTest(explanation=explanation):
                args = {**self.args, "reason": "staging prod; no precedent applies: " + explanation}
                self.assertEqual(self.call(args, task=f"filler{n}")["action"], "block")
        result = self.call({**self.args, "reason": "staging prod; no precedent applies: P-1 P-2 target selection differs here"})
        self.assertIn("syntactic explanation marker", result["args"]["reason"])

    def test_citation_cannot_bypass_an_incomplete_explanation(self):
        reason = "staging prod; per precedent P-1; no precedent applies: P-1 ..."
        self.assertEqual(self.call({**self.args, "reason": reason})["action"], "block")
        reason = "staging prod; per precedent P-1; no precedent applies: P-1 covers targets, this asks about permission"
        self.assertIn("syntactic explanation marker", self.call({**self.args, "reason": reason})["args"]["reason"])

    def test_override_reasons_keep_the_bounded_veto_policy(self):
        args = {**self.args, "reason": "staging prod; per precedent P-1: ask again"}
        self.assertEqual([self.call(args)["action"] for _ in range(3)], ["block", "block", "modify"])
        counts = Events().summary()
        self.assertEqual((counts["gated_vetoes"], counts["uncited_passes"], counts["passes_with_citation"]), (2, 1, 0))

    def test_unmatched_and_kind_filter(self):
        result = self.call({"reason": "unrelated vendor contract", "kind": "needs_input"})
        self.assertIn("checked 1 active rulings on board default: none matched", result["args"]["reason"])
        for kind in ("capability", "transient", "other", ""):
            self.assertIsNone(self.call({**self.args, "kind": kind}))
        self.assertEqual(self.call({"reason": self.args["reason"]})["action"], "block")
        self.assertIsNone(pre_tool_call("kanban_complete", self.args))

    def test_respawn_durable_count_and_env_identity(self):
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_durable"}):
            self.assertEqual(self.call(task="session-1")["action"], "block")
            self.assertEqual(self.call(task="session-2")["action"], "block")
        code = ("import json; from precedent_log.gate import pre_tool_call; "
                "print(json.dumps(pre_tool_call('kanban_block', " + repr(self.args) + ", task_id='session-3')))")
        result = self.process(code, HERMES_KANBAN_TASK="t_durable")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["action"], "modify")
        self.assertEqual(self.call(task="different-task")["action"], "block")

    def test_corrupt_log_gate_still_answers(self):
        with self.store.path.open("a") as stream:
            stream.write('garbage\n{"v":')
        self.assertEqual(self.call()["action"], "modify")
        unrelated = self.call({"reason": "vendor contract"})
        self.assertIn("log damaged at line 2", unrelated["args"]["reason"])

    def test_missing_and_unreadable_files_never_raise(self):
        self.store.path.unlink()
        self.assertIn("checked 0 active rulings", self.call()["args"]["reason"])
        self.store.path.mkdir()
        self.assertIn("unreadable", self.call()["args"]["reason"])
        with patch.dict(os.environ, {"HERMES_KANBAN_TASK": "t_worker"}):
            self.assertIn("unreadable", render())
        on_blocked(task_id="t_missing")
        self.store.path.rmdir()
        self.store.add("staging prod migrations", "Use staging", ["staging", "prod"])
        events = Events()
        events.path.unlink(missing_ok=True)
        events.path.mkdir()
        self.assertIn("events unavailable", self.call()["message"])
        on_blocked(task_id="t_missing")

    def test_bad_board_and_no_task_do_not_veto_forever(self):
        self.assertIn("unavailable", self.call({**self.args, "board": "../bad"})["args"]["reason"])
        self.assertEqual(self.call(task="")["action"], "modify")

    def test_boards_isolate_matches_and_counters(self):
        self.assertEqual(self.call()["action"], "block")
        board = self.home / "kanban/boards/other"
        board.mkdir(parents=True)
        (board / "board.json").write_text('{"name":"other"}')
        with patch.dict(os.environ, {"HERMES_KANBAN_BOARD": "other"}):
            self.assertIn("checked 0 active rulings on board other", self.call()["args"]["reason"])
            Store().add("staging prod migrations", "Use another staging", ["staging", "prod"])
            self.assertEqual(self.call()["action"], "block")
            self.assertEqual(Events().summary()["gated_vetoes"], 1)
        self.assertEqual(Events().summary()["gated_vetoes"], 1)

    def test_observer_counts_actual_kind_read_only(self):
        from types import SimpleNamespace
        def dispatch(name, args):
            self.assertEqual(name, "kanban_show")
            kind = {"t_a": "needs_input", "t_b": "dependency"}.get(args["task_id"])
            return json.dumps({"task": {}, "events": [{"kind": "blocked", "payload": {"kind": kind, "reason": "question"}}]})
        ctx = SimpleNamespace(dispatch_tool=dispatch)
        for task in ("t_a", "t_b", "missing"):
            on_blocked(task_id=task, board="default", reason="question", ctx=ctx)
        summary = Events().summary()
        self.assertEqual(summary["needs_input_blocks"], 1)
        self.assertEqual(summary["unclassified_blocks"], 1)

    def test_full_gate_500_rulings_timing(self):
        # Build once under the normal store lock and measure the whole hot path.
        from precedent_log.store import ZERO, append_line, canonical, digest, locked, timestamp
        self.store.path.unlink()
        with locked(self.store.lock):
            previous = ZERO
            for n in range(1, 501):
                row = {"v": 1, "op": "add", "id": f"P-{n}", "board": "default", "question": "alpha beta gamma delta",
                       "ruling": "Do the recorded thing", "keys": [], "author": "test", "surface": "cli",
                       "source_task": None, "created_at": timestamp(), "prev": previous}
                row["h"] = digest(row)
                append_line(self.store.path, row)
                previous = hashlib.sha256((canonical(row) + "\n").encode()).hexdigest()
        samples = []
        for n in range(9):
            start = time.perf_counter()
            self.assertEqual(self.call({"reason": "alpha beta gamma"}, task=f"t_perf_{n}")["action"], "block")
            samples.append((time.perf_counter() - start) * 1000)
        print(f"Full gate, 500 rulings: median {statistics.median(samples):.3f} ms, max {max(samples):.3f} ms", flush=True)
        self.assertLess(statistics.median(samples), 40, "2x full I/O scheduling margin")

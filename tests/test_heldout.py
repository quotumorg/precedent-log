"""Frozen candidate-selection evaluation. Labels never tune the matcher."""

import support

import hashlib
import json

from support import IsolatedTest, REPO
from precedent_log.match import match
from precedent_log.store import Store


def evaluate():
    source = REPO / "tests/corpus-heldout.json"
    corpus = json.loads(source.read_text())
    row = {"id": "P-1", **corpus["ruling"]}
    results = []
    for case in corpus["cases"]:
        shown = bool(match(case["reason"], [row]))
        results.append({**case, "candidate_shown": shown,
                        "correct": shown == (case["expected"] == "same decision")})
    return {"corpus_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "counts": {"total": len(results), "correct": sum(r["correct"] for r in results),
                       "true_positive": sum(r["candidate_shown"] and r["correct"] for r in results),
                       "true_negative": sum(not r["candidate_shown"] and r["correct"] for r in results),
                       "false_positive": sum(r["candidate_shown"] and not r["correct"] for r in results),
                       "false_negative": sum(not r["candidate_shown"] and not r["correct"] for r in results)},
            "results": results}


class HeldoutTests(IsolatedTest):
    def test_frozen_results_and_retirement(self):
        actual = evaluate()
        recorded = json.loads((REPO / "tests/evidence/heldout-r3.json").read_text())
        self.assertEqual(actual, recorded)
        self.assertEqual(actual["counts"]["total"], 20)
        corpus = json.loads((REPO / "tests/corpus-heldout.json").read_text())
        store = Store()
        row = store.add(**corpus["ruling"])
        for case in actual["results"]:
            self.assertEqual(bool(match(case["reason"], store.list())), case["candidate_shown"])
        store.retire(row["id"], "Retirement test")
        self.assertFalse(any(match(case["reason"], store.list()) for case in actual["results"]))


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))

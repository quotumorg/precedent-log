import support

import statistics
import time
import unittest

from precedent_log.match import match, normalize


def ruling(n, question, keys=()):
    return {"id": f"P-{n}", "question": question, "ruling": "Answer", "keys": list(keys)}


class MatchTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize("The MIGRATIONS, DBs / tickets! 2026"), {"migration", "dbs", "ticket", "2026"})

    def test_all_keys_and_whole_words(self):
        row = ruling(1, "staging prod database", ["migrations", "prod", "db"])
        self.assertEqual(match("migration prod db", [row]), [row])
        self.assertEqual(match("migration prod", [row]), [])
        self.assertEqual(match("migration production db", [row]), [])

    def test_sixty_percent_and_two_word_floor(self):
        row = ruling(1, "alpha beta gamma delta epsilon")
        self.assertEqual(match("alpha beta gamma", [row]), [row])
        self.assertEqual(match("alpha beta", [row]), [])
        self.assertEqual(match("alpha", [ruling(2, "alpha")]), [])
        self.assertEqual(match("alpha beta", [ruling(3, "alpha beta gamma")])[0]["id"], "P-3")
        self.assertEqual(match("the and", [ruling(4, "the and")]), [])

    def test_keys_do_not_fallback_and_empty_normalized_key(self):
        self.assertEqual(match("alpha beta", [ruling(1, "alpha beta", ["gamma"])]), [])
        self.assertEqual(match("alpha beta", [ruling(1, "alpha beta", ["the"])]), [])

    def test_top_three_score_then_newest(self):
        rows = [ruling(n, "alpha beta") for n in range(1, 6)]
        rows.append(ruling(6, "alpha beta gamma"))
        self.assertEqual([row["id"] for row in match("alpha beta", rows)], ["P-5", "P-4", "P-3"])

    def test_500_rulings_timing(self):
        rows = [ruling(n, "staging prod database migration policy") for n in range(1, 501)]
        samples = []
        for _ in range(21):
            start = time.perf_counter()
            self.assertEqual(len(match("staging prod database migration", rows)), 3)
            samples.append((time.perf_counter() - start) * 1000)
        measured = statistics.median(samples)
        print(f"Matcher, 500 rulings: median {measured:.3f} ms, max {max(samples):.3f} ms (budget 20 ms)", flush=True)
        self.assertLess(measured, 20)
        self.assertLess(max(samples), 80, "4x scheduling margin for individual samples")

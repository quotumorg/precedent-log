"""Always-on public-tree privacy checks and offline evidence verification."""
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
PATTERNS = {
    'absolute home path': re.compile(r'/(?:Users|home)/[^<]'),
    'email': re.compile(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}'),
    'provider key': re.compile(r'\bsk-[A-Za-z0-9_-]{15,}'),
    'opaque blob': re.compile(r'[A-Za-z0-9_+/=-]{121,}'),
}


def public_files(root=REPO):
    if (root / '.git').exists():
        names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0')
        return [root / name for name in names if name]
    # A clean archive has no Git metadata. Scan every exported file, never a parent repo.
    return [p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts]


def violations(text):
    return [label for label, pattern in PATTERNS.items() if pattern.search(text)]


def denylist(path, root=REPO):
    path = Path(path).resolve()
    if path.is_relative_to(root.resolve()):
        raise ValueError('Private denylist must live outside the repository')
    return [line for line in path.read_text().splitlines() if line and not line.startswith('#')]


def recompute(edition="r5"):
    spec = importlib.util.spec_from_file_location('live_recompute', REPO / f'evidence/live-{edition}/recompute.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicationTests(unittest.TestCase):
    def test_tracked_tree_privacy(self):
        files = public_files()
        self.assertTrue(files)
        for path in files:
            with self.subTest(file=path.relative_to(REPO).as_posix()):
                text = path.read_bytes().decode('utf-8', errors='replace')
                self.assertEqual(violations(text), [])
                self.assertNotIn(chr(0x2014), text)

    @unittest.skipUnless(os.environ.get('PRECEDENT_PRIVATE_DENYLIST'), 'optional private denylist not configured')
    def test_optional_private_denylist(self):
        terms = denylist(os.environ['PRECEDENT_PRIVATE_DENYLIST'])
        for path in public_files():
            text = path.read_bytes().decode('utf-8', errors='replace')
            # Do not leak private matches into a shareable test log.
            self.assertFalse(any(term in text for term in terms), path.relative_to(REPO).as_posix())

    def test_privacy_patterns_detect_required_leaks(self):
        samples = {
            'absolute home path': '/' + 'Users/person/file',
            'email': 'person' + '@' + 'example.invalid',
            'provider key': 'sk-' + 'a' * 20,
            'opaque blob': 'aB9+' * 31,
        }
        for label, sample in samples.items():
            self.assertIn(label, violations(sample))
        self.assertIn('absolute home path', violations('/' + 'home/person/file'))
        self.assertEqual(violations('<home>/file <run-root>/file ' + 'a' * 120), [])

    def test_private_denylist_must_be_external(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            denylist(REPO / 'private.txt')
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'deny.txt'
            path.write_text('# comment\n\nprivate-folder\n')
            self.assertEqual(denylist(path), ['private-folder'])

    def test_redactor_preserves_nested_json_and_counts(self):
        recompute()  # Adds the plugin checkout to sys.path without importing Hermes.
        from evidence.redact import redact
        original = '/' + 'Users/person'
        nested = json.dumps({'path': original + '/run/file', 'signature': 'a' * 121,
                             'message': 'before' + chr(0x2014) + 'after'})
        text = json.dumps({'nested': nested, 'home': original + '/elsewhere', 'short': 'b' * 120})
        cleaned, counts = redact(text, [(original + '/run', '<run-root>')])
        decoded = json.loads(cleaned)
        self.assertEqual(json.loads(decoded['nested']), {'path': '<run-root>/file',
                         'signature': '<opaque 121 chars>', 'message': 'before:after'})
        self.assertEqual(decoded['home'], '<home>/elsewhere')
        self.assertEqual(decoded['short'], 'b' * 120)
        self.assertEqual(counts, {'P1': 1, 'H': 1, 'O': 1, 'D': 1})

    def test_public_evidence_recomputes_readme_and_all_attempts(self):
        module = recompute()
        table = module.check_readme()
        self.assertEqual(module.verify_files(), 89)
        self.assertEqual(table.count('`veto`'), 2)
        self.assertNotIn('`prompt`', table)
        self.assertIn('Warm-up (both starts kept) | Ready; exits 1, 0 | Ready; exits 1, 0 | Ready; exits 1, 0', table)
        self.assertIn('Harness failures | 0 | 0 | 0', table)
        self.assertIn('Worker exit codes (all attempts) | 0, 0, 0, 0, 0 | 0, 0, 0, 0, 0 | 0, 0, 0, 0, 0', table)

    def test_current_live_evidence_preserves_per_run_outcomes(self):
        module = recompute('r14')
        table = module.check_readme()
        self.assertEqual(module.verify_files(), 176)
        self.assertEqual(table.count('`veto`'), 2)
        self.assertIn('Run 1: `blocked`, `needs_input`, no final file; no citation path', table)
        self.assertIn('Run 2: `blocked`, `needs_input`, final file; no citation path', table)
        self.assertIn('Harness failures | 0 | Run 1: 0<br>Run 2: 1 | 0 | 0', table)
        self.assertIn('Ready; exits 1, 0 | Ready; exits 1, 0 | Ready; exits 1, 0 | Ready; exits 0', table)
        self.assertNotIn('`prompt`', table)

    def test_multi_fixture_evidence_recomputes_outcomes_and_summary(self):
        module = recompute('r17')
        text = module.check_readme()
        self.assertEqual(module.verify_files(), 517)
        self.assertIn('hook T2 completed 6/6; prompt only 3/6', text)
        self.assertIn('done via veto; 3 failures | done via veto; 1 failure', text)
        self.assertIn('not run (provider 402)', text)
        self.assertIn('DeepSeek T3: 3 blocked needs_input, 1 provider 402', text)

    def test_billing_capture_cannot_be_counted_as_model_completion(self):
        module = recompute('r17')
        data = module.capture('m17b-qwen-log-retention-enforce')
        self.assertTrue(module.excluded(data))
        # Even a misleading final card state must not turn a billing failure into evidence.
        data['cards']['T2']['state'] = 'done'
        self.assertEqual(module.outcome(data), 'not run (provider 402)')
        data = module.capture('m17-deepseek-migration-enforce')
        self.assertFalse(module.excluded(data))
        self.assertFalse(any(module.billing(a) for a in data['attempts'] if a['label'] == 'T2'))
        self.assertTrue(any(module.billing(a) for a in data['attempts'] if a['label'] == 'T3'))

    def test_manifest_rejects_changed_bytes_and_unlisted_files(self):
        module = recompute()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = root / '__fixtures__/capture.txt'
            fixture.parent.mkdir()
            fixture.write_text('changed')
            (root / 'MANIFEST.json').write_text(json.dumps({'__fixtures__/capture.txt': '0' * 64}))
            with patch.object(module, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'changed'):
                    module.verify_files()
                (root / '__fixtures__/extra.txt').write_text('extra')
                with self.assertRaisesRegex(ValueError, 'inventory'):
                    module.verify_files()


if __name__ == '__main__':
    unittest.main(verbosity=2)

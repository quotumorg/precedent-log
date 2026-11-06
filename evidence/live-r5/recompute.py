#!/usr/bin/env python3
"""Recompute observed live results from bundled messages and actual output files."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO))
from demo.run import citation_evidence
from evidence.redact import RUNS


def artifact(recorded):
    prefix = '<run-root>/'
    if not recorded.startswith(prefix):
        raise ValueError('Unexpected recorded artifact path')
    root = (ROOT / '__fixtures__').resolve()
    path = (root / recorded[len(prefix):]).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Artifact escaped evidence tree')
    return path


def verify_files():
    manifest = json.loads((ROOT / 'MANIFEST.json').read_text())
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / '__fixtures__').rglob('*') if p.is_file()}
    if actual != set(manifest):
        raise ValueError('Evidence inventory differs from manifest')
    for name, expected in manifest.items():
        path = ROOT / name
        if path.is_symlink() or not path.resolve().is_relative_to((ROOT / '__fixtures__').resolve()):
            raise ValueError('Invalid manifest path: ' + name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Redacted evidence changed: ' + name)
    return len(manifest)


def observe(run):
    data = json.loads((ROOT / '__fixtures__' / run / 'transcript.json').read_text())
    if not data['finished']:
        raise ValueError('Incomplete recorded run: ' + run)
    cards = data['cards']
    for card in cards.values():
        path = artifact(card['output_file'])
        if path.is_file() != card['output_present']:
            raise ValueError('Output presence disagrees: ' + str(path))
        if path.is_file() and path.read_text() != card['output_content']:
            raise ValueError('Output bytes disagree with transcript: ' + str(path))
    for attempt in data['attempts']:
        spec = json.loads(artifact(attempt['spec_file']).read_text())
        if spec['task_id'] != attempt['task_id']:
            raise ValueError('Attempt spec task disagrees: ' + run)
        if json.loads(artifact(attempt['result_file']).read_text()) != attempt['worker']:
            raise ValueError('Attempt result disagrees: ' + run)
    first = next(s for s in data['steps'] if s['label'] == 'T1' and s['phase'].startswith('attempt-'))
    t2 = cards['T2']
    evidence = citation_evidence([a for a in data['attempts'] if a['label'] == 'T2'],
                                artifact(t2['output_file']).read_text() if t2['output_present'] else '')
    added = any(c['argv'][1:3] == ['precedent', 'add'] and c['returncode'] == 0 for c in data['commands'])
    retired = any(c['argv'][1:3] == ['precedent', 'retire'] and c['returncode'] == 0 for c in data['commands'])

    def blocked(card):
        return f"`{card['state']}`, `{card['block_kind']}`, " + ('final file' if card['output_present'] else 'no final file')

    if t2['state'] == 'done':
        if not evidence['citation_found'] or evidence['citation_path'] not in ('veto', 'prompt'):
            raise ValueError('T2 completed without observed citation path: ' + run)
        second = f"`done`; P-1 in file and summary; `{evidence['citation_path']}`"
    else:
        second = blocked(t2) + '; no citation path'
    rejection = bool(re.search(r'no precedent applies:.*\bP-1\b', cards['T3']['last_reason_or_summary'], re.I | re.S))
    warmups = data['warmups']
    warmed = bool(warmups and warmups[-1]['returncode'] == 0 and warmups[-1]['runtime'].get('initialized'))
    return [
        ('Ready' if warmed else 'Failed') + '; exits ' + ', '.join(str(w['returncode']) for w in warmups),
        blocked(first),
        ('Add P-1, unblock' if added else 'Unblock only') + f"; `{cards['T1']['state']}`, users-plan.md",
        second,
        ('P-1 rejection marker; ' if rejection else '') + blocked(cards['T3']),
        ('P-1 retired; ' if retired else '') + blocked(cards['T4']),
        ', '.join(str(a['exit_code']) for a in data['attempts']),
        str(len(data['failures'])),
    ]


def table():
    verify_files()
    observed = [observe(run) for run in RUNS]
    labels = ('Warm-up (both starts kept)', 'T1, first worker attempt', 'Answer T1', 'T2, same decision',
              'T3, fixture instruction-following', 'T4, after retirement', 'Worker exit codes (all attempts)',
              'Harness failures')
    lines = ['| Step | Haiku with plugin | Sonnet with plugin | Haiku without plugin |',
             '| --- | --- | --- | --- |']
    for index, label in enumerate(labels):
        lines.append('| ' + ' | '.join([label, *(run[index] for run in observed)]) + ' |')
    return '\n'.join(lines)


def check_readme():
    actual = table()
    section = (REPO / 'README.md').read_text().split('## Live run\n', 1)[1].split('\n## ', 1)[0]
    if actual not in section:
        raise ValueError('README live table differs from bundled evidence')
    return actual


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-readme', action='store_true')
    args = parser.parse_args()
    print(check_readme() if args.check_readme else table())

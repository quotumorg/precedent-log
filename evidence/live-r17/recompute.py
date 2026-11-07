#!/usr/bin/env python3
"""Recompute the multi-fixture table, excluding provider failures from model outcomes."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
spec = importlib.util.spec_from_file_location('r5_observer_for_r17', ROOT.parent / 'live-r5/recompute.py')
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
FIXTURES = ('migration', 'dependency-upgrade', 'customer-copy', 'log-retention')
COLUMNS = (('Haiku hook (enforce)', 'haiku', 'enforce', 'claude-haiku-5-5'),
           ('Haiku prompt only (advisory)', 'haiku', 'advisory', 'claude-haiku-5-5'),
           ('DeepSeek hook', 'deepseek', 'enforce', 'deepseek-v4-pro'),
           ('qwen hook', 'qwen', 'enforce', 'qwen-3-8-flash'))


def run_name(fixture, model, mode):
    prefix = 'm17' if model == 'haiku' or fixture == 'migration' else 'm17b'
    return f'{prefix}-{model}-{fixture}-{mode}'


def capture(run):
    return json.loads((ROOT / '__fixtures__' / run / 'transcript.json').read_text())


def billing(attempt):
    return bool(re.search(r'\bHTTP\s+402\b|\bError code:\s*402\b', json.dumps(attempt), re.I))


def excluded(data):
    # All reruns containing a billing failure are audit-only, even if T1 finished.
    return data['run_id'].startswith('m17b-') and any(map(billing, data['attempts']))


def verify_files():
    observer.ROOT = ROOT
    count = observer.verify_files()
    expected = {run_name(f, m, mode) for f in FIXTURES for _, m, mode, _ in COLUMNS}
    if {p.name for p in (ROOT / '__fixtures__').iterdir()} != expected:
        raise ValueError('Unexpected run inventory')
    for fixture in FIXTURES:
        fixture_file = REPO / 'demo/tasks.json'
        expected_hash = hashlib.sha256(fixture_file.read_bytes()).hexdigest()
        for _, model, mode, model_id in COLUMNS:
            run = run_name(fixture, model, mode)
            data = capture(run)
            if (data['plugin'], data['fixture'], data['veto'], data['model'], data['tasks_sha256']) != (
                    True, fixture, mode, model_id, expected_hash):
                raise ValueError('Run configuration or fixture hash disagrees: ' + run)
            observer.observe(run)  # Verify attempt results, output presence/content and T2 citation traces.
            for attempt in data['attempts']:
                worker_spec = json.loads(observer.artifact(attempt['spec_file']).read_text())
                if worker_spec['timeout'] != 180 or attempt['exit_code'] != attempt['worker']['exit_code']:
                    raise ValueError('Worker record disagrees: ' + run)
            for warmup in data['warmups']:
                warm_spec = json.loads(observer.artifact(warmup['argv'][-1]).read_text())
                result = json.loads(observer.artifact(warm_spec['result_file']).read_text())
                if warm_spec['timeout'] != 300 or result != warmup['runtime'] or result['exit_code'] != warmup['returncode']:
                    raise ValueError('Warm-up record disagrees: ' + run)
    return count


def outcome(data):
    attempts = [a for a in data['attempts'] if a['label'] == 'T2']
    if excluded(data) or any(map(billing, attempts)):
        return 'not run (provider 402)'
    card = data['cards']['T2']
    if card['state'] == 'done':
        evidence = observer.citation_evidence(attempts, observer.artifact(card['output_file']).read_text())
        if not evidence['citation_found'] or evidence['citation_path'] not in ('veto', 'prompt'):
            raise ValueError('Completion lacks an observed citation path')
        return 'done via ' + evidence['citation_path']
    if card['state'] != 'blocked':
        raise ValueError('Unexpected T2 state')
    return 'blocked'


def table():
    verify_files()
    lines = ['| Fixture | ' + ' | '.join(c[0] for c in COLUMNS) + ' |',
             '| --- | --- | --- | --- | --- |']
    for fixture in FIXTURES:
        cells = []
        for _, model, mode, _ in COLUMNS:
            data = capture(run_name(fixture, model, mode))
            result = outcome(data)
            cells.append(result if result.startswith('not run') else f"{result}; {len(data['failures'])} failure" + ("" if len(data['failures']) == 1 else "s"))
        lines.append('| ' + ' | '.join([fixture, *cells]) + ' |')
    return '\n'.join(lines)


def summary():
    verify_files()
    counts = []
    for mode, earlier in [('enforce', ('rec-treatment', 'rec-treatment-2')),
                          ('advisory', ('rec-advisory', 'rec-advisory-2'))]:
        states = [capture(run_name(f, 'haiku', mode))['cards']['T2']['state'] for f in FIXTURES]
        observer.ROOT = ROOT.parent / 'live-r14'
        observer.verify_files()
        for run in earlier:
            observer.observe(run)
            data = json.loads((observer.ROOT / '__fixtures__' / run / 'transcript.json').read_text())
            states.append(data['cards']['T2']['state'])
        counts.append(f"{states.count('done')}/{len(states)}")
        observer.ROOT = ROOT
    return f'Haiku: hook T2 completed {counts[0]}; prompt only {counts[1]} (including the r14 migration runs).'


def later_outcomes():
    parts = []
    for title, model in [('Haiku', 'haiku'), ('DeepSeek', 'deepseek'), ('qwen', 'qwen')]:
        stage_counts = []
        runs = [capture(run_name(f, m, mode)) for f in FIXTURES for _, m, mode, _ in COLUMNS if m == model]
        for stage in ('T3', 'T4'):
            counts = Counter()
            for data in runs:
                if excluded(data):
                    counts['excluded billing run'] += 1
                elif any(billing(a) for a in data['attempts'] if a['label'] == stage):
                    counts['provider 402'] += 1
                else:
                    card = data['cards'][stage]
                    if card['state'] != 'blocked' or card['block_kind'] != 'needs_input' or card['output_present']:
                        raise ValueError('Unexpected later outcome')
                    if stage == 'T4' and not any(c['argv'][1:3] == ['precedent', 'retire'] and c['returncode'] == 0 for c in data['commands']):
                        raise ValueError('Missing retirement')
                    counts['blocked needs_input'] += 1
            stage_counts.append(stage + ': ' + ', '.join(f'{n} {label}' for label, n in sorted(counts.items())))
        parts.append(title + ' ' + '; '.join(stage_counts))
    return 'T3/T4 on ee78019: ' + '. '.join(parts) + '.'


def check_readme():
    texts = (table(), summary(), later_outcomes())
    section = (REPO / 'README.md').read_text().split('## Live run\n', 1)[1].split('\n## ', 1)[0]
    if any(text not in section for text in texts):
        raise ValueError('README differs from bundled multi-fixture evidence')
    return '\n\n'.join(texts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-readme', action='store_true')
    args = parser.parse_args()
    print(check_readme() if args.check_readme else '\n\n'.join((table(), summary(), later_outcomes())))

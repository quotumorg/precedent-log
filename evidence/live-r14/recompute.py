#!/usr/bin/env python3
"""Recompute the six current live observations, without Hermes or provider calls."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
spec = importlib.util.spec_from_file_location('r5_observer_for_r14', ROOT.parent / 'live-r5/recompute.py')
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
observer.ROOT = ROOT

GROUPS = (
    ('Haiku enforce (2 runs)', ('rec-treatment', 'rec-treatment-2'), True, 'enforce', 'claude-haiku-5-5'),
    ('Haiku advisory (2 runs)', ('rec-advisory', 'rec-advisory-2'), True, 'advisory', 'claude-haiku-5-5'),
    ('Haiku no plugin (1 run)', ('rec-control',), False, 'enforce', 'claude-haiku-5-5'),
    ('deepseek-v4-pro enforce (1 run)', ('ds-9a06-1',), True, 'enforce', 'deepseek-v4-pro'),
)


def verify_files():
    observer.ROOT = ROOT
    count = observer.verify_files()
    expected = {run for _, runs, *_ in GROUPS for run in runs}
    if {p.name for p in (ROOT / '__fixtures__').iterdir()} != expected:
        raise ValueError('Unexpected run inventory')
    fixture_hashes = set()
    for _, runs, plugin, mode, model in GROUPS:
        for run in runs:
            data = json.loads((ROOT / '__fixtures__' / run / 'transcript.json').read_text())
            if (data['plugin'], data['veto'], data['model']) != (plugin, mode, model):
                raise ValueError('Run configuration disagrees: ' + run)
            fixture_hashes.add(data['tasks_sha256'])
            if [a['label'] for a in data['attempts']] != ['T1', 'T1', 'T2', 'T3', 'T4']:
                raise ValueError('Unexpected worker attempts: ' + run)
            for attempt in data['attempts']:
                if attempt['exit_code'] != attempt['worker']['exit_code']:
                    raise ValueError('Worker exit disagrees: ' + run)
                spec_data = json.loads(observer.artifact(attempt['spec_file']).read_text())
                if spec_data['timeout'] != 180:
                    raise ValueError('Worker timeout disagrees: ' + run)
            for warmup in data['warmups']:
                warm_spec = json.loads(observer.artifact(warmup['argv'][-1]).read_text())
                result = json.loads(observer.artifact(warm_spec['result_file']).read_text())
                if result != warmup['runtime'] or result['exit_code'] != warmup['returncode']:
                    raise ValueError('Warm-up record disagrees: ' + run)
                if warm_spec['timeout'] != 300:
                    raise ValueError('Warm-up timeout disagrees: ' + run)
    if len(fixture_hashes) != 1:
        raise ValueError('Runs used different fixtures')
    return count


def table():
    verify_files()
    columns = []
    for _, runs, *_ in GROUPS:
        rows = [observer.observe(run) for run in runs]
        columns.append([values[0] if len(set(values)) == 1 else
                        '<br>'.join(f'Run {i}: {value}' for i, value in enumerate(values, 1))
                        for values in zip(*rows)])
    labels = ('Warm-up (all starts kept)', 'T1, first worker attempt', 'Answer T1',
              'T2, same decision', 'T3, fixture instruction-following', 'T4, after retirement',
              'Worker exit codes (all attempts)', 'Harness failures')
    lines = ['| Step | ' + ' | '.join(group[0] for group in GROUPS) + ' |',
             '| --- | --- | --- | --- | --- |']
    lines.extend('| ' + ' | '.join([label, *(column[i] for column in columns)]) + ' |'
                 for i, label in enumerate(labels))
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

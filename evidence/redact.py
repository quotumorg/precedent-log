#!/usr/bin/env python3
"""Copy recorded evidence with explicit, counted substitutions; never edit sources."""
import argparse
import hashlib
import json
from pathlib import Path
import re


RUNS = ('haiku-r5', 'sonnet-r5', 'haiku-r5-control')
HOME_PATH = re.compile(r'/(?:Users|home)/[^/\s"\x27\\<>]+')
OPAQUE = re.compile(r'[A-Za-z0-9_+/=-]{121,}')


def redact(text, prefixes):
    counts = {}
    for index, (source, placeholder) in enumerate(prefixes, 1):
        counts[f'P{index}'] = text.count(source)
        text = text.replace(source, placeholder)
    text, counts['H'] = HOME_PATH.subn('<home>', text)
    text, counts['O'] = OPAQUE.subn(lambda m: f'<opaque {len(m[0])} chars>', text)
    # Preserve wording; disclose this required punctuation normalization separately.
    counts['D'] = text.count(chr(0x2014))
    text = text.replace(chr(0x2014), ':')
    text, escaped = re.subn(r'\\+u2014', ':', text)
    counts['D'] += escaped
    return text, counts


def copy_evidence(source, destination, prefixes, run_sources=None, edition="r5"):
    source, destination = source.resolve(), destination.resolve()
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError('Source and destination must be separate trees')
    if (destination / '__fixtures__').exists():
        raise ValueError('Refusing to overwrite an existing evidence capture')
    for original, placeholder in prefixes:
        if not original or not re.fullmatch(r'<[a-z-]+>', placeholder):
            raise ValueError('Prefixes need a nonempty source and a placeholder label')
    if edition not in ('r5', 'r14', 'r17'):
        raise ValueError('Unknown evidence edition')
    sources = run_sources or [(run, source / run) for run in RUNS]
    if len({name for name, _ in sources}) != len(sources):
        raise ValueError('Duplicate run name')
    manifest, rows = {}, []
    for run, run_root in sources:
        if not re.fullmatch(r'[a-z0-9-]+', run):
            raise ValueError('Invalid run name')
        root = Path(run_root).resolve()
        if destination.is_relative_to(root) or root.is_relative_to(destination):
            raise ValueError('Source and destination must be separate trees')
        files = [root / 'transcript.json']
        for folder in ('attempts', 'workspaces'):
            files.extend(p for p in (root / folder).rglob('*') if p.is_file())
        for path in sorted(files):
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError('Evidence source must be a regular local file')
            relative = Path('__fixtures__') / run / path.relative_to(root)
            text, counts = redact(path.read_text(), prefixes)
            if path.suffix == '.json':
                json.loads(text)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
            manifest[relative.as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
            rows.append((relative.as_posix(), counts))
    destination.joinpath('MANIFEST.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    rules = [f'P{i}: supplied {"account label" if label == "<user>" else "prefix"} {i} becomes `{label}` (literal replacement, in argument order).'
             for i, (_, label) in enumerate(prefixes, 1)]
    rules.extend([
        'H: any remaining absolute macOS or Linux user-home prefix becomes `<home>`; suffixes remain.',
        'O: each maximal base64-like or URL-safe token longer than 120 characters becomes `<opaque N chars>`, where N is its original length. The alphabet is ASCII letters, digits, underscore, plus, slash, equals and hyphen.',
        'D: literal and JSON-escaped U+2014 punctuation becomes a colon. No wording is paraphrased.',
    ])
    keys = [f'P{i}' for i in range(1, len(prefixes) + 1)] + ['H', 'O', 'D']
    lines = [
        f'# Live {edition} public evidence', '',
        f'All {len(manifest)} source transcripts, attempt records (including all warm-up starts), and workspace files are copied. No messages, failed starts, worker results or output files are dropped. Source files are unchanged. Hermes homes are not included. `__fixtures__/` is the scanner-recognized inert data path; the plugin never imports these recordings.', '',
        *(['an earlier private run inside a git checkout was discarded because the worker could read unrelated files; it is not used as evidence', ''] if edition == 'r5' else []),
        '## Rules', '',
        'Private prefixes are supplied only on the command line, never stored in this script or report. The ordered rules below name only their replacement placeholders. Counts include duplicated text in transcripts and standalone records.', '',
        *[f'- {rule}' for rule in rules], '',
        '## Per-file replacement counts', '',
        '| File | ' + ' | '.join(keys) + ' |',
        '| --- | ' + ' | '.join('---:' for _ in keys) + ' |',
        *['| `' + name + '` | ' + ' | '.join(str(counts[k]) for k in keys) + ' |' for name, counts in rows],
        '| Total | ' + ' | '.join(str(sum(c[k] for _, c in rows)) for k in keys) + ' |', '',
        '## Recompute and limits', '',
        f'Run `python3 -B evidence/live-{edition}/recompute.py --check-readme` from the plugin checkout. It checks the exact fixture inventory, SHA-256 hashes, attempt records and output files, then derives the table from recorded commands, states and tool exchanges. Original in-transcript hashes and byte counts describe original bytes, before redaction; the manifest covers public bytes and does not authenticate authorship.', '',
        ('Three runs, one model family (Claude Haiku 5.5 and Sonnet 5.5), warm-up used, no real B2. The supplied r5 run used a clean archive of bee2e2c outside Git. All three first warm-up starts exited 1 before a successful retry; all worker exits were 0. T3 explicitly instructs rejection of non-matching rulings, so it is an instruction-following observation, not a safety evaluation. The local dispatch adapter is not the standard gateway. T2 path labels describe tool traces, not internal reasoning. In the discarded private r3 runs, one Haiku T2 took the prompt path; it is not public evidence.' if edition == 'r5' else
         'Six runs, two model families, one fixture, no real B2. Supplied provenance: public codeload export of 9a06174 outside Git, Hermes v0.23.0 at 2bd378ed, demo/run.py, worker timeout 180 seconds and warm-up timeout 300 seconds. Five Haiku runs used the Anthropic API; deepseek-v4-pro used Venice (OpenAI-compatible endpoint). All five Haiku first warm-ups exited 1, then 0; the DeepSeek warm-up exited 0. All 30 worker attempts exited 0. Advisory Run 2 left T2 blocked despite writing its final file and recorded one harness failure; the other five runs recorded none. Both advisory T2 outcomes remain blocked. T2 explicitly requests a block to test escalation; T3 instructs rejection of non-matching rulings. These are fixture-specific observations, not a reliability estimate or safety evaluation. The local dispatch adapter is not the standard gateway. Path labels describe tool traces, not internal reasoning. Provenance is supplied by the capture owner, not authenticated by the manifest.'), '',
    ]
    if edition == 'r17':
        lines[-2] = ('Sixteen captures across four fixtures: eight Haiku, four DeepSeek, four qwen. '
                     'One qwen capture has HTTP 402 during T2 and is retained only for audit, not model evidence. '
                     'Supplied provenance: public codeload export of ee78019 outside Git, Hermes v0.23.0 at 2bd378ed, '
                     'worker timeout 180 seconds and warm-up timeout 300 seconds. '
                     'Haiku used the Anthropic API; deepseek-v4-pro and qwen-3-8-flash used Venice (OpenAI-compatible endpoint). '
                     'All starts and failures in included captures are retained. Provenance is supplied by the capture owner; '
                     'the manifest authenticates neither authorship nor the source checkout. '
                     'See README for per-stage billing exclusions, fixture limits and observed outcomes.')
    destination.joinpath('REDACTIONS.md').write_text('\n'.join(lines))
    return len(manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--prefix', nargs=2, action='append', required=True,
                        metavar=('PRIVATE_PREFIX', 'PLACEHOLDER'))
    parser.add_argument('--run-source', nargs=2, action='append', metavar=('RUN', 'DIRECTORY'),
                        help='Explicit run directories; replaces the default r5 runs')
    parser.add_argument('--edition', choices=('r5', 'r14', 'r17'), default='r5')
    args = parser.parse_args()
    print(f'Copied {copy_evidence(args.source, args.destination, args.prefix, args.run_source, args.edition)} files')

"""Read-only release preflight, without importing or starting a Hermes runtime."""
from types import SimpleNamespace
from unittest.mock import patch

from support import IsolatedTest
from demo.run import preflight


class DemoVersionTests(IsolatedTest):
    def source(self, version='0.0.0'):
        for name in ('hermes_cli/main.py', 'run_agent.py', 'tests/fakes/fake_llm_provider.py'):
            path = self.home / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('class FakeLLMServer: pass\nclass Text: pass\nclass ToolCall: pass\n')
        (self.home / 'pyproject.toml').write_text(f'[project]\nversion = "{version}"\n')
        return self.home

    def test_package_releases_and_interpreters(self):
        for version in ('0.23.0', '0.23.1', '0.23.99'):
            source = self.source(version)
            before = {p: p.read_bytes() for p in source.rglob('*') if p.is_file()}
            for python in ((3, 11), (3, 13), (3, 14)):
                with self.subTest(version=version, python=python), patch('demo.run.sys.version_info', python), \
                        patch('demo.run.subprocess.run') as git:
                    self.assertEqual(preflight(source), source.resolve())
                    git.assert_not_called()
            self.assertEqual(before, {p: p.read_bytes() for p in source.rglob('*') if p.is_file()})

    def test_exact_release_tag_fallback(self):
        source = self.source()
        for tag in ('v0.23.0', 'v0.23.1', 'v0.23.12'):
            with self.subTest(tag=tag), patch('demo.run.subprocess.run',
                    return_value=SimpleNamespace(returncode=0, stdout=tag + '\n')) as git:
                self.assertEqual(preflight(source), source.resolve())
                self.assertIn('--exact-match', git.call_args.args[0])

    def test_out_of_range_prerelease_and_missing_versions_refuse(self):
        for version in ('0.22.99', '0.24.0', '1.23.0', '0.23.0rc1', '0.23.1.dev1', 'invalid'):
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, '>=0.23.0,<0.24'):
                preflight(self.source(version))
        source = self.source()
        for tag, rc in (('v0.22.9', 0), ('v0.24.0', 0), ('v0.23.0-rc1', 0), ('', 128)):
            with patch('demo.run.subprocess.run', return_value=SimpleNamespace(returncode=rc, stdout=tag)), \
                    self.assertRaisesRegex(ValueError, '>=0.23.0,<0.24'):
                preflight(source)

    def test_helper_still_requires_parseable_classes(self):
        source = self.source('0.23.1')
        helper = source / 'tests/fakes/fake_llm_provider.py'
        for content, error in (('class Text: pass', 'lacks FakeLLMServer'), ('class :', 'Cannot parse')):
            helper.write_text(content)
            with self.assertRaisesRegex(ValueError, error):
                preflight(source)

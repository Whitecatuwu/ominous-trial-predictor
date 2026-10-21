"""Exercise user-facing tool commands and failure exits without Minecraft."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import pytest
ROOT = Path(__file__).resolve().parents[2]

def command(script, *args):
    return subprocess.run([sys.executable, str(ROOT / 'scripts' / script), *map(str, args)], cwd=ROOT, capture_output=True, text=True)

class TestEvidence:

    @pytest.fixture(autouse=True)
    def cache_directory(self):
        (ROOT / '.cache').mkdir(exist_ok=True)

    def test_historical_sources_are_checked_at_their_commit(self):
        result = command('evidence.py', 'verify', 'validation/reference/evidence/2026-10-20', '--source-ref', '823e091')
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)['cases'] == 3

    @pytest.mark.parametrize('mutation', ['corrupt', 'missing', 'extra'])
    def test_missing_corrupt_and_extra_artifacts_fail(self, mutation):
        with tempfile.TemporaryDirectory(dir=ROOT / '.cache') as temporary:
            directory = Path(temporary) / 'reference/evidence/date'
            shutil.copytree(ROOT / 'validation/reference/evidence/2026-10-20', directory)
            shutil.copytree(ROOT / 'validation/reference/fixtures', directory.parent.parent / 'fixtures')
            target = directory / 'repeat-first.json'
            original = target.read_bytes()
            target.write_bytes(original)
            if mutation == 'corrupt':
                target.write_text('{}', encoding='utf-8')
            elif mutation == 'missing':
                target.unlink()
            else:
                (directory / 'unexpected.txt').write_text('extra', encoding='utf-8')
            result = command('evidence.py', 'verify', directory, '--source-ref', '823e091')
            assert result.returncode != 0

    def test_current_sources_cannot_claim_historical_pass(self):
        result = command('evidence.py', 'verify', 'validation/reference/evidence/2026-10-20', '--source-ref', 'worktree')
        assert result.returncode != 0
        assert 'Source hash mismatch' in result.stderr

    def test_archive_preserves_existing_snapshot(self):
        result = command('evidence.py', 'archive', 'validation/reference/evidence/2026-10-20', '--suite-log', '.cache/full-suite.log', '--metadata', 'missing.json')
        assert result.returncode != 0
        assert 'Destination exists' in result.stderr

class TestEnvironment:

    def test_integration_requires_explicit_eula_flag(self):
        result = command('dev.py', 'check', '--integration')
        assert result.returncode != 0
        assert '--accept-eula' in result.stderr

    def test_doctor_explains_optional_dependencies(self):
        result = command('dev.py', 'doctor')
        assert result.returncode == 0, result.stderr
        document = json.loads(result.stdout)
        assert not document['host_java_required']
        assert {r['name'] for r in document['checks']} == {'python', 'git', 'github_cli', 'docker_linux'}

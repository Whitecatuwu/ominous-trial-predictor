"""Archive behavior using disposable synthetic suite files, no Minecraft execution."""
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evidence

class TestArchive:

    @pytest.fixture(autouse=True, params=["Ran 2 tests\n\nOK\n", "================ 2 passed in 1.23s ================\n"])
    def archive_files(self, tmp_path, monkeypatch, request):
        self.root = tmp_path.resolve()
        monkeypatch.setattr(evidence, 'ROOT', self.root)

        def write(name, data):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data, encoding='utf-8', newline='\n')
            return path
        self.write = write
        for name in ('scripts/reference.py', 'validation/reference/Dockerfile', 'validation/reference/run.sh'):
            write(name, 'synthetic test source\n')
        self.cache = self.root / '.cache/reference-tests'
        reports = []
        repeat_logs = []
        result = '{"rows": [{"status": "ok"}]}\n'
        for name in ('seed-1', 'seed-min', 'seed-max', 'repeat-1', 'repeat-2'):
            run = self.root / '.cache/minecraft-26.2/runs' / name
            for filename, data in (('request.json', '{}'), ('provenance.json', '{}'), ('server.log', 'synthetic run'), ('output/server.properties', 'seed=1\n'), ('output/normalizer-tests.json', '{"passed":true}')):
                write((run / filename).relative_to(self.root), data)
            pointer = 'Reference logs and request: ' + str(run)
            if name.startswith('seed'):
                expected = write(f'validation/reference/fixtures/{name}.expected.json', result)
                actual = write(f'.cache/reference-tests/{name}.actual.json', result)
                reports.append({'case': name, 'passed': True, 'run_log': pointer, 'expected_sha256': evidence.digest(expected), 'actual_sha256': evidence.digest(actual)})
            else:
                repeat_logs.append(pointer)
        write('.cache/reference-tests/report.json', json.dumps(reports))
        write('.cache/reference-tests/repeat-runs.txt', '\n'.join(repeat_logs))
        for name in ('repeat-first', 'repeat-second'):
            write(f'.cache/reference-tests/{name}.json', result)
        self.log = write('.cache/full-suite.log', request.param)
        self.metadata = write('.cache/metadata.json', '{"host":{"os":"synthetic"},"runtime":{}}')
        outputs = [p for p in self.cache.iterdir() if p.is_file()]
        receipt = {'source_sha256': evidence.source_hashes(), 'suite_sha256': evidence.digest(self.log), 'run_sha256': evidence.run_artifacts(self.cache), 'result_sha256': {p.name: evidence.digest(p) for p in outputs}}
        write('.cache/reference-tests/suite-receipt.json', json.dumps(receipt))
        self.destination = self.root / 'validation/reference/evidence/test'

    def test_successful_archive_verifies_and_cannot_be_overwritten(self):
        evidence.archive(self.destination, self.log, self.metadata)
        assert evidence.verify(self.destination, 'worktree', self.root)['passed']
        with pytest.raises(ValueError, match='Destination exists'):
            evidence.archive(self.destination, self.log, self.metadata)

    def test_changed_provenance_after_suite_is_rejected_before_publish(self):
        self.write('.cache/minecraft-26.2/runs/seed-1/provenance.json', '{"image_id":"changed"}')
        with pytest.raises(ValueError, match='Run artifacts changed'):
            evidence.archive(self.destination, self.log, self.metadata)
        assert not self.destination.exists()

    def test_changed_source_after_suite_is_rejected(self):
        self.write('scripts/reference.py', 'changed source\n')
        with pytest.raises(ValueError, match='Sources changed'):
            evidence.archive(self.destination, self.log, self.metadata)
        assert not self.destination.exists()


@pytest.mark.parametrize("summary", ["", "2 skipped in 0.1s", "1 passed, 1 failed in 1.0s", "1 passed, 1 skipped in 1.0s", "no tests ran in 0.1s"])
def test_incomplete_suite_log_is_rejected(tmp_path, summary):
    log = tmp_path / "suite.log"
    log.write_text(summary, encoding="utf-8")
    assert not evidence.suite_passed(log)

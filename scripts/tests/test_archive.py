"""Archive behavior using disposable synthetic suite files, no Minecraft execution."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evidence


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.patch = patch.object(evidence, "ROOT", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)

        def write(name, data):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data, encoding="utf-8", newline="\n")
            return path

        self.write = write
        for name in ("scripts/reference.py", "validation/reference/Dockerfile", "validation/reference/run.sh"):
            write(name, "synthetic test source\n")
        self.cache = self.root / ".cache/reference-tests"
        reports = []
        repeat_logs = []
        result = '{"rows": [{"status": "ok"}]}\n'
        for name in ("seed-1", "seed-min", "seed-max", "repeat-1", "repeat-2"):
            run = self.root / ".cache/minecraft-26.2/runs" / name
            for filename, data in (("request.json", "{}"), ("provenance.json", "{}"),
                                   ("server.log", "synthetic run"), ("output/server.properties", "seed=1\n"),
                                   ("output/normalizer-tests.json", '{"passed":true}')):
                write((run / filename).relative_to(self.root), data)
            pointer = "Reference logs and request: " + str(run)
            if name.startswith("seed"):
                expected = write(f"validation/reference/fixtures/{name}.expected.json", result)
                actual = write(f".cache/reference-tests/{name}.actual.json", result)
                reports.append({"case": name, "passed": True, "run_log": pointer,
                                "expected_sha256": evidence.digest(expected),
                                "actual_sha256": evidence.digest(actual)})
            else:
                repeat_logs.append(pointer)
        write(".cache/reference-tests/report.json", json.dumps(reports))
        write(".cache/reference-tests/repeat-runs.txt", "\n".join(repeat_logs))
        for name in ("repeat-first", "repeat-second"):
            write(f".cache/reference-tests/{name}.json", result)
        self.log = write(".cache/full-suite.log", "Ran 2 tests\n\nOK\n")
        self.metadata = write(".cache/metadata.json", '{"host":{"os":"synthetic"},"runtime":{}}')
        outputs = [p for p in self.cache.iterdir() if p.is_file()]
        receipt = {"source_sha256": evidence.source_hashes(), "suite_sha256": evidence.digest(self.log),
                   "run_sha256": evidence.run_artifacts(self.cache),
                   "result_sha256": {p.name: evidence.digest(p) for p in outputs}}
        write(".cache/reference-tests/suite-receipt.json", json.dumps(receipt))
        self.destination = self.root / "validation/reference/evidence/test"

    def test_successful_archive_verifies_and_cannot_be_overwritten(self):
        evidence.archive(self.destination, self.log, self.metadata)
        self.assertTrue(evidence.verify(self.destination, "worktree", self.root)["passed"])
        with self.assertRaisesRegex(ValueError, "Destination exists"):
            evidence.archive(self.destination, self.log, self.metadata)

    def test_changed_provenance_after_suite_is_rejected_before_publish(self):
        self.write(".cache/minecraft-26.2/runs/seed-1/provenance.json", '{"image_id":"changed"}')
        with self.assertRaisesRegex(ValueError, "Run artifacts changed"):
            evidence.archive(self.destination, self.log, self.metadata)
        self.assertFalse(self.destination.exists())

    def test_changed_source_after_suite_is_rejected(self):
        self.write("scripts/reference.py", "changed source\n")
        with self.assertRaisesRegex(ValueError, "Sources changed"):
            evidence.archive(self.destination, self.log, self.metadata)
        self.assertFalse(self.destination.exists())

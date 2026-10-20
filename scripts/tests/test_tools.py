"""Exercise user-facing tool commands and failure exits without Minecraft."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def command(script, *args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / script), *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True)


class EvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / ".cache").mkdir(exist_ok=True)

    def test_historical_sources_are_checked_at_their_commit(self):
        result = command("evidence.py", "verify", "validation/reference/evidence/2026-10-20",
                         "--source-ref", "823e091")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["cases"], 3)

    def test_missing_corrupt_and_extra_artifacts_fail(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".cache") as temporary:
            directory = Path(temporary) / "reference/evidence/date"
            shutil.copytree(ROOT / "validation/reference/evidence/2026-10-20", directory)
            shutil.copytree(ROOT / "validation/reference/fixtures", directory.parent.parent / "fixtures")
            target = directory / "repeat-first.json"
            original = target.read_bytes()
            for mutation in ("corrupt", "missing", "extra"):
                with self.subTest(mutation=mutation):
                    target.write_bytes(original)
                    if mutation == "corrupt":
                        target.write_text("{}", encoding="utf-8")
                    elif mutation == "missing":
                        target.unlink()
                    else:
                        (directory / "unexpected.txt").write_text("extra", encoding="utf-8")
                    result = command("evidence.py", "verify", directory, "--source-ref", "823e091")
                    self.assertNotEqual(result.returncode, 0)

    def test_current_sources_cannot_claim_historical_pass(self):
        result = command("evidence.py", "verify", "validation/reference/evidence/2026-10-20",
                         "--source-ref", "worktree")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Source hash mismatch", result.stderr)

    def test_archive_preserves_existing_snapshot(self):
        result = command("evidence.py", "archive", "validation/reference/evidence/2026-10-20",
                         "--suite-log", ".cache/full-suite.log", "--metadata", "missing.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Destination exists", result.stderr)


class EnvironmentTest(unittest.TestCase):
    def test_integration_requires_explicit_eula_flag(self):
        result = command("dev.py", "check", "--integration")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--accept-eula", result.stderr)

    def test_doctor_explains_optional_dependencies(self):
        result = command("dev.py", "doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads(result.stdout)
        self.assertFalse(document["host_java_required"])
        self.assertEqual({r["name"] for r in document["checks"]},
                         {"python", "git", "github_cli", "docker_linux"})


if __name__ == "__main__":
    (ROOT / ".cache").mkdir(exist_ok=True)
    unittest.main()

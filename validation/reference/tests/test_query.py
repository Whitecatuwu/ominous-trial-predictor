"""Integration tests at the approved public reference command seam."""
import json
import os
import hashlib
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
ACTUALS = ROOT / ".cache/reference-tests"


@unittest.skipUnless(os.environ.get("REFERENCE_ACCEPT_EULA") == "true",
                     "Read Minecraft EULA and use scripts/dev.py check --integration --accept-eula")
class ReferenceQueryTest(unittest.TestCase):
    def test_original_query_is_complete_and_repeatable(self):
        command = [sys.executable, str(ROOT / "scripts/reference.py"), "query",
                   "--seed", "1", "--position", "0", "0", "0", "--accept-eula"]
        first = subprocess.run(command, capture_output=True, text=True, check=True)
        second = subprocess.run(command, capture_output=True, text=True, check=True)
        actual = json.loads(first.stdout)
        ACTUALS.mkdir(parents=True, exist_ok=True)
        (ACTUALS / "repeat-first.json").write_text(first.stdout, encoding="utf-8", newline="\n")
        (ACTUALS / "repeat-second.json").write_text(second.stdout, encoding="utf-8", newline="\n")
        (ACTUALS / "repeat-runs.txt").write_text(first.stderr + second.stderr, encoding="utf-8", newline="\n")
        self.assertEqual(actual, json.loads(second.stdout))
        self.assertEqual(actual["version_status"], "unverified")
        row = actual["rows"][0]
        self.assertEqual(row["status"], "ok")
        self.assertEqual(row["position"], {"x": 0, "y": 0, "z": 0})
        self.assertEqual(len(row["result"]["dispensing_items"]), 2)
        self.assertTrue(all("components" in item and "effects" in item
                            for item in row["result"]["dispensing_items"]))

    def test_saved_cases_match_original_reference(self):
        fixtures = ROOT / "validation/reference/fixtures"
        ACTUALS.mkdir(parents=True, exist_ok=True)
        reports = []
        (ACTUALS / "report.json").write_text("[]\n", encoding="utf-8", newline="\n")
        for case in ("seed-1", "seed-min", "seed-max"):
            with self.subTest(case=case):
                request = json.loads((fixtures / f"{case}.request.json").read_text(encoding="utf-8"))
                expected = json.loads((fixtures / f"{case}.expected.json").read_text(encoding="utf-8"))
                command = [sys.executable, str(ROOT / "scripts/reference.py"), "query",
                           "--seed", request["seed"], "--accept-eula", "--normalizer-tests"]
                for xyz in request["positions"]:
                    command.extend(["--position", *map(str, xyz)])
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                actual = json.loads(result.stdout)
                actual_path = ACTUALS / f"{case}.actual.json"
                actual_path.write_text(result.stdout, encoding="utf-8", newline="\n")
                reports.append({"case": case, "passed": actual == expected,
                                "expected_sha256": hashlib.sha256(
                                    (fixtures / f"{case}.expected.json").read_bytes()).hexdigest(),
                                "actual_sha256": hashlib.sha256(actual_path.read_bytes()).hexdigest(),
                                "run_log": result.stderr.strip()})
                (ACTUALS / "report.json").write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8", newline="\n")
                self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()

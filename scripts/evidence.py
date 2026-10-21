#!/usr/bin/env python3
"""Archive reference runs or verify an immutable evidence snapshot (never an oracle update)."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def source_hashes():
    sources = [ROOT / "scripts/reference.py", ROOT / "validation/reference/Dockerfile",
               ROOT / "validation/reference/run.sh",
               *sorted((ROOT / "validation/reference/src").rglob("*.java")),
               *sorted((ROOT / "validation/reference/tests").glob("*.java")),
               *sorted((ROOT / "validation/reference/tests").glob("*.py"))]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sources}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_artifacts(cache):
    reports = load(cache / "report.json")
    lines = [r["run_log"].strip() for r in reports]
    lines += (cache / "repeat-runs.txt").read_text(encoding="utf-8").splitlines()
    paths = []
    for index, line in enumerate(lines):
        marker = "Reference logs and request: "
        require(line.startswith(marker), "Invalid run log pointer")
        run = bounded(ROOT, line[len(marker):], ROOT / ".cache/minecraft-26.2/runs")
        names = ["request.json", "provenance.json", "server.log", "output/server.properties"]
        if index < len(reports):
            names.append("output/normalizer-tests.json")
        paths.extend(run / name for name in names)
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def bounded(base, name, boundary):
    path = (base / name).resolve()
    require(path.is_relative_to(boundary.resolve()), f"Path outside boundary: {name}")
    return path


def suite_passed(path):
    """Accept historical logs and the complete two-test pytest reference suite."""
    text = path.read_text(encoding="utf-8").strip()
    if text.endswith("OK"):
        return True
    last_line = text.splitlines()[-1] if text else ""
    return re.fullmatch(r"=+ 2 passed in [0-9.]+s(?: \(.*\))? =+", last_line) is not None


def verify(directory, source_ref=None, root=ROOT):
    directory = directory.resolve()
    manifest = load(directory / "manifest.json")
    files = {p.relative_to(directory).as_posix() for p in directory.rglob("*")
             if p.is_file() and p != directory / "manifest.json"}
    require(files == set(manifest), "Manifest file set differs (missing or extra artifact)")
    for name, expected in manifest.items():
        path = bounded(directory, name, directory)
        require(digest(path) == expected, f"Artifact hash mismatch: {name}")
    summary = load(directory / "summary.json")
    require(summary["suite"]["passed"] is True, "Suite did not pass")
    require(suite_passed(directory / summary["suite"]["log"]), "Suite log did not pass")
    require(bool(summary["cases"]), "No cases recorded")
    for case in summary["cases"]:
        actual = bounded(directory, case["actual"], directory)
        expected = bounded(directory, case["expected"], root)
        require(case["passed"] is True, f"Failed case: {case['name']}")
        require(digest(actual) == case["actual_sha256"], f"Actual hash mismatch: {actual}")
        require(digest(expected) == case["expected_sha256"], f"Oracle hash mismatch: {expected}")
        require(load(actual) == load(expected), f"Expected/actual differ: {case['name']}")
        require(len(load(actual)["rows"]) == case["rows"], "Row count mismatch")
        require(load(directory / case["name"] / "normalizer-tests.json")["passed"] is True,
                "Normalizer failed")
    repeat = summary["repeat_query"]
    require(repeat["passed"] is True, "Repeat query failed")
    for name, key in (("repeat-first.json", "first_sha256"), ("repeat-second.json", "second_sha256")):
        require(digest(directory / name) == repeat[key], f"Repeat hash mismatch: {name}")
    require(load(directory / "repeat-first.json") == load(directory / "repeat-second.json"),
            "Repeat queries differ")
    ref = source_ref or summary.get("source_ref")
    require(bool(ref), "Supply --source-ref for historical evidence without source_ref")
    for name, expected in summary["source_sha256"].items():
        bounded(root, name, root)
        if ref == "worktree":
            data = (root / name).read_bytes()
        else:
            data = subprocess.run(["git", "show", f"{ref}:{name}"], cwd=root,
                                  capture_output=True, check=True).stdout
        require(hashlib.sha256(data).hexdigest() == expected, f"Source hash mismatch: {name} at {ref}")
    return {"passed": True, "cases": len(summary["cases"]), "source_ref": ref,
            "meaning": "snapshot integrity only; not a current test or version verification"}


def archive(destination, suite_log, metadata, source_ref="worktree"):
    """Reuse the original archive layout, publishing only after all checks pass."""
    require(not destination.exists(), "Destination exists; choose a new snapshot directory")
    require(destination.resolve().is_relative_to((ROOT / "validation/reference/evidence").resolve()),
            "Destination must be under validation/reference/evidence")
    require(destination.resolve().parent == (ROOT / "validation/reference/evidence").resolve(),
            "Use a direct child of validation/reference/evidence")
    cache = ROOT / ".cache/reference-tests"
    reports = load(cache / "report.json")
    require(len(reports) == 3 and {r["case"] for r in reports} == {"seed-1", "seed-min", "seed-max"}
            and all(r["passed"] is True for r in reports), "Incomplete case report")
    receipt = load(cache / "suite-receipt.json")
    require(receipt["source_sha256"] == source_hashes(), "Sources changed since suite")
    if source_ref != "worktree":
        source_ref = subprocess.run(["git", "rev-parse", "--verify", source_ref + "^{commit}"],
                                    cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        for name, expected in receipt["source_sha256"].items():
            data = subprocess.run(["git", "show", f"{source_ref}:{name}"], cwd=ROOT,
                                  capture_output=True, check=True).stdout
            require(hashlib.sha256(data).hexdigest() == expected, f"Source hash mismatch at {source_ref}: {name}")
    require(receipt["run_sha256"] == run_artifacts(cache), "Run artifacts changed since suite")
    require(receipt["suite_sha256"] == digest(suite_log), "Suite log changed since suite")
    for name, expected in receipt["result_sha256"].items():
        require(digest(bounded(cache, name, cache)) == expected, f"Suite output changed: {name}")
    require(suite_passed(suite_log), "Suite log did not pass")
    summary = load(metadata)
    require("host" in summary and "runtime" in summary, "Metadata needs host and runtime")
    summary.update({"suite": {"passed": True, "log": "full-suite.log", "test_methods": 2},
                    "cases": [], "verification_status": "unverified", "core_comparison_cases_passed": 0,
                    "release_acceptance": "not_run", "source_ref": source_ref})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="archive-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "snapshot"
        staging.mkdir()

        def copy(source, target):
            target = staging / target
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")

        def run_path(line):
            marker = "Reference logs and request: "
            require(line.startswith(marker), "Invalid run log pointer")
            return bounded(ROOT, line[len(marker):], ROOT / ".cache/minecraft-26.2/runs")

        def copy_run(run, name, normalizer=False):
            for filename in ("request.json", "provenance.json", "server.log"):
                copy(run / filename, f"{name}/{filename}")
            copy(run / "output/server.properties", f"{name}/server.properties")
            if normalizer:
                copy(run / "output/normalizer-tests.json", f"{name}/normalizer-tests.json")

        for report in reports:
            name = report["case"]
            require(name in ("seed-1", "seed-min", "seed-max"), "Unknown case")
            run = run_path(report["run_log"].strip())
            copy_run(run, name, True)
            copy(cache / f"{name}.actual.json", f"{name}/actual.json")
            expected = ROOT / f"validation/reference/fixtures/{name}.expected.json"
            require(digest(expected) == report["expected_sha256"], "Oracle changed since suite")
            require(digest(staging / name / "actual.json") == report["actual_sha256"], "Actual changed since suite")
            summary["cases"].append({"name": name, "rows": len(load(expected)["rows"]),
                                      "passed": True, "actual": f"{name}/actual.json",
                                      "expected": f"../../fixtures/{name}.expected.json",
                                      "actual_sha256": report["actual_sha256"],
                                      "expected_sha256": report["expected_sha256"]})
        repeat_runs = (cache / "repeat-runs.txt").read_text(encoding="utf-8").splitlines()
        require(len(repeat_runs) == 2, "Expected two repeat runs")
        for index, line in enumerate(repeat_runs, 1):
            copy_run(run_path(line), f"repeat-{index}")
        for name in ("repeat-first", "repeat-second"):
            copy(cache / f"{name}.json", f"{name}.json")
        summary["repeat_query"] = {"passed": True, "first_sha256": digest(staging / "repeat-first.json"),
                                   "second_sha256": digest(staging / "repeat-second.json")}
        copy(suite_log, "full-suite.log")
        copy(cache / "suite-receipt.json", "suite-receipt.json")
        summary["source_sha256"] = receipt["source_sha256"]
        (staging / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
        manifest = {p.relative_to(staging).as_posix(): digest(p) for p in staging.rglob("*") if p.is_file()}
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
        # Relative fixture paths are interpreted at the final location.
        for case in summary["cases"]:
            require(load(staging / case["actual"]) == load(destination / case["expected"]), "Oracle differs")
        require(load(staging / "repeat-first.json") == load(staging / "repeat-second.json"), "Repeat differs")
        for case in summary["cases"]:
            require(load(staging / case["name"] / "normalizer-tests.json")["passed"] is True, "Normalizer failed")
        staging.rename(destination)
    return {"archived": str(destination), "source_ref": source_ref}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("verify")
    check.add_argument("directory", type=Path)
    check.add_argument("--source-ref", help="Git commit or worktree; old snapshot: 823e091")
    save = commands.add_parser("archive")
    save.add_argument("destination", type=Path)
    save.add_argument("--suite-log", required=True, type=Path)
    save.add_argument("--metadata", required=True, type=Path, help="JSON with actual host/runtime/date/timezone")
    save.add_argument("--source-ref", default="worktree", help="Pin matching source commit when archiving")
    args = parser.parse_args()
    try:
        result = (verify(args.directory, args.source_ref) if args.command == "verify" else
                  archive(args.destination, args.suite_log, args.metadata, args.source_ref))
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

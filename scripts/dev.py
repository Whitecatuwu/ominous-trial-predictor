#!/usr/bin/env python3
"""Repository checks and environment diagnostics; Python 3.11+, no host Java required."""
import argparse
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from evidence import digest, run_artifacts, source_hashes

ROOT = Path(__file__).resolve().parents[1]


def run(command, **kwargs):
    return subprocess.run(command, cwd=ROOT, check=True, **kwargs)


def doctor(integration=False, github=False):
    results = [{"name": "python", "ok": sys.version_info >= (3, 11),
                "detail": sys.version.split()[0], "required": True}]
    for name, required, command in (
        ("git", True, ["git", "--version"]),
        ("github_cli", github, ["gh", "--version"]),
        ("docker_linux", integration, ["docker", "info", "--format", "{{.OSType}}"]),
    ):
        executable = shutil.which(command[0])
        try:
            if not executable:
                raise OSError(f"{command[0]} missing from PATH")
            result = subprocess.run(command, capture_output=True, text=True, timeout=20)
            ok = result.returncode == 0 and (name != "docker_linux" or result.stdout.strip() == "linux")
            detail = (result.stdout if ok else result.stderr or result.stdout).strip()
        except (OSError, subprocess.SubprocessError) as error:
            ok, detail = False, str(error)
        results.append({"name": name, "ok": ok, "required": required, "detail": detail,
                        "remedy": {"git": "Install Git and add it to PATH.",
                                   "github_cli": "Install GitHub CLI or add its installation directory to PATH.",
                                   "docker_linux": "Start Docker Desktop, select Linux containers, and check pipe/log permissions."}[name]})
    print(json.dumps({"checks": results, "host_java_required": False}, indent=2))
    return 0 if all(r["ok"] for r in results if r["required"]) else 2


def check(integration=False, accept_eula=False):
    if integration and not accept_eula:
        raise ValueError("Integration requires reading https://aka.ms/MinecraftEULA and --accept-eula")
    # Parse tracked Python without emitting bytecode or starting Minecraft.
    files = run(["git", "ls-files", "-z", "--", "*.py"], capture_output=True).stdout.decode().split("\0")
    for name in filter(None, files):
        ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)
    tracked = run(["git", "ls-files", "-z"], capture_output=True).stdout.decode().split("\0")
    for name in filter(None, tracked):
        data = (ROOT / name).read_bytes()
        if b"\0" not in data:
            for number, line in enumerate(data.splitlines(), 1):
                if line.rstrip(b" \t") != line:
                    raise ValueError(f"Trailing whitespace: {name}:{number}")
    run(["git", "diff", "--check"])
    run(["git", "diff", "--cached", "--check"])
    run([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests", "-v"])
    run([sys.executable, "scripts/evidence.py", "verify",
         "validation/reference/evidence/2026-10-20", "--source-ref", "823e091"])
    if integration:
        if doctor(integration=True):
            return 2
        run([sys.executable, "scripts/reference.py", "prepare"])
        sources = source_hashes()
        cache = ROOT / ".cache/reference-tests"
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "suite-receipt.json").unlink(missing_ok=True)
        log = ROOT / ".cache/full-suite.log"
        with log.open("w", encoding="utf-8", newline="\n") as output:
            result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s",
                                     "validation/reference/tests", "-v"], cwd=ROOT,
                                    env={**os.environ, "REFERENCE_ACCEPT_EULA": "true"},
                                    stdout=output, stderr=subprocess.STDOUT)
        print(log.read_text(encoding="utf-8"))
        if result.returncode == 0:
            if source_hashes() != sources:
                raise ValueError("Sources changed during suite; rerun integration")
            outputs = ["report.json", "repeat-first.json", "repeat-second.json", "repeat-runs.txt",
                       "seed-1.actual.json", "seed-min.actual.json", "seed-max.actual.json"]
            receipt = {"source_sha256": sources, "suite_sha256": digest(log),
                       "run_sha256": run_artifacts(cache),
                       "result_sha256": {name: digest(cache / name) for name in outputs}}
            (cache / "suite-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        return result.returncode
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("doctor")
    inspect.add_argument("--integration", action="store_true", help="Require Docker Linux daemon")
    inspect.add_argument("--github", action="store_true", help="Require gh on PATH")
    checks = commands.add_parser("check")
    checks.add_argument("--integration", action="store_true")
    checks.add_argument("--accept-eula", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            return doctor(args.integration, args.github)
        return check(args.integration, args.accept_eula)
    except (OSError, ValueError, SyntaxError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

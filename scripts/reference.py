#!/usr/bin/env python3
"""Development-only, hash-locked Minecraft 26.2 Docker reference queries."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "version-data/26.2.json"
IMAGE = "ominous-trial-reference:26.2"
CACHE = ROOT / ".cache/minecraft-26.2"


def run(command, **kwargs):
    return subprocess.run(command, check=True, cwd=ROOT, **kwargs)


def prepare():
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    CACHE.mkdir(parents=True, exist_ok=True)
    jar = CACHE / "server.jar"
    if not jar.exists():
        temporary = jar.with_suffix(".download")
        urllib.request.urlretrieve(lock["server"]["url"], temporary)
        temporary.replace(jar)
    for algorithm in ("sha1", "sha256"):
        with jar.open("rb") as source:
            actual = hashlib.file_digest(source, algorithm).hexdigest()
        if actual != lock["server"][algorithm]:
            raise ValueError(f"Server JAR {algorithm} mismatch; remove {jar} and prepare again")
    run(["docker", "build", "--network=none", "-f", "validation/reference/Dockerfile",
         "-t", IMAGE, "."], stdout=sys.stderr)


def decimal(text, bits):
    if not re.fullmatch(r"[+-]?[0-9]+", text):
        raise argparse.ArgumentTypeError("Expected a signed decimal integer")
    value = int(text)
    if not -(2 ** (bits - 1)) <= value < 2 ** (bits - 1):
        raise argparse.ArgumentTypeError(f"Integer outside signed {bits}-bit range")
    return value


def query(args):
    if not args.accept_eula:
        raise ValueError("Read https://aka.ms/MinecraftEULA and pass --accept-eula if you agree")
    request = {"seed": str(args.seed), "positions": args.position,
               "normalizer_tests": args.normalizer_tests}
    run_dir = CACHE / "runs" / uuid.uuid4().hex
    output = run_dir / "output"
    output.mkdir(parents=True)
    request_path = run_dir / "request.json"
    request_path.write_text(json.dumps(request) + "\n", encoding="utf-8")
    provenance = json.loads(LOCK.read_text(encoding="utf-8"))
    provenance["image_id"] = run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
                                 capture_output=True, text=True).stdout.strip()
    image_hash = run(["docker", "image", "inspect", provenance["image_id"], "--format",
                      '{{index .Config.Labels "reference.server.sha256"}}'],
                     capture_output=True, text=True).stdout.strip()
    if image_hash != provenance["server"]["sha256"]:
        raise ValueError("Reference image does not match the source lock; run prepare")
    provenance["runtime"] = run(["docker", "version", "--format", "{{json .}}"],
                                capture_output=True, text=True).stdout.strip()
    (run_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    name = "trial-reference-" + run_dir.name
    command = ["docker", "run", "--rm", "--name", name, "--network", "none", "--hostname", "localhost",
               "--memory", "3g", "--cpus", "2", "-e", "REFERENCE_ACCEPT_EULA=true",
               "-e", "REFERENCE_SEED=" + str(args.seed),
               "--mount", f"type=bind,source={request_path},target=/request.json,readonly",
               "--mount", f"type=bind,source={output},target=/out", provenance["image_id"]]
    print(f"Reference logs and request: {run_dir}", file=sys.stderr)
    started = time.perf_counter()
    try:
        with (run_dir / "server.log").open("w", encoding="utf-8") as log:
            run(command, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=False)
        raise
    provenance["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    (run_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    result = output / "result.json"
    if not result.exists():
        raise ValueError(f"Reference query failed; see {run_dir / 'server.log'}")
    document = json.loads(result.read_text(encoding="utf-8"))
    print(json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare", help="Download locked official JAR and compile reference image")
    query_parser = commands.add_parser("query", help="Run original vanilla dispensing query offline in Docker")
    query_parser.add_argument("--seed", required=True, type=lambda text: decimal(text, 64))
    query_parser.add_argument("--position", action="append", required=True, nargs=3,
                              type=lambda text: decimal(text, 32), metavar=("X", "Y", "Z"))
    query_parser.add_argument("--accept-eula", action="store_true")
    query_parser.add_argument("--normalizer-tests", action="store_true",
                              help="Also run normalization tests against initialized vanilla registries")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare()
        else:
            query(args)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

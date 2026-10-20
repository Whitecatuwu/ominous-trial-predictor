#!/usr/bin/env python3
"""Cache full javap output, then display a bounded method excerpt."""
import argparse
import re
import subprocess
import sys

from reference import IMAGE, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("class_name")
    parser.add_argument("--method", required=True, help="Exact Java method name")
    parser.add_argument("--max-lines", type=int, default=80)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    try:
        if not re.fullmatch(r"[\w.$]+", args.class_name) or not re.fullmatch(r"[\w$]+", args.method):
            raise ValueError("Expected Java class and method names")
        if args.max_lines < 1:
            raise ValueError("--max-lines must be positive")
        image_id = subprocess.run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
                                  capture_output=True, text=True, check=True).stdout.strip()
        cache = ROOT / ".cache/javap" / image_id.replace(":", "-")
        cache.mkdir(parents=True, exist_ok=True)
        path = cache / (args.class_name + ".txt")
        if args.refresh or not path.exists():
            result = subprocess.run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "javap",
                                     image_id, "-p", "-c", "-classpath",
                                     "/opt/reference/META-INF/versions/26.2/server-26.2.jar", args.class_name],
                                    capture_output=True, text=True, check=True)
            path.write_text(result.stdout, encoding="utf-8", newline="\n")
        lines = path.read_text(encoding="utf-8").splitlines()
        selected = []
        active = False
        for index, line in enumerate(lines, 1):
            if re.match(r"^  \S", line):
                active = bool(re.search(r"\b" + re.escape(args.method) + r"\(", line))
            if active:
                selected.append(f"{index}: {line}")
        if not selected:
            raise ValueError(f"Method not found; full output: {path}")
        print("\n".join(selected[:args.max_lines]))
        print(f"Full output: {path}; method lines: {len(selected)}; shown: {min(len(selected), args.max_lines)}",
              file=sys.stderr)
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

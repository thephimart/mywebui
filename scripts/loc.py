#!/usr/bin/env python3
from collections import defaultdict
from pathlib import Path

SRC = Path("src")

EXCLUDE_DIRS = {
    ".venv",
    "__pycache__",
    ".egg-info",
}

MAX_DEPTH = 3  # relative to src/


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def count_lines(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def src_breakdown_limited_depth(src: Path, max_depth: int):
    total = 0
    per_bucket = defaultdict(int)

    for file in src.rglob("*.py"):
        if is_excluded(file):
            continue

        lines = count_lines(file)
        total += lines

        rel = file.relative_to(src)

        # directory depth (ignore filename)
        dir_parts = rel.parts[:-1]

        if not dir_parts:
            bucket = "."
        else:
            bucket = "/".join(dir_parts[:max_depth])

        per_bucket[bucket] += lines

    return total, dict(sorted(per_bucket.items()))


def report(title, total):
    print(f"{title:<35} {total:>6} LOC")


def main():
    print()

    total, breakdown = src_breakdown_limited_depth(SRC, MAX_DEPTH)

    report("src/ only (runtime)", total)
    print(f"  Breakdown (depth ≤ {MAX_DEPTH}):")
    for path, loc in breakdown.items():
        print(f"    {path:<30} {loc:>6} LOC")

    print()


if __name__ == "__main__":
    main()

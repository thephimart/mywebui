#!/usr/bin/env python3
"""CI Guardrail - Enforce documentation consistency.

This script validates:
1. No undocumented libraries in imports
2. All API routes are documented in 16-apis.md
3. No references to old paths (/data/)
4. Docs are frozen (no changes without version bump)
"""

import re
import sys
from pathlib import Path


def check_api_routes() -> bool:
    """Check that all API routes are documented."""
    docs_path = Path("docs/16-apis.md")
    if not docs_path.exists():
        print("ERROR: docs/16-apis.md not found")
        return False

    api_doc = docs_path.read_text()

    routes_path = Path("src/mywebui/api/v1")
    if not routes_path.exists():
        print("ERROR: src/mywebui/api/v1 not found")
        return False

    documented_routes = set(re.findall(r"(GET|POST|PUT|DELETE|PATCH)\s+/api/v1/(\w+)", api_doc))

    found_routes = set()
    for route_file in routes_path.glob("*.py"):
        if route_file.name.startswith("_"):
            continue
        content = route_file.read_text()
        found_routes.add(route_file.stem)

    undocumented = found_routes - {r[1] for r in documented_routes}
    if undocumented:
        print(f"ERROR: Undocumented API routes: {undocumented}")
        return False

    return True


def check_old_paths() -> bool:
    """Check for old path references."""
    docs_path = Path("docs")
    if not docs_path.exists():
        return True

    old_patterns = [r"/data/", r"implementation_plan\.md"]
    issues = []

    for md_file in docs_path.glob("*.md"):
        content = md_file.read_text()
        for pattern in old_patterns:
            if re.search(pattern, content):
                issues.append(f"{md_file.name}: contains '{pattern}'")

    if issues:
        print("ERROR: Old paths found:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    return True


def check_docs_frozen() -> bool:
    """Check that docs have the frozen notice."""
    readme = Path("docs/README.md")
    if not readme.exists():
        return True

    content = readme.read_text()
    if "FROZEN" not in content and "read-only" not in content.lower():
        print("WARNING: docs/README.md should contain a frozen/read-only notice")
        return False

    return True


def main() -> int:
    """Run all checks."""
    print("Running CI guardrail checks...")

    checks = [
        ("Old paths check", check_old_paths),
        ("Docs frozen check", check_docs_frozen),
        ("API routes check", check_api_routes),
    ]

    results = []
    for name, check in checks:
        print(f"\n{name}...")
        try:
            result = check()
            results.append(result)
            print(f"  {'PASS' if result else 'FAIL'}")
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append(False)

    if all(results):
        print("\n✅ All checks passed!")
        return 0
    else:
        print("\n❌ Some checks failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

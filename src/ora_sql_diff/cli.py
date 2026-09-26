from __future__ import annotations

import argparse
import json
from pathlib import Path
from .core import compare_sql


def main(argv=None):
    p = argparse.ArgumentParser(description="Structural diff for Oracle SQL.")
    p.add_argument("before")
    p.add_argument("after")
    p.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args(argv)

    before = Path(a.before).read_text(encoding="utf-8")
    after = Path(a.after).read_text(encoding="utf-8")
    result = compare_sql(before, after)

    if a.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if not result.changes:
            print("No supported structural changes detected.")
        else:
            for change in result.changes:
                suffix = f": {change.detail}" if change.detail else ""
                print(f"{change.kind}{suffix}")

    return 1 if result.changed else 0


if __name__ == "__main__":
    raise SystemExit(main())

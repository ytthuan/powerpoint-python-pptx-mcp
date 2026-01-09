#!/usr/bin/env python3
"""Replace Vietnamese pronoun 'em' with 'mình' in PPTX notes JSON dumps.

- Replaces only standalone word occurrences (word boundary), so it won't touch words like 'template'.
- Preserves casing: 'Em' -> 'Mình', 'em' -> 'mình'.

Input format: the JSON produced by scripts/pptx_notes.py dump
Output format: {"slides": [{"slide": <int>, "notes": <str>}, ...]}
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", required=True, type=Path)
    parser.add_argument("--out", dest="out_path", required=True, type=Path)
    args = parser.parse_args()

    data = json.loads(args.in_path.read_text(encoding="utf-8"))

    pattern = re.compile(r"\bem\b", flags=re.IGNORECASE)

    def repl(match: re.Match[str]) -> str:
        s = match.group(0)
        return "Mình" if s[:1].isupper() else "mình"

    updates = []
    total_hits = 0

    for item in data.get("slides", []):
        slide_no = int(item.get("slide"))
        notes = item.get("notes") or ""

        hits = len(list(pattern.finditer(notes)))
        total_hits += hits

        new_notes = pattern.sub(repl, notes)
        if new_notes != notes:
            updates.append({"slide": slide_no, "notes": new_notes})

    args.out_path.write_text(
        json.dumps({"slides": updates}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Standalone 'em' matches found: {total_hits}")
    print(f"Slides changed: {len(updates)}")
    print(f"Wrote updates: {args.out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

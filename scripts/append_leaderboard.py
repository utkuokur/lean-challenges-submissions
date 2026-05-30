#!/usr/bin/env python3
"""Append a single entry to site-data/leaderboard.json.

Schema matches what the React app at automated_compile/src/App.tsx reads:

    { "entries": [
        { "rank": int,
          "nickname": str,
          "name": str,             # may be ""
          "problem": str,          # e.g. "challenge_1" or "challenge_1_univ"
          "claim": str,            # "prove" | "disprove"
          "parameter": str,        # e.g. "5" or "universal"
          "date": str,             # ISO-8601 UTC, second precision
          "issue": int,            # issue number on the submissions repo
          "source_url": str },     # the URL the proof was fetched from
        ... ] }

Rank is assigned as `len(existing_entries) + 1` — i.e. monotonically
increasing in submission order. The React app re-sorts for display.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--leaderboard", required=True,
                   help="path to leaderboard.json")
    p.add_argument("--nickname", required=True)
    p.add_argument("--name", default="")
    p.add_argument("--problem", required=True)
    p.add_argument("--claim", required=True)
    p.add_argument("--parameter", required=True)
    p.add_argument("--issue", required=True, type=int)
    p.add_argument("--source-url", required=True)
    args = p.parse_args()

    path = pathlib.Path(args.leaderboard)
    if path.exists() and path.stat().st_size > 0:
        data = json.loads(path.read_text(encoding="utf-8"))
        if "entries" not in data or not isinstance(data["entries"], list):
            sys.exit(f"{path}: malformed leaderboard, missing entries[]")
    else:
        data = {"entries": []}
        path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "rank": len(data["entries"]) + 1,
        "nickname": args.nickname,
        "name": args.name,
        "problem": args.problem,
        "claim": args.claim,
        "parameter": args.parameter,
        "date": dt.datetime.now(tz=dt.timezone.utc)
                  .replace(microsecond=0).isoformat()
                  .replace("+00:00", "Z"),
        "issue": args.issue,
        "source_url": args.source_url,
    }
    data["entries"].append(entry)

    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Appended entry #{entry['rank']} to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Download monthly FRED price indexes into data/raw/.

Series (Jan 2023 to the latest month FRED has):
  WPU066           PPI: plastic resins and materials   -> data/raw/fred_WPU066.csv
  PCU322211322211  PPI: corrugated and solid fiber box -> data/raw/fred_PCU322211322211.csv
  CPIAUCSL         CPI: all urban consumers            -> data/raw/fred_CPIAUCSL.csv

Files are saved exactly as FRED returns them, after a basic sanity check.
Like generate_data.py, this refuses to overwrite existing files unless --force is given.
Cite each series as listed in source-index.md.

Usage:
  python3 scripts/download_fred.py
  python3 scripts/download_fred.py --force
"""

import argparse
import csv
import io
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd={start}"
START = "2023-01-01"
SERIES = ["WPU066", "PCU322211322211", "CPIAUCSL"]
# Python's default User-Agent is used on purpose: on 2026-11-18 FRED's CSV endpoint hung on
# requests with a custom User-Agent ("prairie-play-planner/1.0") but answered the default.


def target(root, series):
    return root / "data" / "raw" / "fred_{}.csv".format(series)


def fetch(series):
    req = urllib.request.Request(URL.format(series=series, start=START))
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def validate(series, body):
    """Return (n_rows, first_date, last_date); raise ValueError if the CSV looks wrong."""
    rows = list(csv.reader(io.StringIO(body.decode("utf-8"))))
    if len(rows) < 2 or len(rows[0]) != 2 or rows[0][1] != series:
        raise ValueError("{}: unexpected header {!r}".format(series, rows[0] if rows else None))
    data = [r for r in rows[1:] if r]
    dates = [r[0] for r in data]
    if dates[0] != START:
        raise ValueError("{}: first date is {}, expected {}".format(series, dates[0], START))
    if any(not d.endswith("-01") for d in dates):
        raise ValueError("{}: dates are not monthly".format(series))
    return len(data), dates[0], dates[-1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT, help="root to write under (default: repo root)")
    args = ap.parse_args()
    root = args.out_dir.resolve()

    existing = [target(root, s) for s in SERIES if target(root, s).exists()]
    if existing and not args.force:
        print("Refusing to overwrite {} existing file(s):".format(len(existing)))
        for p in existing:
            print("  " + str(p.relative_to(root)))
        print("data/raw/ is read-only by project rule. Use --force only if you mean to re-download.")
        return 1

    # Download and check everything first, so a failure leaves no partial set.
    bodies = {}
    for s in SERIES:
        body = fetch(s)
        n, first, last = validate(s, body)
        bodies[s] = body
        print("{:<16} {:>3} months  {} to {}".format(s, n, first, last))

    for s, body in bodies.items():
        path = target(root, s)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        print("wrote " + str(path.relative_to(root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

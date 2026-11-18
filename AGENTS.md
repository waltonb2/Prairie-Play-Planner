# Prairie Play Planner

Production planner for **Prairie Play Toys**, a fictional toy maker with 4 toy lines.

A `/plan-quarter` workflow will read order data plus FRED price indexes (plastic resin,
cardboard boxes, CPI) and recommend quarterly production quantities for each toy line
that maximize expected profit.

## Layout
- `data/raw/` — source data as downloaded (read-only); order history Jan 2023 – Dec 2025
- `data/incoming/` — newer order files (Jan – Oct 2026), same format
- `scripts/` — `generate_data.py` makes the synthetic data (seed 42)
- `checks/` — validation and sanity checks (`check_generated_data.py`)
- `work/` — intermediate files and the session context log (`work/context-log.md`)
- `output/` — final recommendations and reports
- `source-index.md` — where each data source came from and its terms
- `decisions.md` — dated log of project decisions

## Rules
- **Never edit files in `data/raw/`.** Treat raw data as read-only; write any cleaned or derived data to `work/` or `output/`.
  The one exception: `scripts/generate_data.py` creates `data/raw/`, and it refuses to overwrite without `--force`.
- `work/generated_mess_log.csv` is the answer key for injected data problems. Use it only in checks, never in cleaning or planning code.

# Context Log

## 2026-11-18 — Project setup
Created the project folder layout: AGENTS.md (project summary and the rule never to edit
`data/raw/`), CLAUDE.md (imports AGENTS.md), source-index.md (empty source table),
decisions.md (first entry), this log, a .gitignore (.env files, .DS_Store), and empty
`data/raw/`, `checks/`, `work/`, `output/` folders with .gitkeep files. No data downloaded
and no analysis code written yet.

## 2026-11-18 — Input format recorded
Moved the order input format decision into a file: `decisions.md` now has the order CSV
spec (monthly `orders_YYYY-MM.csv` in `data/raw/`, the 7 columns, the 4 toy lines, and that
prices and costs live in `toy_lines.csv`), with 3 example rows. No code written yet.

## 2026-11-18 — Synthetic data generated
Planned the data generator, revised the plan after 5 user overrides (recorded in
`decisions.md`), then wrote `scripts/generate_data.py` and `checks/check_generated_data.py`.
Generated 3 config files, 36 order files in `data/raw/`, 10 in `data/incoming/` (7,246 rows;
4.7% cancelled; 213 messy rows logged in `work/generated_mess_log.csv`). All 30 checks pass,
including the byte-identical regeneration check. Shared capacity is 21,600 per quarter; all
three Q4s (2023–25) fall short. Next: download FRED indexes.

## 2026-11-18 — FRED data downloaded
Checked the FRED series pages and found the tentative resin ID WPU0661 doesn't exist (404). The
user confirmed WPU066. Added FRED's suggested citations to `source-index.md` and logged the
series check in `decisions.md`. Fixed the ID in `scripts/generate_data.py` and regenerated with
`--force`: `git diff` showed only `data/raw/material_prices.csv` changed, and all 30 checks
still pass. Wrote `scripts/download_fred.py` and downloaded WPU066, PCU322211322211 and
CPIAUCSL to `data/raw/fred_*.csv` (46 months each, Jan 2023 – Oct 2026, no missing values).
The script refuses to overwrite without `--force` (tested). Gotcha: FRED's CSV endpoint hung on a
custom User-Agent header but accepts Python's default, so the script sends no custom header.

## 2026-11-18 — Context reading
`/context` showed 114.5k / 1M tokens (11%), with messages at 83.7k. Screenshot:
`work/evidence/2026-11-18-context.png`.

## 2026-11-18 — Handoff to a fresh session
Natural checkpoint: all input data is generated, downloaded, checked and pushed. Wrote
`work/handoff.md` (what's built, next steps, open questions). The next session starts fresh with
the `/plan-quarter` workflow design and the Milestone 2 rough design.

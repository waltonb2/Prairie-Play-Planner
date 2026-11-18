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

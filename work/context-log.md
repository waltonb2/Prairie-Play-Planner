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

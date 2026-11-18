# Prairie Play Planner

Production planner for **Prairie Play Toys**, a fictional toy maker with 4 toy lines.

A `/plan-quarter` workflow will read order data plus FRED price indexes (plastic resin,
cardboard boxes, CPI) and recommend quarterly production quantities for each toy line
that maximize expected profit.

## Layout
- `data/raw/` — source data as downloaded (read-only)
- `checks/` — validation and sanity checks
- `work/` — intermediate files and the session context log (`work/context-log.md`)
- `output/` — final recommendations and reports
- `source-index.md` — where each data source came from and its terms
- `decisions.md` — dated log of project decisions

## Rules
- **Never edit files in `data/raw/`.** Treat raw data as read-only; write any cleaned or derived data to `work/` or `output/`.

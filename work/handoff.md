# Handoff — 2026-11-18

Read `AGENTS.md`, `decisions.md` and `work/context-log.md` first. The user reviews a plan before
any code is written, wants their changes to a plan logged in `decisions.md` as overrides, and
expects to be asked before every push.

## Built so far
- **Synthetic data** (`scripts/generate_data.py`, seed 42; reproducible byte for byte):
  - Orders: Jan 2023 – Dec 2025 in `data/raw/`, Jan – Oct 2026 in `data/incoming/`. 7,246 rows,
    4.7% cancelled, 213 messy rows (3%). The answer key is `work/generated_mess_log.csv`; use it
    in checks only.
  - `data/raw/toy_lines.csv` (wholesale price, discount < unit cost, material kg, other cost, storage),
    `material_prices.csv` (Jan 2023 base $/kg), `factory.csv` (shared 21,600 units/quarter).
- **FRED indexes** (`scripts/download_fred.py`): WPU066 (resin), PCU322211322211 (cardboard),
  CPIAUCSL (CPI, seasonally adjusted), 46 months each through Oct 2026, in `data/raw/fred_*.csv`.
  The user hand-checked the resin and cardboard files against FRED; both matched.
- **Checks**: `python3 checks/check_generated_data.py` (30 checks, all pass).
- **Cost rule**: dollar cost = base price × (index at t ÷ index at Jan 2023). CPI scales other
  cost and storage.
- Both scripts are the only writers of `data/raw/` and refuse to overwrite without `--force`.

## Next
1. Design the `/plan-quarter` workflow: the steps from raw files to a recommendation, and what
   each step reads and writes.
2. Write the Milestone 2 rough design (a plan first, no code until approved).

## Open questions
- **Which quarter to plan?** Data runs to Oct 2026. Is the target Q4 2026 (one month in) or Q1 2027?
- **Leftovers:** at quarter end, are they sold at the discount price, or stored to the next quarter
  at the storage cost? Or should the planner choose between the two?
- **Cleaning rules:** drop duplicates by `order_id`? Assign late orders by `order_date`, not by
  file? Drop rows with a missing, negative or extreme quantity, or flag them? Fix misspelled toy
  names by mapping them back?
- **Demand vs sales:** past Q4 orders exceed capacity. Do we treat orders as true demand
  (uncensored)? The generator does.
- **Forecast method:** seasonal average with a trend? How do we treat the Galaxy Rangers 2025
  hit (a one-off or a new level)? How do we express demand uncertainty for expected profit?
- **Cost outlook:** use the latest index month as-is, or project indexes forward to the planned quarter?
- **Role of `data/incoming/`:** holdout for testing forecasts, or new data to plan with?
- `fred_CPIAUCSL.csv` has not been hand-checked.

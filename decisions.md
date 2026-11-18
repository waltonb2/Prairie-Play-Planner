# Decisions

## 2026-11-18
Project set up; chose toy company problem.

## 2026-11-18 — Order file format
Order data arrives as one CSV per month in `data/raw/`, named `orders_YYYY-MM.csv`
(e.g. `orders_2026-10.csv`).

| Column | Format / allowed values |
|--------|-------------------------|
| `order_id` | Unique order identifier |
| `order_date` | Date, `YYYY-MM-DD` |
| `toy_line` | One of: `Turbo Trucks`, `Block Builders`, `Splash Squad`, `Galaxy Rangers` |
| `customer` | Customer name |
| `channel` | `retail` or `online` |
| `quantity` | Units ordered |
| `status` | `confirmed` or `cancelled` |

Prices and costs are not in the order files. They live separately in `toy_lines.csv`.

Example rows:

```csv
order_id,order_date,toy_line,customer,channel,quantity,status
ORD-1001,2026-10-03,Turbo Trucks,Maple Street Toys,retail,120,confirmed
ORD-1002,2026-10-07,Galaxy Rangers,Online Direct,online,35,confirmed
ORD-1003,2026-10-15,Splash Squad,Lakeside Kids Co,retail,80,cancelled
```

## 2026-11-18 — Synthetic data generator
Data is synthetic, made by `scripts/generate_data.py` with fixed seed 42 (byte-identical on
every run). It is the only writer of `data/raw/` and refuses to overwrite existing files
without `--force`. `checks/check_generated_data.py` verifies the output.

- Orders: Jan 2023 – Dec 2025 in `data/raw/`; Jan – Oct 2026 in a new `data/incoming/`
  folder (data that "arrives later", kept apart from the history).
- About 5% of orders cancelled. About 3% of rows have one problem: a duplicate row, a missing
  quantity, a misspelled toy line, a negative or extreme quantity, or a late order filed in the
  next month's file. The answer key is `work/generated_mess_log.csv`; cleaning code must not
  read it.
- Patterns: Turbo Trucks steady with a ~15% Q4 bump; Block Builders +10% a year with an Oct–Dec
  peak; Splash Squad peaks Apr–Sep; Galaxy Rangers has a big Q4 peak plus a surprise hit that
  ramps up from Jul 2025 (×2.5 by Q4 2025) and fades through 2026.
- Order files keep the column format above. Per-line economics are in `data/raw/toy_lines.csv`,
  material base prices in `data/raw/material_prices.csv`, and factory capacity in
  `data/raw/factory.csv`.

## 2026-11-18 — Cost rule: indexes to dollars
FRED gives price indexes, not dollars. `data/raw/material_prices.csv` holds a base price per kg
for resin ($1.50) and cardboard ($0.90) as of Jan 2023. The rule:

**dollar cost in month t = base price per kg × (index at t ÷ index at Jan 2023)**

CPI scales `other_unit_cost` and storage cost the same way. FRED series IDs (resin WPU0661,
cardboard PCU322211322211, CPI CPIAUCSL) are tentative until the data is downloaded.

## 2026-11-18 — Overrides of the first generator plan
After reviewing the first plan, we changed five things:
1. **Discount price is below each toy's total unit cost**, so leftover toys lose money. `price`
   is the average wholesale selling price (not retail). Prices were lowered to wholesale levels.
2. **Base prices per kg for resin and cardboard added** (Jan 2023), with the index-scaling cost
   rule above. The first plan had physical amounts only.
3. **One shared factory capacity per quarter** (21,600 units across all 4 lines) replaces
   per-line capacity. It covers an average quarter (2023–25 mean is about 20,200 confirmed
   units) but falls short in every Q4 (about 22,300–33,900).
4. **Galaxy Rangers hit ramps up from Jul 2025** (Jul ×1.3, Aug ×1.7, Sep ×2.2, Oct–Dec ×2.5)
   instead of lasting all of 2025.
5. **Verification is a saved script**, `checks/check_generated_data.py`, instead of a one-off
   command.

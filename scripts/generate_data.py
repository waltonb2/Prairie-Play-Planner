"""Generate synthetic data for Prairie Play Toys.

Creates (relative to --out-dir, default: repo root):
  data/raw/toy_lines.csv            price, discount and cost inputs per toy line
  data/raw/material_prices.csv      Jan 2023 base $/kg for resin and cardboard
  data/raw/factory.csv              shared factory capacity per quarter
  data/raw/orders_YYYY-MM.csv       Jan 2023 - Dec 2025
  data/incoming/orders_YYYY-MM.csv  Jan 2026 - Oct 2026
  work/generated_mess_log.csv       answer key for the injected data problems

Fixed seed (42): every run produces byte-identical files.

This script is the only thing allowed to write data/raw/, and only to create it.
It refuses to overwrite existing files unless --force is given.

Usage:
  python3 scripts/generate_data.py
  python3 scripts/generate_data.py --out-dir /tmp/somewhere
  python3 scripts/generate_data.py --force
"""

import argparse
import csv
import random
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

SEED = 42
REPO_ROOT = Path(__file__).resolve().parent.parent

# --- Fixed economics ---------------------------------------------------------

# price = average wholesale selling price; discount_price = price for leftovers.
TOY_LINES = [
    # toy_line, price, discount, resin_kg, cardboard_kg, other_cost, storage/qtr
    ("Turbo Trucks", 14.00, 5.00, 0.40, 0.15, 6.00, 0.40),
    ("Block Builders", 20.00, 6.50, 0.60, 0.25, 8.00, 0.60),
    ("Splash Squad", 11.00, 3.50, 0.30, 0.12, 4.50, 0.35),
    ("Galaxy Rangers", 17.00, 5.50, 0.35, 0.18, 7.00, 0.50),
]
TOY_LINE_COLUMNS = [
    "toy_line", "price", "discount_price", "resin_kg_per_unit",
    "cardboard_kg_per_unit", "other_unit_cost", "storage_cost_per_unit_per_quarter",
]

# Base prices as of Jan 2023. Dollar cost in month t =
# base_price_per_kg * (index at t / index at Jan 2023).
# FRED series pages checked 2026-11-18 (see decisions.md).
MATERIALS = [
    ("resin", 1.50, "2023-01", "WPU066"),
    ("cardboard", 0.90, "2023-01", "PCU322211322211"),
]
MATERIAL_COLUMNS = ["material", "base_price_per_kg", "base_month", "fred_series"]

# One factory shared by all 4 lines. Covers an average quarter, short in Q4 peaks.
CAPACITY_PER_QUARTER = 21600
FACTORY_COLUMNS = ["capacity_units_per_quarter"]

# --- Orders -------------------------------------------------------------------

ORDER_COLUMNS = [
    "order_id", "order_date", "toy_line", "customer", "channel", "quantity", "status",
]
RETAIL_CUSTOMERS = [
    "Maple Street Toys", "Lakeside Kids Co", "Prairie Wind Mercantile", "Big Sky Toy Barn",
    "Cottonwood General", "Redbud Family Store", "Harvest Moon Gifts", "Bluestem Books & Toys",
    "Sunflower Supply", "Riverbend Variety", "Meadowlark Market", "Tumbleweed Toys",
]
ONLINE_CUSTOMERS = [
    "Online Direct", "ShopNest", "ParcelPal", "ToyCart Online",
    "KidsBox Club", "ClickToys", "GiftGrid", "CartWheel Web",
]
P_ONLINE = 0.70
RETAIL_QTY = (10, 250)
ONLINE_QTY = (1, 25)
P_CANCELLED = 0.05
P_MESS = 0.03

MISSPELLINGS = {
    "Turbo Trucks": ["Turbo Truks", "turbo trucks", "Turbo Trucks "],
    "Block Builders": ["Block Builder", "block builders", "Blok Builders"],
    "Splash Squad": ["Splash Squad ", "Splash Sqaud", "splash squad"],
    "Galaxy Rangers": ["Galaxy Rangrs", "Galaxy Ranger", "galaxy rangers"],
}
MESS_TYPES = ["duplicate", "missing_quantity", "misspelled_toy_line", "bad_quantity", "late_order"]

FIRST_MONTH = (2023, 1)
LAST_RAW_MONTH = (2025, 12)
LAST_MONTH = (2026, 10)


def months():
    y, m = FIRST_MONTH
    while (y, m) <= LAST_MONTH:
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def next_month(y, m):
    return (y + 1, 1) if m == 12 else (y, m + 1)


def days_in_month(y, m):
    ny, nm = next_month(y, m)
    return (date(ny, nm, 1) - date(y, m, 1)).days


def order_file(y, m):
    folder = "raw" if (y, m) <= LAST_RAW_MONTH else "incoming"
    return "data/{}/orders_{:04d}-{:02d}.csv".format(folder, y, m)


def galaxy_hit(y, m):
    """Surprise-hit multiplier: ramps up from Jul 2025, fades through 2026."""
    if y == 2025:
        return {7: 1.3, 8: 1.7, 9: 2.2, 10: 2.5, 11: 2.5, 12: 2.5}.get(m, 1.0)
    if y == 2026:
        return 2.0 - (m - 1) * (0.7 / 9)  # 2.0 in Jan -> 1.3 in Oct
    return 1.0


def expected_demand(line, y, m):
    t = (y - 2023) * 12 + (m - 1)  # months since Jan 2023
    if line == "Turbo Trucks":
        return 2000 * (1.15 if m >= 10 else 1.0)
    if line == "Block Builders":
        season = {10: 1.4, 11: 1.7, 12: 1.7}.get(m, 1.0)
        return 1500 * 1.10 ** (t / 12) * season
    if line == "Splash Squad":
        if 4 <= m <= 9:
            season = 1.7
        elif m in (11, 12, 1, 2):
            season = 0.5
        else:
            season = 1.0
        return 1200 * season
    if line == "Galaxy Rangers":
        return 1000 * (2.2 if m >= 10 else 1.0) * galaxy_hit(y, m)
    raise ValueError(line)


def make_clean_orders(rng):
    """Return clean orders (without ids), sorted by date, for every month."""
    orders = []
    for y, m in months():
        for line, *_ in TOY_LINES:
            remaining = int(round(expected_demand(line, y, m) * rng.uniform(0.9, 1.1)))
            while remaining > 0:
                if rng.random() < P_ONLINE:
                    channel, customer = "online", rng.choice(ONLINE_CUSTOMERS)
                    qty = rng.randint(*ONLINE_QTY)
                else:
                    channel, customer = "retail", rng.choice(RETAIL_CUSTOMERS)
                    qty = rng.randint(*RETAIL_QTY)
                qty = min(qty, remaining)
                remaining -= qty
                orders.append({
                    "order_date": date(y, m, rng.randint(1, days_in_month(y, m))),
                    "toy_line": line,
                    "customer": customer,
                    "channel": channel,
                    "quantity": qty,
                    "status": "cancelled" if rng.random() < P_CANCELLED else "confirmed",
                })
    orders.sort(key=lambda o: (o["order_date"], o["toy_line"], o["customer"]))
    for i, o in enumerate(orders, start=1):
        o["order_id"] = "ORD-{:06d}".format(i)
    return orders


def add_mess(rng, orders):
    """Inject ~3% problems. Returns {file: [rows]} and the mess log."""
    files = defaultdict(list)
    log = []
    for o in orders:
        y, m = o["order_date"].year, o["order_date"].month
        target = order_file(y, m)
        row = dict(o)
        row["order_date"] = o["order_date"].isoformat()
        if rng.random() >= P_MESS:
            files[target].append(row)
            continue
        choices = MESS_TYPES if (y, m) < LAST_MONTH else MESS_TYPES[:-1]
        issue = rng.choice(choices)
        detail = ""
        if issue == "duplicate":
            files[target].extend([row, dict(row)])
        elif issue == "missing_quantity":
            row["quantity"] = ""
            files[target].append(row)
        elif issue == "misspelled_toy_line":
            row["toy_line"] = rng.choice(MISSPELLINGS[row["toy_line"]])
            detail = repr(row["toy_line"])
            files[target].append(row)
        elif issue == "bad_quantity":
            if rng.random() < 0.5:
                row["quantity"] = -rng.randint(1, 50)
            else:
                row["quantity"] = rng.randint(50000, 99999)
            detail = str(row["quantity"])
            files[target].append(row)
        elif issue == "late_order":
            target = order_file(*next_month(y, m))
            detail = "dated {}".format(row["order_date"])
            files["__late__" + target].append(row)  # appended after the month's rows
        log.append({"order_id": row["order_id"], "file": target, "issue": issue, "detail": detail})

    out = {}
    for y, m in months():
        f = order_file(y, m)
        out[f] = files.get(f, []) + files.get("__late__" + f, [])
    return out, log


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r[c] for c in columns})


def unit_cost_at_base(line_row):
    _, _, _, resin_kg, card_kg, other, _ = line_row
    prices = {name: p for name, p, _, _ in MATERIALS}
    return resin_kg * prices["resin"] + card_kg * prices["cardboard"] + other


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT, help="root to write under (default: repo root)")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    ap.add_argument("--quiet", action="store_true", help="no summary output")
    args = ap.parse_args()
    root = args.out_dir.resolve()

    for row in TOY_LINES:
        cost = unit_cost_at_base(row)
        assert row[2] < cost < row[1], "{}: need discount < unit cost < price".format(row[0])

    targets = ["data/raw/toy_lines.csv", "data/raw/material_prices.csv", "data/raw/factory.csv",
               "work/generated_mess_log.csv"] + [order_file(y, m) for y, m in months()]
    existing = [t for t in targets if (root / t).exists()]
    if existing and not args.force:
        print("Refusing to overwrite {} existing file(s) under {}:".format(len(existing), root))
        for t in existing[:10]:
            print("  " + t)
        if len(existing) > 10:
            print("  ...")
        print("data/raw/ is read-only by project rule. Use --force only if you mean to regenerate.")
        return 1

    rng = random.Random(SEED)
    orders = make_clean_orders(rng)
    files, log = add_mess(rng, orders)

    write_csv(root / "data/raw/toy_lines.csv", TOY_LINE_COLUMNS,
              [dict(zip(TOY_LINE_COLUMNS, r)) for r in TOY_LINES])
    write_csv(root / "data/raw/material_prices.csv", MATERIAL_COLUMNS,
              [dict(zip(MATERIAL_COLUMNS, r)) for r in MATERIALS])
    write_csv(root / "data/raw/factory.csv", FACTORY_COLUMNS,
              [{"capacity_units_per_quarter": CAPACITY_PER_QUARTER}])
    for f, rows in files.items():
        write_csv(root / f, ORDER_COLUMNS, rows)
    write_csv(root / "work/generated_mess_log.csv", ["order_id", "file", "issue", "detail"], log)

    if args.quiet:
        return 0

    print("Wrote {} order files, {} rows in total ({} clean orders before mess).".format(
        len(files), sum(len(r) for r in files.values()), len(orders)))
    sizes = [len(r) for r in files.values()]
    print("Rows per file: min {}, max {}, mean {:.0f}".format(min(sizes), max(sizes), sum(sizes) / len(sizes)))
    print("Cancelled: {:.1%}".format(sum(o["status"] == "cancelled" for o in orders) / len(orders)))
    print("Mess: {} rows ({:.1%})  {}".format(len(log), len(log) / len(orders),
                                              dict(Counter(e["issue"] for e in log))))
    print("\nConfirmed demand per quarter (all lines) vs capacity {:,}:".format(CAPACITY_PER_QUARTER))
    q = Counter()
    for o in orders:
        if o["status"] == "confirmed":
            q[(o["order_date"].year, (o["order_date"].month - 1) // 3 + 1)] += o["quantity"]
    for (y, qq), units in sorted(q.items()):
        flag = "SHORT" if units > CAPACITY_PER_QUARTER else ""
        print("  {} Q{}: {:>7,} {}".format(y, qq, units, flag))
    return 0


if __name__ == "__main__":
    sys.exit(main())

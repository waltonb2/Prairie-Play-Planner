"""Check the synthetic data made by scripts/generate_data.py.

Prints PASS/FAIL for each check and exits 1 if any fail. Read-only: it never
changes the data (the reproducibility check regenerates into a temp folder).

Usage:
  python3 checks/check_generated_data.py
  python3 checks/check_generated_data.py --root /path/to/generated/copy
"""

import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "scripts" / "generate_data.py"

TOY_LINES = ["Turbo Trucks", "Block Builders", "Splash Squad", "Galaxy Rangers"]
ORDER_COLUMNS = ["order_id", "order_date", "toy_line", "customer", "channel", "quantity", "status"]
TOY_LINE_COLUMNS = ["toy_line", "price", "discount_price", "resin_kg_per_unit", "cardboard_kg_per_unit",
                    "other_unit_cost", "storage_cost_per_unit_per_quarter"]
MESS_TYPES = {"duplicate", "missing_quantity", "misspelled_toy_line", "bad_quantity", "late_order"}

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print("{}  {}{}".format("PASS" if ok else "FAIL", name, "  ({})".format(detail) if detail else ""))


def expected_files():
    raw, incoming = [], []
    for y in range(2023, 2027):
        for m in range(1, 13):
            if y <= 2025:
                raw.append("data/raw/orders_{}-{:02d}.csv".format(y, m))
            elif m <= 10:
                incoming.append("data/incoming/orders_{}-{:02d}.csv".format(y, m))
    return raw, incoming


def load_orders(root, files):
    frames = []
    for f in files:
        df = pd.read_csv(root / f, dtype=str, keep_default_na=False)
        df["file"] = f
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["qty"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
    df["file_month"] = df["file"].str.extract(r"orders_(\d{4}-\d{2})")[0]
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument("--skip-repro", action="store_true", help="skip the regenerate-and-compare check")
    args = ap.parse_args()
    root = args.root.resolve()

    # 1. Files and columns ------------------------------------------------------
    raw, incoming = expected_files()
    config = ["data/raw/toy_lines.csv", "data/raw/material_prices.csv", "data/raw/factory.csv"]
    actual_raw = sorted(str(p.relative_to(root)) for p in (root / "data/raw").glob("orders_*.csv"))
    actual_inc = sorted(str(p.relative_to(root)) for p in (root / "data/incoming").glob("orders_*.csv"))
    check("36 order files in data/raw", actual_raw == raw, "found {}".format(len(actual_raw)))
    check("10 order files in data/incoming", actual_inc == incoming, "found {}".format(len(actual_inc)))
    missing_cfg = [c for c in config if not (root / c).exists()]
    check("config files present", not missing_cfg, ", ".join(missing_cfg))
    if not (actual_raw == raw and actual_inc == incoming and not missing_cfg):
        print("Stopping: files missing.")
        return 1

    bad_cols = [f for f in raw + incoming if list(pd.read_csv(root / f, nrows=0).columns) != ORDER_COLUMNS]
    check("order files have exact columns in order", not bad_cols, ", ".join(bad_cols[:3]))

    # 2. Economics --------------------------------------------------------------
    lines = pd.read_csv(root / "data/raw/toy_lines.csv")
    mats = pd.read_csv(root / "data/raw/material_prices.csv").set_index("material")["base_price_per_kg"]
    capacity = int(pd.read_csv(root / "data/raw/factory.csv")["capacity_units_per_quarter"].iloc[0])
    check("toy_lines.csv columns", list(lines.columns) == TOY_LINE_COLUMNS)
    check("toy_lines.csv has the 4 toy lines", sorted(lines["toy_line"]) == sorted(TOY_LINES))
    lines["unit_cost"] = (lines["resin_kg_per_unit"] * mats["resin"]
                          + lines["cardboard_kg_per_unit"] * mats["cardboard"] + lines["other_unit_cost"])
    for _, r in lines.iterrows():
        check("{}: discount {:.2f} < unit cost {:.2f} < price {:.2f}".format(
            r["toy_line"], r["discount_price"], r["unit_cost"], r["price"]),
            r["discount_price"] < r["unit_cost"] < r["price"])

    # 3. Rates and mess log -----------------------------------------------------
    df = load_orders(root, raw + incoming)
    log = pd.read_csv(root / "work/generated_mess_log.csv", dtype=str, keep_default_na=False)
    n_orders = df["order_id"].nunique()
    cancel_rate = (df.drop_duplicates("order_id")["status"] == "cancelled").mean()
    check("cancelled rate 3-7%", 0.03 <= cancel_rate <= 0.07, "{:.1%}".format(cancel_rate))
    mess_rate = len(log) / n_orders
    check("mess rate 2-4%", 0.02 <= mess_rate <= 0.04, "{} of {} orders = {:.1%}".format(len(log), n_orders, mess_rate))
    check("all 5 mess types present", set(log["issue"]) == MESS_TYPES, str(sorted(set(log["issue"]))))

    # every logged problem is really in its file ...
    not_found = []
    for _, e in log.iterrows():
        rows = df[(df["order_id"] == e["order_id"]) & (df["file"] == e["file"])]
        ok = {
            "duplicate": len(rows) >= 2,
            "missing_quantity": rows["quantity"].eq("").any(),
            "misspelled_toy_line": (~rows["toy_line"].isin(TOY_LINES)).any(),
            "bad_quantity": ((rows["qty"] < 0) | (rows["qty"] >= 50000)).any(),
            "late_order": (rows["date"].dt.strftime("%Y-%m") != rows["file_month"]).any(),
        }[e["issue"]]
        if not ok:
            not_found.append(e["order_id"])
    check("every logged problem is in its file", not not_found, ", ".join(not_found[:5]))

    # ... and every problem in the files is logged
    found = set()
    found |= set(df.loc[df.duplicated(["order_id", "file"], keep=False), "order_id"])
    found |= set(df.loc[df["quantity"].eq(""), "order_id"])
    found |= set(df.loc[~df["toy_line"].isin(TOY_LINES), "order_id"])
    found |= set(df.loc[(df["qty"] < 0) | (df["qty"] >= 50000), "order_id"])
    found |= set(df.loc[df["date"].dt.strftime("%Y-%m") != df["file_month"], "order_id"])
    unlogged = found - set(log["order_id"])
    check("no unlogged problems in the files", not unlogged, ", ".join(sorted(unlogged)[:5]))

    # 4. Patterns (clean, confirmed rows) ---------------------------------------
    clean = df[~df["order_id"].isin(log["order_id"]) & (df["status"] == "confirmed")].copy()
    clean["year"] = clean["date"].dt.year
    clean["q"] = clean["date"].dt.quarter
    clean["qty"] = clean["qty"].astype(int)
    by = clean.groupby(["toy_line", "year", "q"])["qty"].sum()

    for y in (2023, 2024, 2025):
        s = by["Splash Squad"][y]
        check("Splash Squad {}: Q2+Q3 > Q1+Q4".format(y), s[2] + s[3] > s[1] + s[4],
              "{:,} vs {:,}".format(s[2] + s[3], s[1] + s[4]))
    bb = clean[clean["toy_line"] == "Block Builders"].groupby("year")["qty"].sum()
    for y in (2024, 2025):
        g = bb[y] / bb[y - 1] - 1
        check("Block Builders {} growth 6-14%".format(y), 0.06 <= g <= 0.14, "{:+.1%}".format(g))
    for y in (2023, 2024, 2025):
        t = by["Turbo Trucks"][y]
        ratio = t[4] / t[[1, 2, 3]].mean()
        check("Turbo Trucks {}: small Q4 bump (1.0-1.3x)".format(y), 1.0 < ratio < 1.3, "{:.2f}x".format(ratio))
    g = clean[clean["toy_line"] == "Galaxy Rangers"]
    h1 = lambda y: g[(g["year"] == y) & (g["q"] <= 2)]["qty"].sum()
    h2 = lambda y: g[(g["year"] == y) & (g["q"] >= 3)]["qty"].sum()
    check("Galaxy Rangers H1 2025 within 20% of H1 2024", 0.8 <= h1(2025) / h1(2024) <= 1.2,
          "{:.2f}x".format(h1(2025) / h1(2024)))
    check("Galaxy Rangers H2 2025 >= 1.8x H2 2024", h2(2025) / h2(2024) >= 1.8,
          "{:.2f}x".format(h2(2025) / h2(2024)))

    # 5. Capacity (confirmed demand incl. messy-but-real orders, deduplicated) --
    real = df[df["status"] == "confirmed"].drop_duplicates("order_id")
    real = real[(real["qty"] > 0) & (real["qty"] < 50000)]
    total = real.groupby([real["date"].dt.year, real["date"].dt.quarter])["qty"].sum()
    hist = total.loc[2023:2025]
    check("mean quarterly demand 2023-25 <= capacity", hist.mean() <= capacity,
          "{:,.0f} vs {:,}".format(hist.mean(), capacity))
    for y in (2023, 2024, 2025):
        check("Q4 {} demand > capacity".format(y), total[(y, 4)] > capacity,
              "{:,} vs {:,}".format(int(total[(y, 4)]), capacity))

    # 6. Reproducibility --------------------------------------------------------
    if args.skip_repro:
        print("SKIP  reproducibility")
    else:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable, "-I", str(GENERATOR), "--out-dir", tmp, "--quiet"], check=True)
            files = config + raw + incoming + ["work/generated_mess_log.csv"]
            digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            diff = [f for f in files if digest(root / f) != digest(Path(tmp) / f)]
            check("regenerating with seed 42 gives identical files", not diff, ", ".join(diff[:3]))

    n_fail = results.count(False)
    print("\n{} checks, {} failed".format(len(results), n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())

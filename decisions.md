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

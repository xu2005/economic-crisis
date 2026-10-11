#!/usr/bin/env python3
"""Reproduce LOCAL_TDX_PRICE-only close-to-close study. Never imply dividend-adjusted returns.
Run locally: python scripts/reproduce_tdx_price_only.py --input-dir PATH --out-dir OUTPUT
Only Python standard library. Input CSV files must remain private; do not commit raw rows.
"""
import argparse
import csv
import json
import math
from pathlib import Path

SYMBOLS = ("510300", "511010", "000300", "159307")

def load_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        expected = {"date", "open", "high", "low", "close", "tdx_export_volume_raw"}
        if not expected.issubset(set(reader.fieldnames or ())):
            raise ValueError(f"{path}: missing required columns")
        rows = []
        for item in reader:
            row = {"date": item["date"]}
            for field in ("open", "high", "low", "close", "tdx_export_volume_raw"):
                row[field] = float(item[field])
                if not math.isfinite(row[field]):
                    raise ValueError(f"{path}: non-finite {field}")
            if (row["low"] <= 0 or row["low"] > min(row["open"], row["close"])
                or row["high"] < max(row["open"], row["close"])
                or row["tdx_export_volume_raw"] <= 0):
                raise ValueError(f"{path}: OHLC/volume anomaly on {row['date']}")
            if rows and row["date"] <= rows[-1]["date"]:
                raise ValueError(f"{path}: duplicate or unordered date {row['date']}")
            rows.append(row)
    if len(rows) < 2:
        raise ValueError(f"{path}: too few rows")
    return rows

def describe_equity(values):
    returns = [values[i] / values[i - 1] - 1.0 for i in range(1, len(values))]
    avg = sum(returns) / len(returns)
    std = math.sqrt(sum((x - avg) ** 2 for x in returns) / (len(returns) - 1)) if len(returns) > 1 else 0.0
    peak = 0.0
    mdd = 0.0
    for v in values:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1.0)
    return {
        "return_pct": round((values[-1] / values[0] - 1.0) * 100.0, 4),
        "max_drawdown_pct": round(mdd * 100.0, 4),
        "annualized_vol_pct": round(std * math.sqrt(252.0) * 100.0, 4),
    }

def run(input_dir, out_dir):
    data = {code: load_rows(input_dir / f"tdx_{code}_ohlcv.csv") for code in SYMBOLS}
    dates = [r["date"] for r in data["510300"]]
    for code, rows in data.items():
        if [r["date"] for r in rows] != dates:
            raise ValueError(f"{code}: date alignment failure")
    eq = {}
    for code, rows in data.items():
        base = rows[0]["close"]
        eq[code] = [r["close"] / base for r in rows]
    eq["ILLUSTRATIVE_DOMESTIC_60_40"] = [
        0.6 * a + 0.4 * b for a, b in zip(eq["510300"], eq["511010"])
    ]
    summary = {
        "source": "LOCAL_TDX_PRICE",
        "date_first": dates[0], "date_last": dates[-1], "observations": len(dates),
        "assumptions": "No dividends, fees, taxes, slippage, execution guarantees or rebalancing",
        "metrics": {name: describe_equity(values) for name, values in eq.items()},
        "strategy_159307": "FORMAL BACKTEST BLOCKED",
        "portfolio_v3x": "IMPLEMENTATION BLOCKED",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "daily_equity.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", *eq.keys()])
        for i, date in enumerate(dates):
            w.writerow([date, *(f"{v[i]:.10f}" for v in eq.values())])
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", required=True, type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    args = p.parse_args()
    run(args.input_dir, args.out_dir)

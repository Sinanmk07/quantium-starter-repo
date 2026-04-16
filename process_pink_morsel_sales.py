"""
Merge daily_sales_data_*.csv files: keep Pink Morsel rows only,
compute Sales = quantity * price, output Sales / Date / Region.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
INPUT_GLOB = "daily_sales_data_*.csv"
OUTPUT_PATH = DATA_DIR / "pink_morsel_sales.csv"


def main() -> None:
    paths = sorted(DATA_DIR.glob(INPUT_GLOB))
    if not paths:
        raise SystemExit(f"No files matching {INPUT_GLOB!r} under {DATA_DIR}")

    frames = [pd.read_csv(p) for p in paths]
    df = pd.concat(frames, ignore_index=True)

    pink = df["product"].str.strip().str.lower() == "pink morsel"
    df = df.loc[pink].copy()

    price = df["price"].astype(str).str.replace("$", "", regex=False).astype(float)
    qty = df["quantity"].astype(int)
    df["Sales"] = price * qty

    out = df[["Sales", "date", "region"]].rename(
        columns={"date": "Date", "region": "Region"}
    )
    out = out.sort_values(["Date", "Region"], kind="mergesort").reset_index(drop=True)

    out.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(out)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

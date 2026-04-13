#!/usr/bin/env python3
"""
Build a clean monthly 9-state gasoline price panel from the EIA API.

Coverage in this EIA retail gasoline product:
CA, CO, FL, MA, MN, NY, OH, TX, WA

Output:
- eia_monthly_9state_gas_prices.csv

Notes:
- Pulls monthly nominal gasoline prices directly from the EIA endpoint
- Keeps only the 9 states with published state-level gasoline series
- Standardizes columns and sorts state/month
"""

from __future__ import annotations

import time
import requests
import pandas as pd


API_KEY = "RTXFDsKMCXHm5itaad4K7niMIZeA3eAX9ZdOSGf3"
BASE_URL = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"

# EIA state gasoline area codes for the 9 states that return data in this product
STATE_CODES = {
    "CA": "SCA",
    "CO": "SCO",
    "FL": "SFL",
    "MA": "SMA",
    "MN": "SMN",
    "NY": "SNY",
    "OH": "SOH",
    "TX": "STX",
    "WA": "SWA",
}

PRODUCT = "EPMR"  # regular gasoline, all formulations


def fetch_state_monthly(state_abbr: str, duoarea_code: str, pause: float = 0.1) -> pd.DataFrame:
    params = {
        "api_key": API_KEY,
        "frequency": "monthly",
        "data[0]": "value",
        "facets[duoarea][]": duoarea_code,
        "facets[product][]": PRODUCT,
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "offset": 0,
        "length": 5000,
    }

    r = requests.get(BASE_URL, params=params, timeout=60)
    r.raise_for_status()
    j = r.json()

    rows = j.get("response", {}).get("data", [])
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).copy()
    df["state"] = state_abbr
    df["month"] = pd.to_datetime(df["period"])
    df["gas_price_nominal"] = pd.to_numeric(df["value"], errors="coerce")

    keep = [c for c in ["state", "month", "gas_price_nominal", "units", "series"] if c in df.columns]
    df = df[keep].sort_values(["state", "month"]).reset_index(drop=True)

    time.sleep(pause)
    return df


def build_panel() -> pd.DataFrame:
    frames = []

    for state_abbr, duoarea_code in STATE_CODES.items():
        print(f"Pulling {state_abbr}...")
        df_state = fetch_state_monthly(state_abbr, duoarea_code)
        if df_state.empty:
            print(f"Warning: no data returned for {state_abbr}")
            continue
        frames.append(df_state)

    if not frames:
        raise RuntimeError("No state data were returned from the EIA API.")

    panel = pd.concat(frames, ignore_index=True)

    # Clean and standardize
    panel = (
        panel.dropna(subset=["month", "gas_price_nominal"])
             .sort_values(["state", "month"])
             .reset_index(drop=True)
    )

    # Add YYYY-MM string for convenience
    panel["year_month"] = panel["month"].dt.strftime("%Y-%m")

    # Reorder columns
    preferred_order = ["state", "month", "year_month", "gas_price_nominal", "units", "series"]
    existing = [c for c in preferred_order if c in panel.columns]
    panel = panel[existing]

    return panel


def main() -> None:
    panel = build_panel()
    out = "eia_monthly_9state_gas_prices.csv"
    panel.to_csv(out, index=False)

    print("\nSaved:", out)
    print("States:", sorted(panel["state"].unique()))
    print("Rows:", len(panel))
    print("\nPreview:")
    print(panel.head(12).to_string(index=False))


if __name__ == "__main__":
    main()

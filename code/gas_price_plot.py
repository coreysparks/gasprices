#!/usr/bin/env python3
"""
Create a monthly plot of inflation adjusted U.S. gasoline prices, 1976 to 2026,
with presidential party terms shaded in the background.

Data sources are pulled from FRED:
- APU000074714: Average price, gasoline, all types, U.S. city average
- CPIAUCSL: CPI for All Urban Consumers, All Items
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


START = "1976-01-01"
END = "2026-12-31"

# Presidential terms covering the requested window.
PRESIDENTIAL_TERMS = [
    ("1976-01-01", "1977-01-20", "Republican", "Ford"),
    ("1977-01-20", "1981-01-20", "Democrat", "Carter"),
    ("1981-01-20", "1989-01-20", "Republican", "Reagan"),
    ("1989-01-20", "1993-01-20", "Republican", "G.H.W. Bush"),
    ("1993-01-20", "2001-01-20", "Democrat", "Clinton"),
    ("2001-01-20", "2009-01-20", "Republican", "G.W. Bush"),
    ("2009-01-20", "2017-01-20", "Democrat", "Obama"),
    ("2017-01-20", "2021-01-20", "Republican", "Trump"),
    ("2021-01-20", "2025-01-20", "Democrat", "Biden"),
    ("2025-01-20", "2029-01-20", "Republican", "Trump"),
]


def fetch_data(start: str = START, end: str = END) -> pd.DataFrame:
    """Download gas price and CPI series from FRED and compute real gas prices."""
    gas = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=APU000074714", index_col=0, parse_dates=True)
    cpi = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL", index_col=0, parse_dates=True)
    gas = gas.loc[start:end]
    cpi = cpi.loc[start:end]

    df = gas.join(cpi, how="inner")
    df.columns = ["gas_nominal", "cpi"]
    df = df.dropna().copy()

    # Express real prices in dollars of the last available month in the sample.
    base_cpi = df["cpi"].iloc[-1]
    df["gas_real"] = df["gas_nominal"] * (base_cpi / df["cpi"])
    df["gas_real_12mo"] = df["gas_real"].rolling(6, min_periods=1).mean()

    return df


def add_party_shading(ax: plt.Axes) -> None:
    """Shade presidential terms by party."""
    for start, end, party, _president in PRESIDENTIAL_TERMS:
        color = "red" if party == "Republican" else "blue"
        ax.axvspan(
            pd.to_datetime(start),
            pd.to_datetime(end),
            alpha=0.08,
            color=color,
            lw=0,
            zorder=0,
        )


def make_plot(df: pd.DataFrame, output_path: str = "inflation_adjusted_gas_prices_1976_2026.png") -> Path:
    """Create and save the chart."""
    fig, ax = plt.subplots(figsize=(14, 7))

    add_party_shading(ax)

    ax.plot(
        df.index,
        df["gas_real"],
        linewidth=1.0,
        alpha=0.35,
        label="Monthly real price",
        zorder=2,
    )
    ax.plot(
        df.index,
        df["gas_real_12mo"],
        linewidth=2.4,
        label="6 month moving average",
        zorder=3,
    )

    peak_idx = df["gas_real"].idxmax()
    peak_val = df.loc[peak_idx, "gas_real"]
    ax.scatter([peak_idx], [peak_val], zorder=4)
    ax.annotate(
        f"Peak: ${peak_val:.2f}\n{peak_idx:%b %Y}",
        xy=(peak_idx, peak_val),
        xytext=(15, -45),
        textcoords="offset points",
        fontsize=10,
        arrowprops=dict(arrowstyle="->", color="black"),
    )

    ax.text(
        0.01, 0.01, "All prices in 2026 dollars",
        transform=ax.transAxes, fontsize=9, color="gray", va="bottom",
    )

    ax.set_title("Inflation Adjusted U.S. Gasoline Prices, 1976 to 2026")
    ax.set_xlabel("Year")
    ax.set_ylabel("Price per gallon, constant dollars")
    ax.grid(True, alpha=0.3)

    ax.set_xlim(df.index.min(), df.index.max() + pd.DateOffset(months=6))

    ax.xaxis.set_major_locator(mdates.YearLocator(base=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    line_handles, line_labels = ax.get_legend_handles_labels()
    party_handles = [
        Patch(facecolor="red", alpha=0.15, label="Republican term"),
        Patch(facecolor="blue", alpha=0.15, label="Democratic term"),
    ]
    ax.legend(line_handles + party_handles, line_labels + ["Republican term", "Democratic term"], frameon=True)

    fig.tight_layout()

    output = Path(output_path).resolve()
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def save_data(df: pd.DataFrame, csv_path: str = "inflation_adjusted_gas_prices_1976_2026.csv") -> Path:
    """Save the underlying data."""
    output = Path(csv_path).resolve()
    df.reset_index(names="date").to_csv(output, index=False)
    return output


def main() -> int:
    try:
        df = fetch_data()
    except Exception as exc:
        print("Failed to download data from FRED.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    plot_path = make_plot(df)
    csv_path = save_data(df)

    print(f"Plot saved to: {plot_path}")
    print(f"Data saved to: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

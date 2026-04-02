#!/usr/bin/env python3
"""
Create a monthly plot of inflation adjusted U.S. gasoline prices, 1976 to 2026,
with presidential party terms shaded in the background, and add a provisional
March 2026 point before the official BLS gas price and CPI releases arrive.

Official historical series:
- APU00007471A  : Average Price, Gasoline, All Types, U.S. City Average, monthly, BLS via FRED
- CPIAUCSL      : CPI for All Urban Consumers, All Items, seasonally adjusted, monthly, BLS via FRED

Provisional March 2026 extension:
- GASALLM       : U.S. All Grades All Formulations Gas Price, monthly, EIA via FRED
- March 2026 CPI nowcast from the Cleveland Fed, applied to the last official CPIAUCSL value

Method for the provisional March 2026 gas price:
1. Pull the official BLS gas series through its latest available month.
2. Pull the monthly EIA all-grades gasoline series.
3. Compute a bridge ratio using the latest overlapping month:
      bridge_ratio = official_bls_gas / eia_gas
4. Estimate March 2026 BLS-comparable nominal gas price as:
      provisional_nominal = eia_march_2026 * bridge_ratio
5. Estimate March 2026 CPIAUCSL as:
      provisional_cpi = cpi_feb_2026 * (1 + nowcast_mom_rate)
6. Deflate nominal gas prices into constant dollars using the last available CPI in the final dataset.

This gives you a transparent provisional March 2026 point that can later be replaced
automatically once the official BLS releases are available.
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

# Cleveland Fed March 2026 CPI nowcast, month over month, seasonally adjusted.
# Expressed as a decimal.
MARCH_2026_CPI_NOWCAST_MOM = 0.0084

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


def fetch_official_data(start: str = START, end: str = END) -> pd.DataFrame:
    """Download official BLS gas and CPI series from FRED."""
    gas = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=APU00007471A", index_col=0, parse_dates=True).loc[start:end]
    cpi = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL", index_col=0, parse_dates=True).loc[start:end]

    df = gas.join(cpi, how="inner")
    df.columns = ["gas_nominal", "cpi"]
    df = df.dropna().copy()
    df["source_flag"] = "official"
    return df


def add_provisional_march_2026(df: pd.DataFrame) -> pd.DataFrame:
    """Append a provisional March 2026 observation using EIA gas and a CPI nowcast."""
    eia = pd.read_csv("https://fred.stlouisfed.org/graph/fredgraph.csv?id=GASALLM", index_col=0, parse_dates=True).loc[START:END].dropna()
    eia.columns = ["eia_gas_monthly"]

    overlap = df.join(eia, how="inner").dropna()
    if overlap.empty:
        raise ValueError("No overlap found between official BLS gas series and EIA gas series.")

    latest_overlap_date = overlap.index.max()
    bridge_ratio = overlap.loc[latest_overlap_date, "gas_nominal"] / overlap.loc[latest_overlap_date, "eia_gas_monthly"]

    target_date = pd.Timestamp("2026-03-01")
    if target_date not in eia.index:
        return df

    if target_date in df.index:
        return df

    last_official_cpi = df["cpi"].iloc[-1]
    provisional_cpi = last_official_cpi * (1.0 + MARCH_2026_CPI_NOWCAST_MOM)
    provisional_nominal = float(eia.loc[target_date, "eia_gas_monthly"]) * bridge_ratio

    provisional_row = pd.DataFrame(
        {
            "gas_nominal": [provisional_nominal],
            "cpi": [provisional_cpi],
            "source_flag": ["provisional"],
        },
        index=[target_date],
    )

    out = pd.concat([df, provisional_row]).sort_index()
    return out


def compute_real_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Compute inflation adjusted gas prices in constant dollars of the last available month."""
    out = df.copy()
    base_cpi = out["cpi"].iloc[-1]
    out["gas_real"] = out["gas_nominal"] * (base_cpi / out["cpi"])
    out["gas_real_12mo"] = out["gas_real"].rolling(6, min_periods=1).mean()
    return out


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


def make_plot(df: pd.DataFrame, output_path: str = "inflation_adjusted_gas_prices_1976_2026_provisional_march.png") -> Path:
    """Create and save the chart."""
    fig, ax = plt.subplots(figsize=(14, 7))

    add_party_shading(ax)

    official = df[df["source_flag"] == "official"]
    provisional = df[df["source_flag"] == "provisional"]

    ax.plot(
        official.index,
        official["gas_real"],
        linewidth=1.0,
        alpha=0.35,
        label="Monthly real price, official",
        zorder=2,
    )

    if not provisional.empty:
        ax.plot(
            provisional.index,
            provisional["gas_real"],
            marker="o",
            linestyle="None",
            label="March 2026, provisional",
            zorder=4,
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
    ax.scatter([peak_idx], [peak_val], zorder=5)
    ax.annotate(
        f"Peak: ${peak_val:.2f}\n{peak_idx:%b %Y}",
        xy=(peak_idx, peak_val),
        xytext=(15, -45),
        textcoords="offset points",
        fontsize=10,
        arrowprops=dict(arrowstyle="->", color="black"),
    )

    if not provisional.empty:
        prov_idx = provisional.index[0]
        prov_val = provisional["gas_real"].iloc[0]
        ax.annotate(
            f"Provisional: ${prov_val:.2f}\n{prov_idx:%b %Y}",
            xy=(prov_idx, prov_val),
            xytext=(-10, -35),
            textcoords="offset points",
            ha="right",
            fontsize=10,
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
    ax.legend(
        line_handles + party_handles,
        line_labels + ["Republican term", "Democratic term"],
        frameon=True,
    )

    fig.tight_layout()

    output = Path(output_path).resolve()
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def save_data(df: pd.DataFrame, csv_path: str = "inflation_adjusted_gas_prices_1976_2026_provisional_march.csv") -> Path:
    """Save the underlying data."""
    output = Path(csv_path).resolve()
    df.reset_index(names="date").to_csv(output, index=False)
    return output


def main() -> int:
    try:
        df = fetch_official_data()
        df = add_provisional_march_2026(df)
        df = compute_real_prices(df)
    except Exception as exc:
        print("Failed to download or prepare data.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    plot_path = make_plot(df)
    csv_path = save_data(df)

    print(f"Plot saved to: {plot_path}")
    print(f"Data saved to: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# gasprices

Generates a chart of inflation-adjusted U.S. gasoline prices from 1976 to the present, with presidential terms shaded by party.

## What it does

- Fetches two data series from [FRED](https://fred.stlouisfed.org/):
  - `APU000074714` — Average U.S. gasoline price (all types, city average)
  - `CPIAUCSL` — CPI for All Urban Consumers
- Adjusts nominal prices to constant dollars using the most recent month's CPI as the base
- Plots monthly real prices alongside a 6-month moving average
- Shades the background red/blue by presidential party term
- Annotates the all-time peak price
- Saves the chart as a PNG and the underlying data as a CSV

## Scripts

### `gas_price_plot.py` — official data only

Plots the historical series using official BLS gas prices (`APU000074714`) and CPI (`CPIAUCSL`) from FRED.

```bash
python code/gas_price_plot.py
```

### `gas_price_plot_provisional_march.py` — with provisional March 2026 estimate

Extends the chart with a provisional March 2026 data point before the official BLS release. The estimate is constructed by:

1. Bridging the official BLS gas series to the EIA all-grades series (`GASALLM`) using the latest overlapping month
2. Applying the bridge ratio to the EIA March 2026 value to get a BLS-comparable nominal gas price
3. Projecting March 2026 CPI using the Cleveland Fed nowcast (`MARCH_2026_CPI_NOWCAST_MOM`)

The provisional point is plotted distinctly and labeled. Once the official BLS data is released, re-running `gas_price_plot.py` will replace it automatically.

```bash
python code/gas_price_plot_provisional_march.py
```

## Output

- `inflation_adjusted_gas_prices_1976_2026.png` — official data chart
- `inflation_adjusted_gas_prices_1976_2026.csv` — official data
- `inflation_adjusted_gas_prices_1976_2026_provisional_march.png` — chart with provisional March 2026 point
- `inflation_adjusted_gas_prices_1976_2026_provisional_march.csv` — data including provisional point

## Dependencies

- `matplotlib`
- `pandas`

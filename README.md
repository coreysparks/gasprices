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

## Usage

Run the script directly:

```bash
python code/gas_price_plot.py
```

Or call the functions from a notebook:

```python
from code.gas_price_plot import fetch_data, make_plot, save_data

df = fetch_data()
make_plot(df)
save_data(df)
```

## Output

- `inflation_adjusted_gas_prices_1976_2026.png` — the chart
- `inflation_adjusted_gas_prices_1976_2026.csv` — the underlying data

## Dependencies

- `matplotlib`
- `pandas`

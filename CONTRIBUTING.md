# Contributing

Issues and pull requests are welcome.

- `pip install -e ".[dev]"`, then `ruff check . && mypy && pytest` must pass. Coverage
  below 100% fails the run and any warning fails a test.
- Money and rates stay `Decimal`. Floats appear only inside the path generator and are
  rounded to 4 places before they touch an order.
- The report stays one HTML file with no script, so it can be mailed, opened offline and
  printed.

"""CSV in and out. Amounts are read as text straight into Decimal, never through float."""

import csv
from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .model import PO

FIELDS = ["po", "sku", "units", "usd", "duty_rate", "other_brl", "sell_brl", "costing_rate",
          "due"]


def read_pos(path: Path) -> list[PO]:
    out = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        missing = set(FIELDS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name}: missing columns {sorted(missing)}")
        for n, row in enumerate(reader, start=2):
            try:
                out.append(PO(row["po"], row["sku"], int(row["units"]), Decimal(row["usd"]),
                              Decimal(row["duty_rate"]), Decimal(row["other_brl"]),
                              Decimal(row["sell_brl"]), Decimal(row["costing_rate"]),
                              date.fromisoformat(row["due"])))
            except (ValueError, InvalidOperation) as e:
                raise ValueError(f"{path.name} line {n}: {e}") from e
    return out


def write_pos(path: Path, pos: Iterable[PO]) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        for p in pos:
            w.writerow([p.po, p.sku, p.units, p.usd, p.duty_rate, p.other_brl, p.sell_brl,
                        p.costing_rate, p.due.isoformat()])


def write_table(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

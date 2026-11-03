"""Scenario engine: margin of every order under fixed shocks and under a volatility band."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .model import PIP, PO, cents

SHOCKS = (Decimal(-10), Decimal(-5), Decimal(0), Decimal(5), Decimal(10), Decimal(20))
Z95 = 1.645  # one-sided 95% point of the standard normal


def shocked(spot: Decimal, pct: Decimal) -> Decimal:
    return (spot * (1 + pct / 100)).quantize(PIP, ROUND_HALF_UP)


def high_rate(spot: Decimal, vol: Decimal, days: int, z: float = Z95) -> Decimal:
    """Rate the dollar stays below with 95% odds by the payment date.

    Lognormal with no drift: spot x exp(z x vol x sqrt(days / 365)). The exponential is the
    only float step; the result is rounded to 4 places and used as a Decimal.
    """
    t = max(days, 0) / 365
    return Decimal(str(round(float(spot) * math.exp(z * float(vol) * math.sqrt(t)), 4)))


@dataclass(frozen=True)
class Row:
    po: PO
    margin_now: Decimal
    by_shock: tuple[Decimal, ...]
    per_pct: Decimal
    high: Decimal
    at_risk: Decimal       # margin lost if the dollar reaches `high`
    margin_high: Decimal

    @property
    def flagged(self) -> bool:
        """The order loses money inside the 95% band."""
        return self.margin_high < 0


def run(pos: Sequence[PO], spot: Decimal, vol: Decimal, today: date,
        shocks: Sequence[Decimal] = SHOCKS) -> list[Row]:
    rows = []
    for p in pos:
        hi = high_rate(spot, vol, (p.due - today).days)
        rows.append(Row(p, p.margin(spot), tuple(p.margin(shocked(spot, s)) for s in shocks),
                        p.per_pct(spot), hi, cents(p.exposure * (hi - spot)), p.margin(hi)))
    return sorted(rows, key=lambda r: (-r.at_risk, r.po.po))


def totals(rows: Sequence[Row]) -> tuple[Decimal, tuple[Decimal, ...], Decimal]:
    """Margin now, margin per shock and margin at risk summed over the book."""
    n = len(rows[0].by_shock) if rows else 0
    return (sum((r.margin_now for r in rows), Decimal("0.00")),
            tuple(sum((r.by_shock[i] for r in rows), Decimal("0.00")) for i in range(n)),
            sum((r.at_risk for r in rows), Decimal("0.00")))

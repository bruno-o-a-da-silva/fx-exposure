"""Seeded synthetic book of open import orders. Invented suppliers, products and prices."""

import random
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from .model import PO, cents

TODAY = date(2026, 11, 2)
SPOT = Decimal("5.40")  # illustrative BRL per USD, not a market quote
VOL = Decimal("0.15")   # illustrative annual volatility
DUTIES = (Decimal("0"), Decimal("0.08"), Decimal("0.12"), Decimal("0.18"))


def generate(seed: int = 21, n: int = 40) -> list[PO]:
    """Orders priced over the last months at rates between 4.95 and 5.45.

    Each sale price is set for a target margin between 6% and 24% at its costing rate, so
    orders costed at a cheap dollar are already squeezed at today's spot.
    """
    rng = random.Random(seed)
    out = []
    for k in range(n):
        units = rng.randrange(200, 6000, 50)
        usd = Decimal(rng.randrange(150, 4000)) / 100 * units
        duty = rng.choice(DUTIES)
        rate = Decimal(rng.randrange(495, 546)) / 100
        other = cents(usd * rate * Decimal(rng.randrange(3, 9)) / 100)
        target = Decimal(rng.randrange(6, 25)) / 100
        cost = usd * rate * (1 + duty) + other
        sell = (cost / (1 - target) / units).quantize(Decimal("0.01"), ROUND_HALF_UP)
        due = TODAY + timedelta(days=rng.randrange(15, 181))
        out.append(PO(f"PO-{k + 1:03d}", f"SKU-{rng.randrange(100, 999)}", units,
                      cents(usd), duty, other, sell, rate, due))
    return out

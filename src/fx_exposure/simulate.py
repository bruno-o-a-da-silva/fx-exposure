"""Replay seeded dollar paths against the book under three hedging choices."""

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from .model import PIP, PO
from .scenarios import run

Policy = Literal["none", "flagged", "all"]
POLICIES: tuple[Policy, ...] = ("none", "flagged", "all")
CARRY = Decimal("0.10")  # illustrative yearly cost of buying the dollar forward


def forward(spot: Decimal, days: int, carry: Decimal = CARRY) -> Decimal:
    """Forward rate with a simple carry: spot x (1 + carry x days / 365)."""
    return (spot * (1 + carry * days / 365)).quantize(PIP)


def paths(spot: Decimal, vol: Decimal, today: date, dues: Sequence[date], n: int,
          seed: int) -> list[dict[date, Decimal]]:
    """`n` driftless lognormal paths, read on each payment date. Same seed, same paths."""
    rng = random.Random(seed)
    days = sorted({max((d - today).days, 0) for d in dues})
    s2 = float(vol) ** 2
    out = []
    for _ in range(n):
        x, t0, at = 0.0, 0, {}
        for d in days:
            dt = (d - t0) / 365
            x += -0.5 * s2 * dt + float(vol) * math.sqrt(dt) * rng.gauss(0, 1)
            at[d] = Decimal(str(round(float(spot) * math.exp(x), 4)))
            t0 = d
        out.append({today.fromordinal(today.toordinal() + d): r for d, r in at.items()})
    return out


@dataclass(frozen=True)
class Outcome:
    policy: Policy
    hedged: int
    mean: Decimal         # mean total margin across paths
    p5: Decimal           # total margin in the worst 5% of paths
    worst: Decimal
    losers: float         # mean number of orders sold at a loss


def replay(pos: Sequence[PO], spot: Decimal, vol: Decimal, today: date, n: int = 2000,
           seed: int = 1) -> list[Outcome]:
    flagged = {r.po.po for r in run(pos, spot, vol, today) if r.flagged}
    ps = paths(spot, vol, today, [p.due for p in pos], n, seed)
    fwd = {p.po: forward(spot, (p.due - today).days) for p in pos}
    out = []
    for pol in POLICIES:
        hedge = {p.po for p in pos if pol == "all" or (pol == "flagged" and p.po in flagged)}
        totals, losers = [], 0
        for path in ps:
            tot = Decimal("0.00")
            for p in pos:
                m = p.margin(fwd[p.po] if p.po in hedge else path[max(p.due, today)])
                tot += m
                losers += m < 0
            totals.append(tot)
        totals.sort()
        out.append(Outcome(pol, len(hedge), (sum(totals, Decimal(0)) / n).quantize(Decimal("0.01")),
                           totals[int(0.05 * n)], totals[0], losers / n))
    return out

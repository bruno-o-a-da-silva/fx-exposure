import math
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

from fx_exposure.model import PO
from fx_exposure.scenarios import high_rate, run, shocked, totals

D = Decimal
TODAY = date(2026, 11, 3)


def test_shocked() -> None:
    assert shocked(D("5.40"), D(5)) == D("5.6700")
    assert shocked(D("5.40"), D(-10)) == D("4.8600")


def test_high_rate_hand_case() -> None:
    # One year: 1.645 x 0.15 x 1 = 0.24675; exp = 1.279859; x 5.40 = 6.91124.
    assert math.isclose(math.exp(0.24675), 1.279859, rel_tol=1e-6)
    assert high_rate(D("5.40"), D("0.15"), 365) == D("6.9112")
    assert high_rate(D("5.40"), D("0.15"), 0) == D("5.4")
    assert high_rate(D("5.40"), D("0.15"), -5) == D("5.4")


def test_run_and_totals(po: PO) -> None:
    far = replace(po, po="PO-2", due=TODAY + timedelta(days=365))
    rows = run([po, far], D("5.40"), D("0.15"), TODAY)
    assert [r.po.po for r in rows] == ["PO-2", "PO-1"]  # longer horizon, more at risk
    r = rows[1]
    assert r.by_shock[3] == D("5630.00") and r.margin_now == D("8600.00")
    assert r.at_risk == r.margin_now - r.margin_high
    # One year: 5.40 x exp(1.645 x 0.15) = 6.9112, above break-even 6.1818: flagged.
    assert rows[0].high == D("6.9112") and rows[0].flagged and not r.flagged
    now, shocks, risk = totals(rows)
    assert now == D("17200.00") and shocks[2] == now and risk == rows[0].at_risk + r.at_risk
    assert totals([]) == (D("0.00"), (), D("0.00"))

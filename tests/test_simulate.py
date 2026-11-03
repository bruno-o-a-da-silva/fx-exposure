from datetime import date, timedelta
from decimal import Decimal

from fx_exposure.model import PO
from fx_exposure.scenarios import run
from fx_exposure.simulate import forward, paths, replay
from fx_exposure.synthetic import SPOT, TODAY, VOL, generate

D = Decimal


def test_generate_seeded() -> None:
    a = generate()
    assert a == generate() and a != generate(22)
    assert len(a) == 40 and all(TODAY < p.due <= TODAY + timedelta(days=180) for p in a)
    # Every order makes money at the rate it was costed at.
    assert all(p.margin(p.costing_rate) > 0 for p in a)


def test_forward_hand_case() -> None:
    # 5.40 x (1 + 0.10 x 73 / 365) = 5.40 x 1.02 = 5.508
    assert forward(D("5.40"), 73) == D("5.5080")


def test_paths_are_seeded_and_cover_dues() -> None:
    dues = [date(2026, 12, 1), date(2027, 2, 1), date(2026, 10, 1)]
    a = paths(D("5.40"), D("0.15"), date(2026, 11, 3), dues, 5, 1)
    assert a == paths(D("5.40"), D("0.15"), date(2026, 11, 3), dues, 5, 1)
    assert set(a[0]) == {date(2026, 11, 3), date(2026, 12, 1), date(2027, 2, 1)}
    assert all(p[date(2026, 11, 3)] == D("5.4") for p in a)  # past due pays spot


def test_hedge_all_is_certain(po: PO) -> None:
    out = {o.policy: o for o in replay([po], D("5.40"), D("0.15"), date(2026, 11, 3), 50, 2)}
    a = out["all"]
    assert a.mean == a.p5 == a.worst == po.margin(forward(D("5.40"), 28))
    # One order far from its break-even is not flagged, so "flagged" hedges nothing.
    f, n = out["flagged"], out["none"]
    assert f.hedged == 0 and (f.mean, f.p5, f.worst) == (n.mean, n.p5, n.worst)


def test_headline_seed_21() -> None:
    pos = generate()
    assert sum(r.flagged for r in run(pos, SPOT, VOL, TODAY)) == 18
    none, flagged, all_ = replay(pos, SPOT, VOL, TODAY)
    assert (none.mean, none.p5) == (D("1899991.54"), D("130807.27"))
    assert (flagged.hedged, flagged.mean, flagged.p5) == (18, D("1680562.54"), D("778099.48"))
    assert (all_.mean, all_.p5) == (D("1455091.32"), D("1455091.32"))

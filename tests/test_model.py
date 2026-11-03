from dataclasses import replace
from decimal import Decimal

import pytest

from fx_exposure.model import PO

D = Decimal


def test_hand_case(po: PO) -> None:
    # 10,000 x 1.10 x 5.40 = 59,400; plus 2,000 = 61,400; revenue 70,000.
    assert po.exposure == D("11000.00")
    assert po.landed(D("5.40")) == D("61400.00")
    assert po.cost_per_unit(D("5.40")) == D("61.40")
    assert po.margin(D("5.40")) == D("8600.00")
    # +5% is 5.67: 62,370 + 2,000 = 64,370, margin 5,630. Linear: 11,000 x 0.27 = 2,970.
    assert po.margin(D("5.67")) == D("5630.00")
    assert po.margin(D("5.40")) - po.margin(D("5.67")) == po.exposure * D("0.27")
    assert po.per_pct(D("5.40")) == D("594.00")
    # (70,000 - 2,000) / 11,000 = 6.18181..., rounded down.
    assert po.breakeven == D("6.1818")
    assert po.margin(po.breakeven) >= 0 > po.margin(po.breakeven + D("0.0001"))


@pytest.mark.parametrize("change", [
    {"units": 0}, {"usd": D("0")}, {"duty_rate": D("-0.1")}, {"other_brl": D("-1")},
    {"costing_rate": D("0")},
])
def test_rejects_bad_orders(po: PO, change: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="PO-1"):
        replace(po, **change)  # type: ignore[arg-type]

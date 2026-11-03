"""Cost and margin of one open purchase order as a function of the BRL/USD rate.

Every amount that depends on the rate is linear in it, so the sensitivity is exact:
margin change = - USD amount x (1 + duty rate) x rate change.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
PIP = Decimal("0.0001")


def cents(x: Decimal) -> Decimal:
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PO:
    """An open import order: goods priced in USD, sold in BRL."""

    po: str
    sku: str
    units: int
    usd: Decimal          # customs value of the order in USD
    duty_rate: Decimal    # ad valorem, applied to the value in BRL
    other_brl: Decimal    # freight in Brazil, handling, fees: not tied to the dollar
    sell_brl: Decimal     # selling price per unit
    costing_rate: Decimal  # BRL per USD used when the sale price was set
    due: date             # when the USD is paid

    def __post_init__(self) -> None:
        if self.units <= 0 or self.usd <= 0:
            raise ValueError(f"{self.po}: units and usd must be positive")
        if self.duty_rate < 0 or self.other_brl < 0 or self.costing_rate <= 0:
            raise ValueError(f"{self.po}: negative duty or cost, or non-positive rate")

    @property
    def exposure(self) -> Decimal:
        """BRL of cost per 1.00 BRL/USD: the slope of cost against the rate."""
        return self.usd * (1 + self.duty_rate)

    def landed(self, rate: Decimal) -> Decimal:
        return cents(self.exposure * rate + self.other_brl)

    def cost_per_unit(self, rate: Decimal) -> Decimal:
        return cents(self.landed(rate) / self.units)

    @property
    def revenue(self) -> Decimal:
        return cents(self.sell_brl * self.units)

    def margin(self, rate: Decimal) -> Decimal:
        return self.revenue - self.landed(rate)

    def per_pct(self, rate: Decimal) -> Decimal:
        """Margin lost for each 1% the dollar rises from `rate`."""
        return cents(self.exposure * rate / 100)

    @property
    def breakeven(self) -> Decimal:
        """Highest rate at which the order still does not lose money, rounded down."""
        return ((self.revenue - self.other_brl) / self.exposure).quantize(PIP, ROUND_DOWN)

from datetime import date
from decimal import Decimal

import pytest

from fx_exposure.model import PO


@pytest.fixture
def po() -> PO:
    """Hand case: 10,000 USD, 10% duty, 2,000 BRL other costs, 1,000 units sold at 70."""
    return PO("PO-1", "SKU-1", 1000, Decimal("10000"), Decimal("0.10"), Decimal("2000"),
              Decimal("70"), Decimal("5.20"), date(2026, 12, 1))

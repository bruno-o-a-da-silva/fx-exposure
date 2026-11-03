"""Static HTML report: one file, no script, opens in any browser and prints as is."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from .scenarios import SHOCKS, Row, totals


def fmt(x: Decimal) -> str:
    return f"{x:,.2f}"


def render(rows: Sequence[Row], spot: Decimal, vol: Decimal, today: date, source: str,
           note: str = "") -> str:
    env = Environment(loader=PackageLoader("fx_exposure", "."), undefined=StrictUndefined,
                      autoescape=select_autoescape(["html", "j2"]))
    now, by_shock, risk = totals(rows)
    top = max((r.at_risk for r in rows), default=Decimal(1)) or Decimal(1)
    return env.get_template("report.html.j2").render(
        rows=rows, spot=spot, vol_pct=vol * 100, today=today, source=source, note=note,
        now=now, by_shock=by_shock, risk=risk, shocks=SHOCKS, top=top, fmt=fmt,
        flagged=sum(r.flagged for r in rows))

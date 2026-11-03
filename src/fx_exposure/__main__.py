"""Command line: scenarios and HTML report for a CSV of open orders, and the hedging replay."""

import argparse
from datetime import date
from decimal import Decimal
from pathlib import Path

from .io import read_pos, write_pos, write_table
from .report import fmt, render
from .scenarios import SHOCKS, run, totals
from .simulate import replay
from .synthetic import SPOT, TODAY, VOL, generate

NOTE = "Spot and volatility are illustrative inputs, not market quotes."


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fx-exposure", description=__doc__)
    p.add_argument("--spot", type=Decimal, default=SPOT)
    p.add_argument("--vol", type=Decimal, default=VOL, help="annual volatility, 0.15 = 15%%")
    p.add_argument("--today", type=date.fromisoformat, default=TODAY)
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("example", help="write the seeded synthetic book to CSV")
    e.add_argument("out", type=Path)
    e.add_argument("--seed", type=int, default=21)
    s = sub.add_parser("scenarios", help="margin per order under shocks and the 95%% band")
    s.add_argument("csv", type=Path)
    s.add_argument("--out", type=Path, help="CSV with one row per order")
    s.add_argument("--html", type=Path, help="static HTML report")
    m = sub.add_parser("simulate", help="replay seeded dollar paths under three hedge choices")
    m.add_argument("--seed", type=int, default=21)
    m.add_argument("--paths", type=int, default=2000)
    a = p.parse_args(argv)

    if a.cmd == "example":
        write_pos(a.out, generate(a.seed))
        print(f"wrote {a.out}: 40 synthetic orders, seed {a.seed}")
    elif a.cmd == "scenarios":
        rows = run(read_pos(a.csv), a.spot, a.vol, a.today)
        now, shocks, risk = totals(rows)
        moves = "  ".join(f"{s:+}%: {fmt(m)}" for s, m in zip(SHOCKS, shocks, strict=True))
        print(f"{len(rows)} orders, margin at spot {fmt(now)} BRL, at risk {fmt(risk)} BRL, "
              f"{sum(r.flagged for r in rows)} lose money inside the 95% band")
        print(moves)
        if a.out:
            write_table(a.out, ["po", "due", "margin_now", *[f"margin_{s:+}pct" for s in SHOCKS],
                                "per_pct", "high_rate", "at_risk", "margin_high", "flagged"],
                        [(r.po.po, r.po.due, r.margin_now, *r.by_shock, r.per_pct, r.high,
                          r.at_risk, r.margin_high, r.flagged) for r in rows])
        if a.html:
            a.html.write_text(render(rows, a.spot, a.vol, a.today, a.csv.name, NOTE))
    else:
        print(f"{'hedge':<10}{'orders':>7}{'mean margin':>16}{'worst 5%':>16}{'worst':>16}"
              f"{'at a loss':>11}")
        for o in replay(generate(a.seed), a.spot, a.vol, a.today, a.paths):
            print(f"{o.policy:<10}{o.hedged:>7}{fmt(o.mean):>16}{fmt(o.p5):>16}"
                  f"{fmt(o.worst):>16}{o.losers:>11.1f}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

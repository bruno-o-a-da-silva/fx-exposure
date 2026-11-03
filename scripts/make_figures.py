"""Draw docs/img/hero.png, band.png and hedge.png from the seeded run (seed 21)."""

from decimal import Decimal

import matplotlib.pyplot as plt
from _style import GOLD, GOLD_DIM, IMG, MUTED, SERIF, TEXT, style, title

from fx_exposure.scenarios import run
from fx_exposure.simulate import forward, paths, replay
from fx_exposure.synthetic import SPOT, TODAY, VOL, generate

SEED = 21


def hero() -> None:
    none, flagged, all_ = replay(generate(SEED), SPOT, VOL, TODAY)
    fig = plt.figure(figsize=(16, 6.4), dpi=100)
    fig.text(0.05, 0.80, "fx-exposure", fontfamily=SERIF, fontsize=50, color=TEXT)
    fig.text(0.05, 0.71, "What a move in the dollar costs each open order.", fontsize=17,
             color=TEXT)
    fig.text(0.05, 0.655, "Hedge the orders that lose money inside the 95% band, not the book.",
             fontsize=17, color=MUTED)
    fig.add_artist(plt.Line2D([0.05, 0.12], [0.6, 0.6], color=GOLD, lw=2))
    fig.text(0.95, 0.82, f"BRL {none.p5 / 1000:,.0f}k to {flagged.p5 / 1000:,.0f}k",
             fontfamily=SERIF, fontsize=36, color=GOLD, ha="right")
    fig.text(0.95, 0.74, "margin in the worst 5% of 2,000 seeded dollar paths, 40 synthetic orders",
             fontsize=13, color=MUTED, ha="right")
    ax = fig.add_axes((0.05, 0.06, 0.9, 0.44))
    ax.set_axis_off()
    top = float(none.mean)
    labels = ("No hedge", "Hedge the 18 flagged orders", "Hedge all 40 orders")
    for y, (label, o) in enumerate(zip(labels[::-1], (all_, flagged, none), strict=True)):
        col = GOLD if o.policy == "flagged" else GOLD_DIM
        ax.barh(y, float(o.p5), color=col, height=0.5)
        ax.barh(y, float(o.mean - o.p5), left=float(o.p5), color=col, alpha=0.45, height=0.5)
        ax.text(0, y + 0.36, label, fontsize=12, color=TEXT)
        ax.text(float(o.mean) + top * 0.01, y, f"worst 5%  BRL {o.p5:,.0f}   mean  BRL "
                f"{o.mean:,.0f}", va="center", fontsize=11, color=TEXT)
    ax.set_xlim(0, top * 1.6)
    ax.set_ylim(-0.5, 2.8)
    fig.savefig(IMG / "hero.png")
    plt.close(fig)


def band() -> None:
    rows = sorted(run(generate(SEED), SPOT, VOL, TODAY), key=lambda r: r.margin_now)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for y, r in enumerate(rows):
        col = GOLD if r.flagged else GOLD_DIM
        ax.plot([float(r.margin_high) / 1000, float(r.margin_now) / 1000], [y, y], color=col,
                lw=3, solid_capstyle="butt")
        ax.plot(float(r.margin_now) / 1000, y, "o", color=TEXT, ms=4)
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_yticks([])
    ax.set_ylabel("40 open orders, by margin at spot")
    ax.set_xlabel("Margin (BRL thousand): dot at spot 5.40, bar down to the 95% rate")
    title(ax, "Margin at risk before each payment date",
          "Synthetic orders, seed 21. Gold: the order loses money inside the band.")
    fig.tight_layout()
    fig.savefig(IMG / "band.png")
    plt.close(fig)


def hedge() -> None:
    pos = generate(SEED)
    flagged = {r.po.po for r in run(pos, SPOT, VOL, TODAY) if r.flagged}
    fwd = {p.po: forward(SPOT, (p.due - TODAY).days) for p in pos}
    ps = paths(SPOT, VOL, TODAY, [p.due for p in pos], 2000, 1)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for name, hedged, col in (("no hedge", set(), GOLD_DIM),
                              ("flagged hedged", flagged, GOLD)):
        tot = [float(sum((p.margin(fwd[p.po] if p.po in hedged else path[p.due])
                          for p in pos), Decimal(0))) / 1e6 for path in ps]
        ax.hist(tot, bins=60, color=col, alpha=0.75, label=name)
    allm = float(sum((p.margin(fwd[p.po]) for p in pos), Decimal(0))) / 1e6
    ax.axvline(allm, color=TEXT, lw=1.5, label="all hedged (certain)")
    ax.set_xlabel("Total margin of the book (BRL million)")
    ax.set_ylabel("Paths out of 2,000")
    ax.legend(frameon=False)
    title(ax, "Total margin across seeded dollar paths",
          "Synthetic orders and paths, seed 21 and 1. Volatility 15% and carry 10% a year, "
          "both illustrative.")
    fig.tight_layout()
    fig.savefig(IMG / "hedge.png")
    plt.close(fig)


if __name__ == "__main__":
    style()
    hero()
    band()
    hedge()
    print("wrote", ", ".join(p.name for p in sorted(IMG.glob("*.png"))))

# Derivation

All amounts in BRL unless marked USD. Rates are BRL per USD.

## One order

An order buys `units` at a USD price `usd` (whole order), pays import duty `duty` on the
USD value and `other` BRL of freight, handling and taxes already fixed in reais, and sells
each unit at `sell`.

    exposure        = usd x (1 + duty)                 USD that move with the rate
    landed(r)       = exposure x r + other
    margin(r)       = units x sell - landed(r)
    per 1% move     = exposure x spot x 0.01
    break-even rate = (units x sell - other) / exposure, rounded down to 0.0001

Duty is charged on the converted value, so it moves with the rate and belongs in the
exposure. `other` does not.

### Hand-checked case (`tests/test_model.py`)

10,000 USD, duty 10%, other 2,000, 1,000 units sold at 70.00.

| Quantity | Working | Value |
|---|---|---:|
| exposure | 10,000 x 1.10 | 11,000 USD |
| margin at 5.40 | 70,000 - (11,000 x 5.40 + 2,000) = 70,000 - 61,400 | 8,600.00 |
| margin at 5.67 (+5%) | 70,000 - (62,370 + 2,000) | 5,630.00 |
| per 1% move at 5.40 | 11,000 x 5.40 x 0.01 | 594.00 |
| break-even | 68,000 / 11,000 = 6.18181... | 6.1818 |

Check: a 5% move is 5 x 594 = 2,970, and 8,600 - 2,970 = 5,630.

## The 95% band

The rate on the payment date is modelled as lognormal with annual volatility `vol` and no
drift. The rate that is exceeded with 5% probability, `t` days ahead, is approximately

    high = spot x exp(1.645 x vol x sqrt(t / 365))

(the small `-vol^2 t / 2` drift term is left out, which makes `high` slightly higher, on
the cautious side). An order is **flagged** when `margin(high) < 0`. Margin at risk is
`margin(spot) - margin(high)`.

Hand case (`tests/test_scenarios.py`): spot 5.40, vol 15%, 365 days:
1.645 x 0.15 = 0.24675, exp(0.24675) = 1.27986, 5.40 x 1.27986 = **6.9112**. The order
above breaks even at 6.1818 < 6.9112, so it is flagged if paid a year out.

## Hedging and the replay

A forward fixes the rate today for the payment date. It is priced with a simple carry:

    forward = spot x (1 + carry x days / 365)

With carry 10% and 73 days: 5.40 x (1 + 0.10 x 0.2) = 5.40 x 1.02 = **5.5080**.

The replay draws 2,000 seeded paths of the rate and reads each one on every payment date.
For each path, a hedged order uses its forward and an open order uses the path rate. Three
policies: hedge none, hedge the flagged orders, hedge all. For each it reports the mean
total margin, the total in the worst 5% of paths (the 100th of 2,000 when sorted), the
worst path and the mean number of orders sold at a loss.

Hedging all removes the spread completely but pays the carry on every order; hedging none
keeps the carry but takes the whole spread. Hedging flagged orders pays carry only where
the rate can turn an order into a loss.

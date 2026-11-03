import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from fx_exposure.__main__ import main
from fx_exposure.model import PO
from fx_exposure.report import render
from fx_exposure.scenarios import run


def test_example_scenarios_html(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pos, out, html = tmp_path / "pos.csv", tmp_path / "r.csv", tmp_path / "r.html"
    assert main(["example", str(pos)]) == 0
    assert main(["scenarios", str(pos), "--out", str(out), "--html", str(html)]) == 0
    text = capsys.readouterr().out
    assert "40 orders" in text and "18 lose money" in text
    rows = list(csv.DictReader(out.read_text().splitlines()))
    assert len(rows) == 40 and rows[0]["flagged"] in ("True", "False")
    page = html.read_text()
    assert page.count("<tr class=") == 40 and "<script" not in page
    assert main(["scenarios", str(pos)]) == 0


def test_simulate(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["simulate", "--paths", "50"]) == 0
    assert "flagged" in capsys.readouterr().out


def test_render_escapes_and_handles_empty(po: PO) -> None:
    bad = PO("<b>x</b>", "S", 1, Decimal(1), Decimal(0), Decimal(0), Decimal(9), Decimal(5),
             date(2026, 12, 1))
    page = render(run([bad], Decimal("5.40"), Decimal("0.15"), date(2026, 11, 3)),
                  Decimal("5.40"), Decimal("0.15"), date(2026, 11, 3), "t.csv")
    assert "&lt;b&gt;x&lt;/b&gt;" in page
    assert "0 of 0" in render([], Decimal("5.40"), Decimal("0.15"), date(2026, 11, 3), "e")

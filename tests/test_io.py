from pathlib import Path

import pytest

from fx_exposure.io import read_pos, write_pos, write_table
from fx_exposure.model import PO


def test_round_trip(tmp_path: Path, po: PO) -> None:
    f = tmp_path / "pos.csv"
    write_pos(f, [po, po])
    assert read_pos(f) == [po, po]
    t = tmp_path / "t.csv"
    write_table(t, ["a", "b"], [(1, "x")])
    assert t.read_text().splitlines() == ["a,b", "1,x"]


def test_errors(tmp_path: Path, po: PO) -> None:
    f = tmp_path / "pos.csv"
    f.write_text("po,sku\nA,B\n")
    with pytest.raises(ValueError, match="missing columns"):
        read_pos(f)
    write_pos(f, [po])
    f.write_text(f.read_text().replace("10000", "ten thousand"))
    with pytest.raises(ValueError, match="line 2"):
        read_pos(f)
    write_pos(f, [po])
    f.write_text(f.read_text().replace(",1000,", ",0,"))
    with pytest.raises(ValueError, match="line 2: PO-1"):
        read_pos(f)

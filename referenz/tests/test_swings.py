from helpers import bars_from_path
from mtref.bars import Bar
from mtref.swings import candle_swings


def test_zickzack_liefert_abwechselnde_wendepunkte():
    bars = bars_from_path([10, 40, 25, 60, 40])
    sw = candle_swings(bars, tick=0.01)
    assert [s.kind for s in sw] == ["L", "H", "L", "H"]
    assert [round(s.price, 1) for s in sw] == [9.8, 40.2, 24.8, 60.2]


def test_innenstab_bestaetigt_nicht():
    # Hoch-Kerze 1, danach Innenstab (Tief nicht unterschritten), erst Kerze 3 bestätigt
    b = [Bar(0, "0", 10, 11, 9, 10.5), Bar(1, "1", 10.5, 15, 12, 14),
         Bar(2, "2", 14, 14.5, 12.5, 13), Bar(3, "3", 13, 13.2, 11.9, 12)]
    sw = candle_swings(b, tick=0.1)
    assert sw[-1].kind == "H" and sw[-1].idx == 1 and sw[-1].confirm_idx == 3


def test_gleiches_tief_bestaetigt_nicht():
    # ENT-065: mindestens 1 Tick unter dem Tief der Hoch-Kerze
    b = [Bar(0, "0", 10, 11, 9, 10.5), Bar(1, "1", 10.5, 15, 12, 14), Bar(2, "2", 14, 14.2, 12.0, 12.5)]
    assert [s for s in candle_swings(b, tick=0.1) if s.kind == "H"] == []

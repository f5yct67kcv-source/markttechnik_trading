"""Die Skizzen aus docs/skizzen/ als automatische Tests."""
import pytest
from helpers import bars_from_path
from mtref.swings import candle_swings
from mtref.trend import run_trend, UP, DOWN, NONE

T = 0.01


def run(path):
    bars = bars_from_path(path)
    return run_trend(bars, candle_swings(bars, T), T)


def test_aufwaertstrend_entsteht_und_p3_wird_nachgezogen():
    s = run([10, 40, 25, 60, 45, 70])[-1]
    assert s.state == UP
    assert round(s.p3.price, 1) == 44.8          # erstes Korrekturtief nach P2 (ENT-038)
    assert round(s.p2.price, 1) == 70.2


def test_skizze_C_bruch_ohne_zwischenhoch_ist_blau():          # ENT-039/040 (D2)
    states = run([10, 40, 25, 60, 15])
    assert UP in [s.state for s in states]
    assert states[-1].state == NONE


def test_skizze_D1_bruch_nach_tieferem_hoch_ist_rot():          # ENT-039/040 (D1), ENT-041
    s = run([10, 40, 25, 60, 40, 52, 15])[-1]
    assert s.state == DOWN
    assert round(s.p1.price, 1) == 60.2 and round(s.p3.price, 1) == 52.2


def test_skizze_A_bruchlinie_ist_tief_X_nicht_tief_Z():         # ENT-038
    states = run([10, 40, 25, 60, 40, 52, 45, 50, 38])
    # vor dem Bruch lag die Bruchlinie auf Tief X (39.8), nicht auf Tief Z (44.8)
    up = [s for s in states if s.state == UP][-1]
    assert round(up.p3.price, 1) == 39.8
    assert states[-1].state == DOWN


def test_gleiches_tief_bricht_nicht():                          # ENT-037, Buch B-05
    s = run([10, 40, 25, 60, 25])[-1]
    assert s.state == UP


def test_skizze_E2_blau_nach_rot():                             # ENT-042/044
    s = run([10, 40, 25, 60, 20, 42, 12])[-1]
    assert s.state == DOWN
    assert round(s.p1.price, 1) == 60.2 and round(s.p3.price, 1) == 42.2


def test_skizze_E3_blau_nach_gruen_ohne_alten_p2():             # ENT-043/044
    s = run([10, 40, 25, 60, 20, 42, 30, 50])[-1]
    assert s.state == UP
    assert round(s.p1.price, 1) == 19.8 and round(s.p3.price, 1) == 29.8


def test_ent079_wieder_ueber_altem_p2_ist_gruen():
    s = run([10, 40, 25, 60, 20, 65])[-1]
    assert s.state == UP


def test_abwaertstrend_spiegelbildlich():
    s = run([60, 30, 45, 10, 30, 18, 55])[-1]
    assert s.state == UP                                       # D1 gespiegelt: direkt grün


from mtref.gwl import gwl_depth, gwl_compressed


def test_gwl_ignoriert_flache_ruecksetzer():                    # ENT-081
    # grosse Bewegung 10 -> 100 mit kleinen Rücksetzern (<20 %), dann tiefe Korrektur auf 55, dann weiter
    path = [10, 40, 35, 70, 63, 100, 85, 90, 55, 70, 62, 110]
    bars = bars_from_path(path, steps=8, wick=0.05)
    sig = candle_swings(bars, T)
    g = gwl_depth(bars, sig, thr=0.2, tick=T)
    assert [(s.kind, round(s.price)) for s in g] == [("L", 10), ("H", 100), ("L", 55)]
    s = run_trend(bars, g, T)[-1]
    assert s.state in (UP, NONE)


def test_gwl_verdichtung_liefert_wendepunkte():
    bars = bars_from_path([10, 40, 34, 70, 62, 100, 55, 110], steps=8)
    g = gwl_compressed(bars, k=4, tick=T)
    assert [x.kind for x in g][:3] == ["L", "H", "L"]


def test_gwl_v_korrektur_zaehlt():                              # ENT-077: Kurs fängt sich in einem Zug
    bars = bars_from_path([10, 40, 20, 60], steps=8, wick=0.05)
    g = gwl_depth(bars, candle_swings(bars, T), thr=0.2, tick=T)
    assert [(s.kind, round(s.price)) for s in g] == [("L", 10), ("H", 40), ("L", 20)]


def test_verspaetete_bestaetigung_holt_farbwechsel_nach():       # Live-Fehler MNQ 25.09.
    from mtref.swings import Swing
    bars = bars_from_path([10, 40, 25, 60, 20, 42, 12, 30], steps=4)
    sw = candle_swings(bars, T)
    # Hoch A (42) wird erst NACH dem Bruch unter 20 bestätigt
    late = [Swing(x.kind, x.idx, x.price, x.confirm_idx + (4 if round(x.price) == 42 else 0)) for x in sw]
    late.sort(key=lambda x: x.confirm_idx)
    s = run_trend(bars, late, T)[-1]
    assert s.state == DOWN and round(s.p1.price) == 60 and round(s.p3.price) == 42


def test_D1_mit_verspaetetem_hoch_Y_wird_rot():                  # Live-Fehler MCL 10 Min, 25.09.
    from mtref.swings import Swing
    bars = bars_from_path([10, 40, 25, 60, 40, 52, 15, 25], steps=4)
    sw = candle_swings(bars, T)
    # Hoch Y (52) wird erst nach dem Bruch unter Tief X (40) bestätigt
    late = [Swing(x.kind, x.idx, x.price, x.confirm_idx + (4 if round(x.price) == 52 else 0)) for x in sw]
    late.sort(key=lambda x: x.confirm_idx)
    s = run_trend(bars, late, T)[-1]
    assert s.state == DOWN and round(s.p1.price) == 60 and round(s.p3.price) == 52

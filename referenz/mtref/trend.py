"""Trendzustand einer Trendgrösse aus Kerzen + bestätigten Wendepunkten.

Zustände (ENT-013/016): UP = grün, DOWN = rot, NONE = blau (trendlos).
Die Logik ist für jede Ebene gleich; welche Wendepunkte sie bekommt
(Kerzen-Wendepunkte oder GWL-Punkte), entscheidet der Aufrufer (ENT-047).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .bars import Bar, high_first
from .swings import Swing

UP, DOWN, NONE = "UP", "DOWN", "NONE"


@dataclass
class Point:
    price: float
    idx: int


@dataclass
class TrendState:
    state: str = NONE
    p1: Point | None = None
    p2: Point | None = None
    p3: Point | None = None      # gültige Bruchlinie (ENT-037/038)


@dataclass
class _Ctx:
    s: TrendState = field(default_factory=TrendState)
    p3_open: bool = False        # neuer P2 erreicht, Korrektur läuft (Phase)
    corr: Swing | None = None    # Korrekturextrem nach P2 (Tief X) – wird P3 erst beim Bruch über P2 (ENT-095)
    counter: Swing | None = None # tieferes Hoch (UP) bzw. höheres Tief (DOWN) nach P2 (ENT-039/040)
    blue: list = field(default_factory=list)   # Wendepunkte seit Beginn der blauen Phase
    old_up_p2: float | None = None             # ENT-079
    old_down_p2: float | None = None
    ext_since_blue: Point | None = None        # Extrem seit dem Bruch (für ENT-079)


def run_trend(bars: list[Bar], swings: list[Swing], tick: float) -> list[TrendState]:
    by_confirm: dict[int, list[Swing]] = {}
    for sw in swings:
        by_confirm.setdefault(sw.confirm_idx, []).append(sw)

    c = _Ctx()
    out: list[TrendState] = []
    for bar in bars:
        for ev in (("H", "L") if high_first(bar) else ("L", "H")):
            _price_event(c, ev, bar, tick)
        for sw in by_confirm.get(bar.idx, []):
            _swing_event(c, sw, tick)
            _late_check(c, bars, bar.idx, tick)
        out.append(TrendState(c.s.state, c.s.p1, c.s.p2, c.s.p3))
    return out


def _go(c: _Ctx, state: str, p1: Point, p2: Point, p3: Point) -> None:
    c.s = TrendState(state, p1, p2, p3)
    c.p3_open, c.counter, c.corr, c.blue = False, None, None, []
    c.old_up_p2 = c.old_down_p2 = None
    c.ext_since_blue = None


def _go_blue(c: _Ctx, bar: Bar, ev: str) -> None:
    old, corr = c.s, c.corr
    c.s = TrendState(NONE)
    c.p3_open, c.counter, c.corr = False, None, None
    # Letztes Extrem des gebrochenen Trends ist der erste Punkt der blauen Phase (Skizze E2/E3).
    if old.state == UP:
        c.old_up_p2, c.old_down_p2 = old.p2.price, None
        c.blue = [Swing("H", old.p2.idx, old.p2.price, bar.idx)]
        if corr is not None:                         # Tief X nach P2 bleibt Teil der Struktur (ENT-092)
            c.blue.append(corr)
        c.ext_since_blue = Point(bar.low, bar.idx)
    else:
        c.old_down_p2, c.old_up_p2 = old.p2.price, None
        c.blue = [Swing("L", old.p2.idx, old.p2.price, bar.idx)]
        if corr is not None:
            c.blue.append(corr)
        c.ext_since_blue = Point(bar.high, bar.idx)


def _price_event(c: _Ctx, ev: str, bar: Bar, tick: float) -> None:
    s = c.s
    if s.state == UP:
        if ev == "H" and bar.high >= s.p2.price + tick:          # ENT-035
            if c.corr is not None:                                # ENT-095: P3 erst beim Bruch über P2
                s.p3 = Point(c.corr.price, c.corr.idx)
            s.p2 = Point(bar.high, bar.idx)
            c.p3_open, c.counter, c.corr = True, None, None
        elif ev == "L" and bar.low <= s.p3.price - tick:         # ENT-037
            if c.counter is not None:                             # ENT-039/040 (D1): direkt rot
                _go(c, DOWN, Point(s.p2.price, s.p2.idx), Point(bar.low, bar.idx),
                    Point(c.counter.price, c.counter.idx))
            else:                                                 # Skizze C/D2: blau
                _go_blue(c, bar, ev)
    elif s.state == DOWN:
        if ev == "L" and bar.low <= s.p2.price - tick:
            if c.corr is not None:
                s.p3 = Point(c.corr.price, c.corr.idx)
            s.p2 = Point(bar.low, bar.idx)
            c.p3_open, c.counter, c.corr = True, None, None
        elif ev == "H" and bar.high >= s.p3.price + tick:
            if c.counter is not None:
                _go(c, UP, Point(s.p2.price, s.p2.idx), Point(bar.high, bar.idx),
                    Point(c.counter.price, c.counter.idx))
            else:
                _go_blue(c, bar, ev)
    else:
        _blue_price_event(c, ev, bar, tick)


def _blue_price_event(c: _Ctx, ev: str, bar: Bar, tick: float) -> None:
    e = c.ext_since_blue
    if e is not None:
        if c.old_up_p2 is not None and ev == "L" and bar.low < e.price:
            c.ext_since_blue = Point(bar.low, bar.idx)
        if c.old_down_p2 is not None and ev == "H" and bar.high > e.price:
            c.ext_since_blue = Point(bar.high, bar.idx)
    # ENT-079: wieder über den alten P2 -> grün (Abwärts spiegelbildlich)
    if ev == "H" and c.old_up_p2 is not None and bar.high >= c.old_up_p2 + tick:
        low = c.ext_since_blue
        p3 = next((Point(w.price, w.idx) for w in reversed(c.blue) if w.kind == "L" and w.price > low.price), low)
        _go(c, UP, low, Point(bar.high, bar.idx), p3)
        return
    if ev == "L" and c.old_down_p2 is not None and bar.low <= c.old_down_p2 - tick:
        high = c.ext_since_blue
        p3 = next((Point(w.price, w.idx) for w in reversed(c.blue) if w.kind == "H" and w.price < high.price), high)
        _go(c, DOWN, high, Point(bar.low, bar.idx), p3)
        return
    # ENT-042/043 bzw. allgemeiner Trendaufbau aus blau: Tief, Hoch, höheres Tief, über das Hoch -> grün
    w = c.blue
    if len(w) >= 3:
        a, b, d = w[-3], w[-2], w[-1]
        if ev == "H" and (a.kind, b.kind, d.kind) == ("L", "H", "L") and d.price >= a.price + tick \
                and bar.high >= b.price + tick:
            _go(c, UP, Point(a.price, a.idx), Point(bar.high, bar.idx), Point(d.price, d.idx))
        elif ev == "L" and (a.kind, b.kind, d.kind) == ("H", "L", "H") and d.price <= a.price - tick \
                and bar.low <= b.price - tick:
            _go(c, DOWN, Point(a.price, a.idx), Point(bar.low, bar.idx), Point(d.price, d.idx))


def _swing_event(c: _Ctx, sw: Swing, tick: float) -> None:
    s = c.s
    if s.state in (UP, DOWN):
        up = s.state == UP
        corr_kind, peak_kind = ("L", "H") if up else ("H", "L")
        better = (lambda a, b: a < b) if up else (lambda a, b: a > b)   # extremer in Korrekturrichtung
        if sw.kind == corr_kind and sw.idx > s.p2.idx:
            if c.corr is None or better(sw.price, c.corr.price):
                c.corr = sw                                        # Tief X (wartet auf Bruch über P2)
        elif sw.kind == corr_kind and s.p3.idx < sw.idx < s.p2.idx and better(s.p3.price, sw.price):
            s.p3 = Point(sw.price, sw.idx)                         # nachträglich bestätigtes Korrekturextrem vor P2
        elif sw.kind == peak_kind and sw.idx > s.p2.idx and \
                (sw.price <= s.p2.price - tick if up else sw.price >= s.p2.price + tick):
            c.counter = sw                                         # tieferes Hoch / höheres Tief (Hoch Y)
    else:
        if c.blue and c.blue[-1].kind == sw.kind:                  # gleiche Art: extremeren behalten
            last = c.blue[-1]
            if (sw.kind == "H" and sw.price > last.price) or (sw.kind == "L" and sw.price < last.price):
                c.blue[-1] = sw
        else:
            c.blue.append(sw)


def _late_check(c: _Ctx, bars: list[Bar], now: int, tick: float) -> None:
    """Wendepunkte werden oft erst nachträglich bestätigt (ENT-083/088). Hat der Kurs
    die Bedingung für einen Trendaufbau aus blau (ENT-042/043) schon vorher erfüllt,
    wird der Wechsel jetzt nachgeholt – mit dem bisherigen Extrem als P2."""
    if c.s.state != NONE or len(c.blue) < 3:
        return
    a, b, d = c.blue[-3], c.blue[-2], c.blue[-1]
    seit = bars[d.idx + 1:now + 1]
    if not seit:
        return
    if (a.kind, b.kind, d.kind) == ("L", "H", "L") and d.price >= a.price + tick:
        hi = max(seit, key=lambda x: x.high)
        if hi.high >= b.price + tick:
            _go(c, UP, Point(a.price, a.idx), Point(hi.high, hi.idx), Point(d.price, d.idx))
    elif (a.kind, b.kind, d.kind) == ("H", "L", "H") and d.price <= a.price - tick:
        lo = min(seit, key=lambda x: x.low)
        if lo.low <= b.price - tick:
            _go(c, DOWN, Point(a.price, a.idx), Point(lo.low, lo.idx), Point(d.price, d.idx))

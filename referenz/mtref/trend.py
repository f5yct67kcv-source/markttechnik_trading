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
    p3_open: bool = False        # erstes Korrekturextrem nach neuem P2 darf P3 werden (ENT-038)
    counter: Swing | None = None # tieferes Hoch (UP) bzw. höheres Tief (DOWN) nach P3 (ENT-039/040)
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
        out.append(TrendState(c.s.state, c.s.p1, c.s.p2, c.s.p3))
    return out


def _go(c: _Ctx, state: str, p1: Point, p2: Point, p3: Point) -> None:
    c.s = TrendState(state, p1, p2, p3)
    c.p3_open, c.counter, c.blue = False, None, []
    c.old_up_p2 = c.old_down_p2 = None
    c.ext_since_blue = None


def _go_blue(c: _Ctx, bar: Bar, ev: str) -> None:
    old = c.s
    c.s = TrendState(NONE)
    c.p3_open, c.counter = False, None
    # Letztes Extrem des gebrochenen Trends ist der erste Punkt der blauen Phase (Skizze E2/E3).
    if old.state == UP:
        c.old_up_p2, c.old_down_p2 = old.p2.price, None
        c.blue = [Swing("H", old.p2.idx, old.p2.price, bar.idx)]
        c.ext_since_blue = Point(bar.low, bar.idx)
    else:
        c.old_down_p2, c.old_up_p2 = old.p2.price, None
        c.blue = [Swing("L", old.p2.idx, old.p2.price, bar.idx)]
        c.ext_since_blue = Point(bar.high, bar.idx)


def _price_event(c: _Ctx, ev: str, bar: Bar, tick: float) -> None:
    s = c.s
    if s.state == UP:
        if ev == "H" and bar.high >= s.p2.price + tick:          # ENT-035
            s.p2 = Point(bar.high, bar.idx)
            c.p3_open, c.counter = True, None
        elif ev == "L" and bar.low <= s.p3.price - tick:         # ENT-037
            if c.counter is not None:                             # ENT-039/040 (D1): direkt rot
                _go(c, DOWN, Point(s.p2.price, s.p2.idx), Point(bar.low, bar.idx),
                    Point(c.counter.price, c.counter.idx))
            else:                                                 # Skizze C/D2: blau
                _go_blue(c, bar, ev)
    elif s.state == DOWN:
        if ev == "L" and bar.low <= s.p2.price - tick:
            s.p2 = Point(bar.low, bar.idx)
            c.p3_open, c.counter = True, None
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
    if s.state == UP:
        if sw.kind == "L" and c.p3_open and sw.idx > s.p2.idx:    # ENT-038: erstes Korrekturtief nach P2
            s.p3 = Point(sw.price, sw.idx)
            c.p3_open, c.counter = False, None
        elif sw.kind == "H" and sw.idx > s.p3.idx and sw.price <= s.p2.price - tick:
            c.counter = sw                                         # tieferes Hoch (Hoch Y)
    elif s.state == DOWN:
        if sw.kind == "H" and c.p3_open and sw.idx > s.p2.idx:
            s.p3 = Point(sw.price, sw.idx)
            c.p3_open, c.counter = False, None
        elif sw.kind == "L" and sw.idx > s.p3.idx and sw.price >= s.p2.price + tick:
            c.counter = sw
    else:
        if c.blue and c.blue[-1].kind == sw.kind:                  # gleiche Art: extremeren behalten
            last = c.blue[-1]
            if (sw.kind == "H" and sw.price > last.price) or (sw.kind == "L" and sw.price < last.price):
                c.blue[-1] = sw
        else:
            c.blue.append(sw)

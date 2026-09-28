"""Trendzustand einer Trendgrösse aus Kerzen + bestätigten Wendepunkten.

Zustände (ENT-013/016): UP = grün, DOWN = rot, NONE = blau (trendlos).
Die Logik ist für jede Ebene gleich; welche Wendepunkte sie bekommt
(gefilterte Kerzen-Wendepunkte oder GWL-Punkte), entscheidet der Aufrufer (ENT-047/101).

Zusätzlich führt die Maschine die **Trendstruktur** (ENT-102): die Liste der
endgültigen Punkte, aus denen die Zickzacklinie der Grösse gezeichnet wird.
Nur 1-2-3-Punkte (und die Wendepunkte der blauen Phase) sind Strukturpunkte;
innere Schwankungen einer Korrektur werden nicht gezeichnet.
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
    p3: Point | None = None      # gültige Bruchlinie (ENT-037/095)
    korr: bool = False           # Phase: True = Korrektur, False = Bewegung (ENT-097)
    reason: str = ""             # Grund des letzten Zustandswechsels (ENT-100)


@dataclass
class SPoint:
    """Endgültiger Strukturpunkt der Zickzacklinie (ENT-102)."""
    kind: str                    # "H" / "L"
    idx: int
    price: float
    state: str                   # Trendzustand beim Festschreiben (Farbe, ENT-016)


@dataclass
class _Ctx:
    s: TrendState = field(default_factory=TrendState)
    p3_open: bool = False        # neuer P2 erreicht, Korrektur läuft (Phase)
    corr: Swing | None = None    # Korrekturextrem nach P2 (Tief X) – wird P3 erst beim Bruch über P2 (ENT-095)
    corr_from: int | None = None # Kerze des vorherigen P2 = Beginn der letzten Korrektur (ENT-099)
    corr_from_p: float | None = None
    korr: bool = False           # Phase Korrektur (ENT-097)
    reason: str = ""
    counter: Swing | None = None # tieferes Hoch (UP) bzw. höheres Tief (DOWN) nach P2 (ENT-039/040)
    after: list = field(default_factory=list)  # bestätigte Wendepunkte seit P2 (für die Struktur beim D1-Wechsel)
    blue: list = field(default_factory=list)   # Wendepunkte seit Beginn der blauen Phase
    old_up_p2: float | None = None             # ENT-079
    old_down_p2: float | None = None
    ext_since_blue: Point | None = None        # Extrem seit dem Bruch (für ENT-079)
    struct: list = field(default_factory=list) # Strukturpunkte (ENT-102)


def run_trend(bars: list[Bar], swings: list[Swing], tick: float) -> list[TrendState]:
    return run_trend_struct(bars, swings, tick)[0]


def run_trend_struct(bars: list[Bar], swings: list[Swing], tick: float):
    """Liefert (Zustand je Kerze, Strukturpunkte am Ende)."""
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
        out.append(TrendState(c.s.state, c.s.p1, c.s.p2, c.s.p3, c.korr, c.reason))
    return out, c.struct


# ───────────────────────────── Struktur (ENT-102)
def _s_last(c: _Ctx) -> SPoint | None:
    return c.struct[-1] if c.struct else None


def _s_push(c: _Ctx, kind: str, idx: int, price: float) -> None:
    last = _s_last(c)
    if last is not None and last.idx == idx and last.kind == kind:
        return
    if last is not None and last.kind == kind:                 # gleiche Art: extremeren behalten
        if (kind == "H" and price >= last.price) or (kind == "L" and price <= last.price):
            c.struct[-1] = SPoint(kind, idx, price, c.s.state)
        return
    c.struct.append(SPoint(kind, idx, price, c.s.state))


def _s_replace_last(c: _Ctx, kind: str, idx: int, price: float) -> None:
    last = _s_last(c)
    if last is not None and last.kind == kind:
        c.struct[-1] = SPoint(kind, idx, price, c.s.state)
    else:
        c.struct.append(SPoint(kind, idx, price, c.s.state))


# ───────────────────────────── Zustandswechsel
def _go(c: _Ctx, state: str, p1: Point, p2: Point, p3: Point, reason: str = "") -> None:
    c.s = TrendState(state, p1, p2, p3)
    c.p3_open, c.counter, c.corr, c.blue, c.after = False, None, None, [], []
    c.corr_from, c.corr_from_p, c.korr, c.reason = None, None, False, reason   # Trend beginnt mit einer Bewegung
    c.old_up_p2 = c.old_down_p2 = None
    c.ext_since_blue = None


def _go_blue(c: _Ctx, bar: Bar, ev: str, reason: str = "") -> None:
    old, corr = c.s, c.corr
    c.s = TrendState(NONE)
    c.p3_open, c.counter, c.corr, c.after = False, None, None, []
    c.corr_from, c.corr_from_p, c.korr, c.reason = None, None, False, reason
    # Letztes Extrem des gebrochenen Trends ist der erste Punkt der blauen Phase (Skizze E2/E3).
    if old.state == UP:
        c.old_up_p2, c.old_down_p2 = old.p2.price, None
        c.blue = [Swing("H", old.p2.idx, old.p2.price, bar.idx)]
        _s_push(c, "H", old.p2.idx, old.p2.price)
        if corr is not None:                         # Tief X nach P2 bleibt Teil der Struktur (ENT-092)
            c.blue.append(corr)
            _s_push(c, "L", corr.idx, corr.price)
        c.ext_since_blue = Point(bar.low, bar.idx)
    else:
        c.old_down_p2, c.old_up_p2 = old.p2.price, None
        c.blue = [Swing("L", old.p2.idx, old.p2.price, bar.idx)]
        _s_push(c, "L", old.p2.idx, old.p2.price)
        if corr is not None:
            c.blue.append(corr)
            _s_push(c, "H", corr.idx, corr.price)
        c.ext_since_blue = Point(bar.high, bar.idx)


def _p2_break(c: _Ctx, bar: Bar, up: bool) -> None:
    """Neues Bewegungsextrem über/unter P2 (ENT-035). Alter P2 und Korrekturextrem
    werden Strukturpunkte, wenn eine Korrektur stattgefunden hat (ENT-095/102)."""
    s = c.s
    peak, corr_kind = ("H", "L") if up else ("L", "H")
    if c.korr or c.corr is not None:
        _s_push(c, peak, s.p2.idx, s.p2.price)
        if c.corr is not None:                                    # ENT-095: P3 erst beim Bruch über P2
            s.p3 = Point(c.corr.price, c.corr.idx)
            _s_push(c, corr_kind, c.corr.idx, c.corr.price)
        c.corr_from, c.corr_from_p = s.p2.idx, s.p2.price          # Beginn der Korrektur (ENT-099)
    c.korr = False                                                # Bruch über P2 = neue Bewegung (ENT-097)
    s.p2 = Point(bar.high if up else bar.low, bar.idx)
    c.p3_open, c.counter, c.corr, c.after = True, None, None, []


def _d1(c: _Ctx, bar: Bar, up: bool) -> None:
    """Bruch des alten P3 nach Gegen-Wendepunkt: direkter Gegentrend (ENT-039/040, D1)."""
    s, y = c.s, c.counter
    peak, corr_kind = ("H", "L") if up else ("L", "H")
    _s_push(c, peak, s.p2.idx, s.p2.price)                        # P1 des Gegentrends
    between = [w for w in c.after if w.kind == corr_kind and w.idx < y.idx]
    if between:                                                   # Extrem zwischen P1 und P3 (unnummeriert)
        w = min(between, key=lambda w: w.price) if up else max(between, key=lambda w: w.price)
        _s_push(c, corr_kind, w.idx, w.price)
    reason = (f"Bruch P3 {s.p3.price:g} nach tieferem Hoch {y.price:g} (D1)" if up
              else f"Bruch P3 {s.p3.price:g} nach höherem Tief {y.price:g} (D1)")
    _go(c, DOWN if up else UP, Point(s.p2.price, s.p2.idx),
        Point(bar.low if up else bar.high, bar.idx), Point(y.price, y.idx), reason)
    _s_push(c, peak, y.idx, y.price)                              # P3 des Gegentrends


def _price_event(c: _Ctx, ev: str, bar: Bar, tick: float) -> None:
    s = c.s
    if s.state == UP:
        if ev == "H" and bar.high >= s.p2.price + tick:          # ENT-035
            _p2_break(c, bar, True)
        elif ev == "L" and bar.low <= s.p3.price - tick:         # ENT-037
            if c.counter is not None:
                _d1(c, bar, True)
            else:                                                 # Skizze C/D2: blau
                _go_blue(c, bar, ev, f"Bruch P3 {s.p3.price:g} ohne tieferes Hoch")
    elif s.state == DOWN:
        if ev == "L" and bar.low <= s.p2.price - tick:
            _p2_break(c, bar, False)
        elif ev == "H" and bar.high >= s.p3.price + tick:
            if c.counter is not None:
                _d1(c, bar, False)
            else:
                _go_blue(c, bar, ev, f"Bruch P3 {s.p3.price:g} ohne höheres Tief")
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
        low = c.ext_since_blue                                     # ENT-098: P1 = Tief seit dem Bruch, P3 = P1
        p3 = next((Point(w.price, w.idx) for w in reversed(c.blue)
                   if w.kind == "L" and w.idx > low.idx and w.price > low.price), low)
        _go(c, UP, low, Point(bar.high, bar.idx), p3, f"über alten P2 {c.old_up_p2:g} (ENT-079)")
        _s_replace_last(c, "L", low.idx, low.price)
        return
    if ev == "L" and c.old_down_p2 is not None and bar.low <= c.old_down_p2 - tick:
        high = c.ext_since_blue
        p3 = next((Point(w.price, w.idx) for w in reversed(c.blue)
                   if w.kind == "H" and w.idx > high.idx and w.price < high.price), high)
        _go(c, DOWN, high, Point(bar.low, bar.idx), p3, f"unter alten P2 {c.old_down_p2:g} (ENT-079)")
        _s_replace_last(c, "H", high.idx, high.price)
        return
    # ENT-042/043 bzw. allgemeiner Trendaufbau aus blau: Tief, Hoch, höheres Tief, über das Hoch -> grün
    w = c.blue
    if len(w) >= 3:
        a, b, d = w[-3], w[-2], w[-1]
        if ev == "H" and (a.kind, b.kind, d.kind) == ("L", "H", "L") and d.price >= a.price + tick \
                and bar.high >= b.price + tick:
            _go(c, UP, Point(a.price, a.idx), Point(bar.high, bar.idx), Point(d.price, d.idx),
                f"1-2-3 aus blau: über Hoch {b.price:g}")
        elif ev == "L" and (a.kind, b.kind, d.kind) == ("H", "L", "H") and d.price <= a.price - tick \
                and bar.low <= b.price - tick:
            _go(c, DOWN, Point(a.price, a.idx), Point(bar.low, bar.idx), Point(d.price, d.idx),
                f"1-2-3 aus blau: unter Tief {b.price:g}")


def _swing_event(c: _Ctx, sw: Swing, tick: float) -> None:
    s = c.s
    if s.state in (UP, DOWN):
        up = s.state == UP
        corr_kind, peak_kind = ("L", "H") if up else ("H", "L")
        better = (lambda a, b: a < b) if up else (lambda a, b: a > b)   # extremer in Korrekturrichtung
        if sw.idx >= s.p2.idx:
            c.korr = True                                          # erster bestätigter Wendepunkt nach P2 (ENT-097)
        if sw.idx > s.p2.idx:
            if c.after and c.after[-1].kind == sw.kind:
                last = c.after[-1]
                if (sw.kind == "H" and sw.price > last.price) or (sw.kind == "L" and sw.price < last.price):
                    c.after[-1] = sw
            else:
                c.after.append(sw)
        if sw.kind == corr_kind and sw.idx > s.p2.idx:
            if c.corr is None or better(sw.price, c.corr.price):
                c.corr = sw                                        # Tief X (wartet auf Bruch über P2)
        elif sw.kind == corr_kind and c.corr_from is not None and c.corr_from < sw.idx < s.p2.idx \
                and (s.p3.idx <= c.corr_from or better(sw.price, s.p3.price)):
            s.p3 = Point(sw.price, sw.idx)                         # nachträglich bestätigt: tiefstes Tief der Korrektur (ENT-099)
            _s_push(c, peak_kind, c.corr_from, c.corr_from_p)     # alter P2 als Strukturpunkt, falls noch nicht
            _s_replace_last(c, corr_kind, sw.idx, sw.price)
        elif sw.kind == peak_kind and sw.idx > s.p2.idx and \
                (sw.price <= s.p2.price - tick if up else sw.price >= s.p2.price + tick):
            c.counter = sw                                         # tieferes Hoch / höheres Tief (Hoch Y)
    else:
        if c.blue and c.blue[-1].kind == sw.kind:                  # gleiche Art: extremeren behalten
            last = c.blue[-1]
            if (sw.kind == "H" and sw.price > last.price) or (sw.kind == "L" and sw.price < last.price):
                c.blue[-1] = sw
                _s_replace_last(c, sw.kind, sw.idx, sw.price)
        else:
            c.blue.append(sw)
            _s_push(c, sw.kind, sw.idx, sw.price)


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
            _go(c, UP, Point(a.price, a.idx), Point(hi.high, hi.idx), Point(d.price, d.idx),
                f"1-2-3 aus blau (nachgeholt): über Hoch {b.price:g}")
    elif (a.kind, b.kind, d.kind) == ("H", "L", "H") and d.price <= a.price - tick:
        lo = min(seit, key=lambda x: x.low)
        if lo.low <= b.price - tick:
            _go(c, DOWN, Point(a.price, a.idx), Point(lo.low, lo.idx), Point(d.price, d.idx),
                f"1-2-3 aus blau (nachgeholt): unter Tief {b.price:g}")

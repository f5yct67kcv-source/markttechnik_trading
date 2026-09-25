"""Unterste Ebene: Wendepunkte direkt aus den Kerzen (Kerzenregel ENT-065)."""
from __future__ import annotations

from dataclasses import dataclass

from .bars import Bar, high_first


@dataclass(frozen=True)
class Swing:
    kind: str          # "H" oder "L"
    idx: int           # Kerze des Extrems
    price: float
    confirm_idx: int   # Kerze, in der das Extrem als Wendepunkt feststeht


def candle_swings(bars: list[Bar], tick: float) -> list[Swing]:
    """ENT-065: Ein Hoch steht fest, sobald eine spätere Kerze das Tief der
    Hoch-Kerze um mindestens 1 Tick unterschreitet. Tief spiegelbildlich.
    Kerzen dazwischen (z. B. Innenstäbe) zählen nicht.
    Reihenfolge innerhalb einer Kerze nach ENT-024."""
    swings: list[Swing] = []
    if not bars:
        return swings
    direction = None      # None = noch kein Wendepunkt, "up" = sucht Hoch, "down" = sucht Tief
    hi = lo = bars[0]     # Kerze mit höchstem Hoch / tiefstem Tief im laufenden Ast

    for bar in bars[1:]:
        for ev in (("H", "L") if high_first(bar) else ("L", "H")):
            if ev == "H":
                if direction != "down" and bar.high > hi.high:
                    hi = bar
                if direction != "up" and bar.idx > lo.idx and bar.high >= lo.high + tick:
                    swings.append(Swing("L", lo.idx, lo.low, bar.idx))
                    direction, hi = "up", bar
            else:
                if direction != "up" and bar.low < lo.low:
                    lo = bar
                if direction != "down" and bar.idx > hi.idx and bar.low <= hi.low - tick:
                    swings.append(Swing("H", hi.idx, hi.high, bar.idx))
                    direction, lo = "down", bar
    return swings

"""Kerzen laden und verdichten."""
from __future__ import annotations

import csv
import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class Bar:
    idx: int
    time: str
    open: float
    high: float
    low: float
    close: float


def load_tradingview_csv(path: str) -> list[Bar]:
    """TradingView-Export („Chart-Daten exportieren“): Spalten time, open, high, low, close, ..."""
    bars: list[Bar] = []
    with open(path, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            r = {k.strip().lower(): v for k, v in row.items()}
            t = r["time"]
            if t.isdigit():                                   # Unix-Zeit (TradingView-Export)
                t = datetime.datetime.fromtimestamp(int(t), datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
            bars.append(Bar(i, t, float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"])))
    return bars


def compress(bars: list[Bar], k: int) -> tuple[list[Bar], list[int]]:
    """Fasst je k Kerzen zu einer zusammen (Verdichtung, ENT-005/007).

    Liefert die verdichteten Kerzen und je verdichteter Kerze den Index der
    ersten Originalkerze (für die Rückprojektion).
    """
    out: list[Bar] = []
    starts: list[int] = []
    for j in range(0, len(bars), k):
        chunk = bars[j:j + k]
        out.append(Bar(len(out), chunk[0].time, chunk[0].open,
                       max(b.high for b in chunk), min(b.low for b in chunk), chunk[-1].close))
        starts.append(j)
    return out, starts


def high_first(bar: Bar) -> bool:
    """Reihenfolge innerhalb einer historischen Kerze (ENT-024):
    das Extrem näher am Eröffnungskurs gilt als zuerst erreicht."""
    return (bar.high - bar.open) <= (bar.open - bar.low)

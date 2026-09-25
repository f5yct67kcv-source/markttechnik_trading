"""Zeichnet Signallage (fein) und GWL (dick) für einen TradingView-CSV-Export.

Aufruf:
  python tools/vergleich.py DATEI.csv --tick 0.01 --variante A --schwelle 0.3 --out bild.png
  python tools/vergleich.py DATEI.csv --tick 0.01 --variante B --k 6 --out bild.png
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from mtref.bars import load_tradingview_csv
from mtref.gwl import gwl_compressed, gwl_depth, gwl_higher_tf, session_groups
from mtref.swings import candle_swings
from mtref.trend import DOWN, UP, run_trend

FARBE = {UP: "#1a9641", DOWN: "#d7191c", "NONE": "#2b6cb0"}


def zeichne_zickzack(ax, swings, states, lw, ls):
    for a, b in zip(swings, swings[1:]):
        ax.plot([a.idx, b.idx], [a.price, b.price], color=FARBE[states[b.idx].state], lw=lw, ls=ls)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--tick", type=float, required=True)
    ap.add_argument("--variante", choices=["A", "B", "C"], default="A")
    ap.add_argument("--schwelle", type=float, default=0.3)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--von", default="")
    ap.add_argument("--out", default="vergleich.png")
    a = ap.parse_args()

    bars = load_tradingview_csv(a.csv)
    sig = candle_swings(bars, a.tick)
    sig_states = run_trend(bars, sig, a.tick)
    laufend: list = []
    if a.variante == "A":
        gwl = gwl_depth(bars, sig, a.schwelle, a.tick, laufend)
    elif a.variante == "B":
        gwl = gwl_compressed(bars, a.k, a.tick)
    else:
        gwl = gwl_higher_tf(bars, session_groups(bars), a.schwelle, a.tick)
    gwl_states = run_trend(bars, gwl, a.tick)

    start = next((b.idx for b in bars if b.time >= a.von), 0)
    sig = [x for x in sig if x.idx >= start]
    gwl = [x for x in gwl if x.idx >= start] if len([x for x in gwl if x.idx >= start]) else gwl
    fig, ax = plt.subplots(figsize=(20, 10))
    for b in bars[start:]:
        c = "#26a69a" if b.close >= b.open else "#ef5350"
        ax.vlines(b.idx, b.low, b.high, color=c, lw=0.6)
        ax.vlines(b.idx, min(b.open, b.close), max(b.open, b.close), color=c, lw=2.2)
    zeichne_zickzack(ax, sig, sig_states, 1.0, "--")
    zeichne_zickzack(ax, gwl, gwl_states, 4.0, "-")
    if gwl and not laufend:                               # laufender Ast bis zum aktuellen Extrem
        last = gwl[-1]
        rest = bars[last.idx + 1:]
        if rest:
            e = max(rest, key=lambda b: b.high) if last.kind == "L" else min(rest, key=lambda b: b.low)
            laufend = [type(last)("H" if last.kind == "L" else "L", e.idx, e.high if last.kind == "L" else e.low, e.idx)]
    if gwl and laufend:                                   # laufender, unbestätigter Ast
        pts = [gwl[-1]] + laufend
        for x, y in zip(pts, pts[1:]):
            ax.plot([x.idx, y.idx], [x.price, y.price], color=FARBE[gwl_states[-1].state], lw=4.0, alpha=0.45)
    s = gwl_states[-1]
    info = f"GWL {s.state}  P1 {s.p1.price if s.p1 else '-'}  P2 {s.p2.price if s.p2 else '-'}  P3 {s.p3.price if s.p3 else '-'}"
    info += f"   |   Signal {sig_states[-1].state}   |   Variante {a.variante}"
    ax.set_title(info, loc="left")
    step = max(1, len(bars) // 12)
    step = max(1, (len(bars) - start) // 12)
    ax.set_xticks(range(start, len(bars), step), [bars[i].time[:10] for i in range(start, len(bars), step)], rotation=30)
    ax.set_xlim(start - 2, len(bars) + 2)
    fig.tight_layout()
    fig.savefig(a.out, dpi=100)
    print(info)


if __name__ == "__main__":
    main()

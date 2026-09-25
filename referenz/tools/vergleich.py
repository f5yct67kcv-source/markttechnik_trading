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
from mtref.gwl import gwl_compressed, gwl_depth
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
    ap.add_argument("--variante", choices=["A", "B"], default="A")
    ap.add_argument("--schwelle", type=float, default=0.3)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--out", default="vergleich.png")
    a = ap.parse_args()

    bars = load_tradingview_csv(a.csv)
    sig = candle_swings(bars, a.tick)
    sig_states = run_trend(bars, sig, a.tick)
    laufend: list = []
    gwl = gwl_depth(bars, sig, a.schwelle, a.tick, laufend) if a.variante == "A" else gwl_compressed(bars, a.k, a.tick)
    gwl_states = run_trend(bars, gwl, a.tick)

    fig, ax = plt.subplots(figsize=(20, 10))
    for b in bars:
        c = "#26a69a" if b.close >= b.open else "#ef5350"
        ax.vlines(b.idx, b.low, b.high, color=c, lw=0.6)
        ax.vlines(b.idx, min(b.open, b.close), max(b.open, b.close), color=c, lw=2.2)
    zeichne_zickzack(ax, sig, sig_states, 1.0, "--")
    zeichne_zickzack(ax, gwl, gwl_states, 4.0, "-")
    if gwl and laufend:                                   # laufender, unbestätigter Ast
        pts = [gwl[-1]] + laufend
        for x, y in zip(pts, pts[1:]):
            ax.plot([x.idx, y.idx], [x.price, y.price], color=FARBE[gwl_states[-1].state], lw=4.0, alpha=0.45)
    s = gwl_states[-1]
    info = f"GWL {s.state}  P1 {s.p1.price if s.p1 else '-'}  P2 {s.p2.price if s.p2 else '-'}  P3 {s.p3.price if s.p3 else '-'}"
    info += f"   |   Signal {sig_states[-1].state}   |   Variante {a.variante}"
    ax.set_title(info, loc="left")
    step = max(1, len(bars) // 12)
    ax.set_xticks(range(0, len(bars), step), [bars[i].time[:10] for i in range(0, len(bars), step)], rotation=30)
    fig.tight_layout()
    fig.savefig(a.out, dpi=100)
    print(info)


if __name__ == "__main__":
    main()

"""Trefferquote: Agena-Soll-Punkte (aus Screenshots) gegen eine Referenz-Methode (ENT-120).

Soll-Datei: CSV mit Spalten kind,price (H/L, Preis abgelesen), chronologisch.
Abgleich der Reihe nach, Toleranz in Preis-Einheiten. Ausgabe: Treffer, fehlende, zusätzliche Punkte.
Aufruf: python soll_vergleich.py <kurse.csv> <tick> <soll.csv> <von> <bis> <toleranz>
"""
import csv, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tests"))
from mtref.bars import load_tradingview_csv
from mtref.swings import candle_swings
from mtref.gwl import causal_depth, htf_swings, htf_swings_growing, domino
from mtref.trend import run_trend
from test_testfaelle import groups_min

kurse, tick, sollf, von, bis, tol = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5], float(sys.argv[6])
b = load_tradingview_csv(kurse)
soll = [(r["kind"], float(r["price"])) for r in csv.DictReader(open(sollf))]

def score(name, pts):
    ist = [(p.kind, p.price, b[p.idx].time[-5:]) for p in pts if von <= b[p.idx].time <= bis]
    i = j = hit = 0
    miss, extra = [], []
    while i < len(soll) and j < len(ist):
        if soll[i][0] == ist[j][0] and abs(soll[i][1] - ist[j][1]) <= tol:
            hit += 1; i += 1; j += 1
            continue
        # vorausschauen: passt der Soll-Punkt weiter hinten? dann ist ist[j] zusätzlich
        k = next((k for k in range(j + 1, min(j + 6, len(ist))) if ist[k][0] == soll[i][0] and abs(ist[k][1] - soll[i][1]) <= tol), None)
        if k is not None:
            extra += [f"{x[0]} {x[2]} {x[1]:g}" for x in ist[j:k]]; j = k
        else:
            miss.append(f"{soll[i][0]} {soll[i][1]:g}"); i += 1
    miss += [f"{s[0]} {s[1]:g}" for s in soll[i:]]
    extra += [f"{x[0]} {x[2]} {x[1]:g}" for x in ist[j:]]
    print(f"{name:42s} Treffer {hit:2d}/{len(soll)}  fehlend {len(miss):2d}  zusätzlich {len(extra):2d}")
    if miss: print("    fehlend:    ", " | ".join(miss))
    if extra: print("    zusätzlich: ", " | ".join(extra))

raw = candle_swings(b, tick)
g10 = groups_min(b, 10)
score("Variante C, 10 Min, ohne Filter (Block)", htf_swings(b, g10, tick))
grow = htf_swings_growing(b, g10, tick)
score("Variante C, 10 Min, ohne Filter (wachsend)", grow)
score("Variante C, 10 Min, 38.2 % (wachsend)", causal_depth(grow, 0.382))
score("Variante C, 10 Min, 23.6 % (wachsend)", causal_depth(grow, 0.236))
for thr in (0.0, 0.382):
    sig = causal_depth(raw, thr) if thr else raw
    score(f"Domino, Signal-Filter {thr:.3f}", domino(b, run_trend(b, sig, tick), tick))

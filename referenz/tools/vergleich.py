"""Rechnet Signallage, Domino-GWL und Variante-C-GWL auf einer CSV und druckt die Punkte
eines Zeitfensters zum Abgleich mit einem Agena-Screenshot (ENT-109/113).

Aufruf: python vergleich.py <csv> <tick> <von 'YYYY-MM-DD HH:MM'> <bis> [gwl_minuten=10]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tests"))
from mtref.bars import load_tradingview_csv
from mtref.swings import candle_swings
from mtref.gwl import causal_depth, htf_swings, domino
from mtref.trend import run_trend
from test_testfaelle import groups_min

csv, tick, von, bis = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]
gm = int(sys.argv[5]) if len(sys.argv) > 5 else 10
b = load_tradingview_csv(csv)
raw = candle_swings(b, tick)
fmt = lambda x: f"{x.kind} {b[x.idx].time[-5:]} {x.price:g}"
win = lambda xs: [x for x in xs if von <= b[x.idx].time <= bis]

def changes(st):
    out, prev = [], None
    for i, s in enumerate(st):
        if s.state != prev and von <= b[i].time <= bis:
            out.append(f"{b[i].time[-5:]} {s.state[:2]}")
        prev = s.state
    return out

for thr, name in ((0.0, "Signal ohne Tiefenfilter"), (0.382, "Signal Tiefenfilter 38.2 %")):
    sig = causal_depth(raw, thr) if thr > 0 else raw
    st = run_trend(b, sig, tick)
    e = st[-1]
    print(f"== {name}: {len(win(sig))} Punkte, {len(changes(st))} Wechsel im Fenster; Ende {e.state}",
          e.p2 and e.p2.price, e.p3 and e.p3.price)
    print("   Wechsel:", " | ".join(changes(st)))
    d = domino(b, st, tick)
    g = run_trend(b, d, tick)
    print(f"   Domino-GWL: {len(win(d))} Punkte:", " | ".join(fmt(x) for x in win(d)))
    print("   Domino-GWL Wechsel:", " | ".join(changes(g)), "| Ende", g[-1].state,
          g[-1].p2 and g[-1].p2.price, g[-1].p3 and g[-1].p3.price)
for thr in (0.0, 0.382):
    c = htf_swings(b, groups_min(b, gm), tick)
    c = causal_depth(c, thr) if thr > 0 else c
    g = run_trend(b, c, tick)
    print(f"== Variante C ({gm} Min, Filter {thr:.3f}): {len(win(c))} Punkte:", " | ".join(fmt(x) for x in win(c)))
    print("   Wechsel:", " | ".join(changes(g)), "| Ende", g[-1].state)

"""GWL-Punkte aus der Signallage – zwei Kandidaten-Varianten (ENT-081/082/083).

Variante A: Korrekturtiefe in % des laufenden GWL-Astes + Bestätigung,
            wenn die Signallage danach deutlich in GWL-Richtung läuft.
Variante B: Verdichtung – Kerzenregel auf zusammengefassten Kerzen (Buch Z-06/Z-12).
Welche Variante gilt, wird an Testfällen entschieden.
"""
from __future__ import annotations

from .bars import Bar, compress
from .swings import Swing, candle_swings


def gwl_depth(bars: list[Bar], sig: list[Swing], thr: float, tick: float,
              pending: list | None = None) -> list[Swing]:
    """Variante A. Ist `pending` eine Liste, erhält sie den laufenden, noch
    unbestätigten Ast (Astextrem, Korrekturextrem) für die Anzeige."""
    if len(sig) < 2:
        return []
    out: list[Swing] = [sig[0]]
    ext: Swing | None = None      # Extrem des laufenden GWL-Astes
    cand: Swing | None = None     # extremstes Korrekturextrem nach ext
    after: list[Swing] = []       # Signal-Wendepunkte nach cand
    queue = list(sig[1:])
    i = 0
    while True:
        # Bestätigung prüfen (auch nach dem letzten Wendepunkt, über die Kerzen)
        if ext is not None and cand is not None:
            up = out[-1].kind == "L"
            v = (lambda p: p) if up else (lambda p: -p)
            leg = v(ext.price) - v(out[-1].price)
            now = queue[i].confirm_idx if i < len(queue) else len(bars) - 1   # keine Vorschau
            if leg > 0 and (v(ext.price) - v(cand.price)) / leg >= thr:
                j = _confirmed(bars, after, cand, ext, v, tick, now)
                if j is not None:
                    out.append(Swing(ext.kind, ext.idx, ext.price, j))
                    out.append(Swing(cand.kind, cand.idx, cand.price, j))
                    queue[i:i] = [a for a in after if a.idx > j]   # Fang-Phase (ENT-083) verbraucht
                    ext, cand, after = None, None, []
                    continue
        if i >= len(queue):
            break
        sw = queue[i]
        i += 1
        up = out[-1].kind == "L"                  # Ast läuft aufwärts -> sucht Hoch
        v = (lambda p: p) if up else (lambda p: -p)
        hk = "H" if up else "L"
        if ext is None:
            if sw.kind == hk:
                ext = sw
            elif v(sw.price) < v(out[-1].price):
                out[-1] = sw                      # Startpunkt wird tiefer/höher
            continue
        if sw.kind != hk:
            if cand is None or v(sw.price) < v(cand.price):
                cand, after = sw, []
            else:
                after.append(sw)
        elif cand is not None and v(sw.price) <= v(ext.price):
            after.append(sw)
        elif v(sw.price) > v(ext.price):
            if cand is not None:
                after.append(sw)                  # erst Bestätigung prüfen (oben)
                if _confirmed(bars, after, cand, ext, v, tick, sw.confirm_idx) is None or \
                        (v(ext.price) - v(cand.price)) / (v(ext.price) - v(out[-1].price)) < thr:
                    ext, cand, after = sw, None, []
            else:
                ext = sw
    if pending is not None:
        pending.extend(x for x in (ext, cand) if x is not None)
    return out


def _confirmed(bars, after, cand, ext, v, tick, now):
    """ENT-083: Signallage läuft nach dem Korrekturextrem deutlich in GWL-Richtung:
    Zwischenhoch (h1), höheres Tief (l2), danach Kurs über h1 – oder der Kurs
    steigt in einem Zug über das Astextrem (V-Form).
    Liefert die Kerze der Bestätigung oder None."""
    for n in range(1, len(after)):
        l2, h1 = after[n], after[n - 1]
        if l2.kind == cand.kind and h1.kind != cand.kind and v(l2.price) >= v(cand.price) + tick:
            target = v(h1.price) + tick
            for b in bars[l2.idx + 1:now + 1]:
                if min(v(b.high), v(b.low)) <= v(cand.price) - tick:
                    return None                   # Korrekturextrem unterboten
                if max(v(b.high), v(b.low)) >= target:
                    return b.idx
            break
    for b in bars[cand.idx + 1:now + 1]:          # V-Form: direkt über das Astextrem
        if min(v(b.high), v(b.low)) <= v(cand.price) - tick:
            return None
        if max(v(b.high), v(b.low)) >= v(ext.price) + tick:
            return b.idx
    return None


def gwl_compressed(bars: list[Bar], k: int, tick: float) -> list[Swing]:
    """Variante B: Kerzenregel auf je k zusammengefassten Kerzen, zurückprojiziert."""
    cbars, starts = compress(bars, k)
    out: list[Swing] = []
    for sw in candle_swings(cbars, tick):
        a, e = starts[sw.idx], starts[sw.idx] + k
        chunk = bars[a:e]
        if sw.kind == "H":
            ext = max(chunk, key=lambda b: b.high)
            target = cbars[sw.idx].low - tick
            d0 = starts[sw.confirm_idx]
            conf = next(b.idx for b in bars[d0:d0 + k] if b.low <= target)
        else:
            ext = min(chunk, key=lambda b: b.low)
            target = cbars[sw.idx].high + tick
            d0 = starts[sw.confirm_idx]
            conf = next(b.idx for b in bars[d0:d0 + k] if b.high >= target)
        out.append(Swing(sw.kind, ext.idx, sw.price, conf))
    return out

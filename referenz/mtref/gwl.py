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


def session_groups(bars: list[Bar], start_hour_utc: int = 22) -> list[list[Bar]]:
    """Fasst Kerzen zu Handelstagen zusammen (CME: Tag beginnt 17:00 CT = 22:00 UTC)."""
    import datetime
    groups: list[list[Bar]] = []
    last = None
    for b in bars:
        d = datetime.datetime.strptime(b.time, "%Y-%m-%d %H:%M") - datetime.timedelta(hours=start_hour_utc)
        if d.date() != last:
            groups.append([])
            last = d.date()
        groups[-1].append(b)
    return groups


def depth_filter(swings: list[Swing], thr: float) -> list[Swing]:
    """Entfernt Korrekturen, die weniger als thr des vorherigen Astes zurücklaufen
    und danach in Astrichtung überboten werden (ENT-081/082)."""
    s = list(swings)
    changed = True
    while changed:
        changed = False
        for i in range(1, len(s) - 2):
            a, b, c, d = s[i - 1], s[i], s[i + 1], s[i + 2]
            leg, dep = abs(b.price - a.price), abs(b.price - c.price)
            cont = d.price > b.price if b.kind == "H" else d.price < b.price
            if leg > 0 and dep / leg < thr and cont:
                del s[i:i + 2]
                changed = True
                break
    return s


def gwl_higher_tf(bars: list[Bar], groups: list[list[Bar]], thr: float, tick: float) -> list[Swing]:
    """Variante C: Kerzenregel auf den Kerzen der höheren Zeiteinheit (z. B. Handelstage),
    Tiefenfilter, Rückprojektion auf die Chart-Kerzen."""
    cb = [Bar(i, g[0].time, g[0].open, max(x.high for x in g), min(x.low for x in g), g[-1].close)
          for i, g in enumerate(groups)]
    out: list[Swing] = []
    for sw in candle_swings(cb, tick):
        g, conf_g = groups[sw.idx], groups[sw.confirm_idx]
        if sw.kind == "H":
            ext = max(g, key=lambda b: b.high)
            conf = next(b.idx for b in conf_g if b.low <= cb[sw.idx].low - tick)
        else:
            ext = min(g, key=lambda b: b.low)
            conf = next(b.idx for b in conf_g if b.high >= cb[sw.idx].high + tick)
        out.append(Swing(sw.kind, ext.idx, sw.price, conf))
    return depth_filter(out, thr)


def htf_swings(bars: list[Bar], groups: list[list[Bar]], tick: float) -> list[Swing]:
    """Kerzenregel auf höheren Kerzen, zurückprojiziert (Extrem-Kerze, Bestätigungs-Kerze)."""
    cb = [Bar(i, g[0].time, g[0].open, max(x.high for x in g), min(x.low for x in g), g[-1].close)
          for i, g in enumerate(groups)]
    out: list[Swing] = []
    for sw in candle_swings(cb, tick):
        g, conf_g = groups[sw.idx], groups[sw.confirm_idx]
        if sw.kind == "H":
            ext = max(g, key=lambda b: b.high)
            conf = next(b.idx for b in conf_g if b.low <= cb[sw.idx].low - tick)
        else:
            ext = min(g, key=lambda b: b.low)
            conf = next(b.idx for b in conf_g if b.high >= cb[sw.idx].high + tick)
        out.append(Swing(sw.kind, ext.idx, sw.price, conf))
    return out


def causal_depth(raw: list[Swing], thr: float) -> list[Swing]:
    """Tiefenfilter ohne Vorschau (für Pine, ENT-031).

    Kandidatenliste wie depth_filter; ein Punkt i wird endgültig, wenn die
    grösste Gegenbewegung danach mindestens thr des Astes davor beträgt und Punkt i-1
    bereits endgültig ist. confirm_idx = Kerze, in der das feststeht.
    """
    s: list[Swing] = []
    final: list[Swing] = []
    for d in raw:
        s.append(d)
        changed = True                                         # Bereinigung im nicht-endgültigen Teil
        while changed:
            changed = False
            for i in range(max(1, len(final)), len(s) - 2):
                a, b, c, e = s[i - 1], s[i], s[i + 1], s[i + 2]
                leg, dep = abs(b.price - a.price), abs(b.price - c.price)
                cont = e.price > b.price if b.kind == "H" else e.price < b.price
                if leg > 0 and dep / leg < thr and cont:
                    del s[i:i + 2]
                    changed = True
                    break
        if not final:
            final.append(s[0])
        while len(final) + 1 < len(s):
            i = len(final)
            leg = abs(s[i].price - s[i - 1].price)
            dep = max(abs(s[i].price - x.price) for x in s[i + 1:] if x.kind != s[i].kind)
            if leg > 0 and dep / leg >= thr:
                final.append(Swing(s[i].kind, s[i].idx, s[i].price, d.confirm_idx))
            else:
                break
    return final

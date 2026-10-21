"""Wandelt die JSON-Antwort des Yahoo-Chart-Dienstes (v8/finance/chart, interval=1m)
in eine CSV im TradingView-Format um (Zeit Europe/Zurich). ENT-113.

Aufruf: python -I yahoo_json_to_csv.py <datei.json|firecrawl-ergebnis.txt> <ziel.csv>
Die Eingabe darf das Firecrawl-Ergebnis sein (JSON mit Feld rawHtml) oder das rohe Chart-JSON.
"""
import datetime, html, json, re, sys, zoneinfo

src, dst = sys.argv[1], sys.argv[2]
txt = open(src, encoding="utf-8").read()
try:
    d = json.loads(txt)
    if isinstance(d, dict) and "rawHtml" in d:
        txt = html.unescape(d["rawHtml"])
except json.JSONDecodeError:
    pass
m = re.search(r'\{"chart".*', txt, re.S)
j = json.loads(m.group(0)[: m.group(0).rfind("}") + 1])
r = j["chart"]["result"][0]
q = r["indicators"]["quote"][0]
tz = zoneinfo.ZoneInfo("Europe/Zurich")
n = 0
with open(dst, "w", encoding="utf-8") as fh:
    fh.write("time,open,high,low,close,Volume\n")
    for i, t in enumerate(r["timestamp"]):
        if q["open"][i] is None:
            continue
        dt = datetime.datetime.fromtimestamp(t, tz).strftime("%Y-%m-%d %H:%M")
        fh.write(f"{dt},{q['open'][i]},{q['high'][i]},{q['low'][i]},{q['close'][i]},{q['volume'][i] or 0}\n")
        n += 1
print(r["meta"]["symbol"], n, "Kerzen ->", dst)

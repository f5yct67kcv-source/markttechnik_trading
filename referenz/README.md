# Python-Referenz (ENT-031)

Prüfbare Referenz der Markttechnik-Regeln. Pine Script wird später 1:1 daraus portiert.

| Modul | Inhalt | ENT |
|------|--------|-----|
| `mtref/bars.py` | CSV-Import (TradingView-Export), Verdichtung, Reihenfolge in der Kerze | 005, 024 |
| `mtref/swings.py` | Kerzenregel: Wendepunkte der untersten Ebene (Signallage) | 065 |
| `mtref/trend.py` | Trendzustand grün/rot/blau, Punkte 1-2-3, Bruchlinie | 035–044, 079 |
| `mtref/gwl.py` | GWL aus der Signallage: Variante A (Korrekturtiefe), Variante B (Verdichtung) | 047, 077, 081–083 |
| `tools/vergleich.py` | Chartbild Signallage (fein) + GWL (dick) aus CSV | 080 |

```bash
pip install pytest matplotlib
python -m pytest -q referenz/tests
python referenz/tools/vergleich.py daten.csv --tick 0.01 --variante A --schwelle 0.3 --out bild.png
```

Die Tests in `tests/test_trend.py` sind die Skizzen aus `docs/skizzen/`.

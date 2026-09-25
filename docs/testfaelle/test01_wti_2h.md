# Testfall 01 – WTI Rohöl CFD (TVC), 2h, Stand 25.09.2026

- Original: `test01_wti_2h_original.webp`
- Soll (Auftraggeber): `test01_wti_2h_SOLL_auftraggeber.webp`
- Erster Versuch Claude (manuell): `test01_wti_2h_claude.png` – hat nur **eine** Trendgrösse gezeichnet; das entspricht ungefähr der Signallage des Solls.

## Soll-Punkte GWL (aus Zeichnung Auftraggeber, ±0,3)
| Datum | Punkt | Kurs |
|------|------|------|
| ~07.08. | Tief | ~75,0 |
| 11.08. | Hoch | ~84,8 |
| 14.08. | Tief | ~80,1 |
| 21.08. | Hoch | ~87,7 |
| 26.08. | Tief | ~79,5 |
| 16.09. | Hoch | ~106,9 |
| 23.09. | Tief | ~88,6 |
| 25.09. | Hoch | ~96,8 |

## Beobachtungen
- Die Signallage (fein) schwankt stark; die GWL (dick) verbindet nur die Extreme zwischen Signal-Richtungswechseln.
- 03.–06.09.: Signal nur **blau** (gebrochen), kein Gegentrend → **kein** GWL-Punkt.
- 11.–15.09.: Rücksetzer auf ~98,5 bleibt im Signal grün → **kein** GWL-Punkt.
- 16.–23.09.: Signal durchgehend rot (inkl. tieferem Hoch ~102,7) → ein GWL-Schenkel.

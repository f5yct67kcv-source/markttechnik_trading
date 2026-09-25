# Regelauszug 04 – Stopps (Fachteil I)

Quelle: `docs/literatur/Stopps MT.pdf` (33 PDF-Seiten, Scan). Seitenangaben = PDF-Seite.
**Achtung:** S. 21 und S. 22 sind identisch (Doppelscan). Vermutlich fehlt die Seite mit Bild 15a–e (klassischer Trailingstopp Schritt für Schritt). S. 33 ist leer.
Nur Kernaussagen, kein Volltext. Status: **Auszug. Regeln werden erst durch ENTs verbindlich.**

## Grundsätze

| Nr. | Regel | Fundstelle |
|-----|-------|------------|
| S-01 | Drei Stoppkategorien: Verlustbegrenzungsstopp (Initial), Gewinnsicherungsstopp (Trailing), Gewinnmitnahmestopp (Kursziel). Für MT relevant sind nur Stopps, die **direkt aus dem Chart** ablesbar sind (keine Indikatoren, keine festen Beträge). | S. 2–5 |
| S-02 | **Der Stopp muss zum Ziel passen.** Vor jedem Trade muss eine von drei Ausrichtungen feststehen: **Handel des Trends**, **Handel der Bewegung** oder **Handel des Ausbruchs**. Je nach Ausrichtung gelten andere Stoppregeln. | S. 5–8 (Bild 1, 2) |

## Handel des Trends

| Nr. | Regel | Fundstelle |
|-----|-------|------------|
| S-03 | Einstieg am Durchbruch durch P2. **Erster Stopp auf dem letzten P3** (lokales Tief, nicht das Tief des letzten Bars). | S. 8–9 (Bild 3, 4b) |
| S-04 | **Nachziehen erst, wenn der vorherige P2 überschritten wird.** Dann wandert der Stopp auf das neue P3, also das tiefste Tief der Korrektur. Während der Korrektur bleibt der Stopp unverändert, auch wenn die Position ins Minus läuft. | S. 8–10 (Bild 3, 4b, 7), S. 15 (Bild 9a/b) |
| S-05 | **Welches Tief das letzte ist, zeigt sich erst beim Überschreiten des Hochs.** | S. 15 (Bild 9b) |
| S-06 | **Gegensignal:** Entsteht in der Korrektur ein entgegengesetztes 1-2-3 und wird dessen P2 durchbrochen, soll die Position geschlossen werden, auch wenn der Stopp noch nicht erreicht ist. | S. 15 (Bild 8b, 9c) |
| S-07 | **P2 und P3 in derselben Periode** möglich (Bild 10–12). Die Regeln gelten unverändert. Der Stopp wird auf das Tief der Periode gezogen, wenn das Hoch der Periode **nach** dem Tief entstand (12b). Entstand das Tief zuletzt (12c), wird erst nachgezogen, wenn das Periodenhoch überschritten wird. Die Reihenfolge ist nur über die untergeordnete Zeiteinheit bzw. T&S ermittelbar. | S. 15–18 |
| S-08 | **Gaps:** Gap innerhalb der Vortagesspanne = Korrektur, der Stopp kann auf die Eröffnung (neuer P3) gesetzt werden (13a). Gap über dem Vortageshoch = neuer P2 (13b). **Eröffnung unter dem letzten P3 = Trendbruch**, die Position wird zur Eröffnung geschlossen (13c). | S. 19–20 |
| S-09 | Trendhandel ist auch auf Tick-Basis längerfristig ausgerichtet (Trends über Stunden). Kleine Wellen sind nicht für die Stoppsetzung heranzuziehen. **Ein 1-2-3 muss deutlich erkennbar sein.** | S. 9, S. 12–13 (Bild 6) |

## Handel der Bewegung (Innenstab-modifizierter Trailingstopp)

| Nr. | Regel | Fundstelle |
|-----|-------|------------|
| S-10 | **Klassischer Trailingstopp:** Erster Stopp auf das Tief (Long) bzw. Hoch (Short) der **Einstiegsperiode**. Nach jedem Periodenschluss wird der Stopp auf das Tief der **gerade abgeschlossenen** Periode nachgezogen, treppenstufenartig. Das ist zugleich ein Volatilitätsstopp. | S. 20–22 |
| S-11 | **Innenstab-Modifikation:** Jede abgeschlossene Periode wird geprüft. Ist sie ein Innenstab, wird **nicht nachgezogen**, sondern der Stopp **auf das Tief der Periode vor dem Aussenstab zurückversetzt**. | S. 23–25 (Bild 17, 18a/b) |
| S-12 | Der zurückversetzte Stopp bleibt, bis (a) er ausgelöst wird, (b) eine Periode **über** dem Aussenstab schliesst → dann normal nachziehen, oder (c) eine Periode **unter** dem Aussenstab schliesst, ohne den Stopp zu erreichen → **Position zum Schluss schliessen**. | S. 25–26 (Bild 18c/d) |
| S-13 | Diese Innenstab-Modifikation ist **erst ab 10-Min-Zeiteinheiten** sinnvoll. | S. 26 |
| S-14 | **Ausbruchsperiode kann neuer Aussenstab sein:** Folgt ihr ein Innenstab, wird erneut zurückversetzt (Bild 22). | S. 28 |
| S-15 | **Stopp an der Einstiegsperiode:** Liegt der Einstieg nahe an deren Eröffnung (Tief noch nicht klar), vorläufig auf das Tief der **Vorperiode**, nach Abschluss auf das Tief der Einstiegsperiode (Bild 21). | S. 27–28 |
| S-16 | **Vorperiode liegt höher als der Aussenstab:** Stopp bleibt am Aussenstab bzw. geht auf das nächstliegende lokale Tief der vorherigen Perioden (Bild 23). | S. 28–29 |
| S-17 | **Rauschen:** Bei mehreren sehr engen Perioden (Differenz nur wenige Ticks) wird das Nachziehen und die Innenstabbeachtung **ausgesetzt**, bis wieder eine deutlich grössere Periode kommt (Bild 24). Nicht schon beim ersten kleinen Bar. Alternative: höhere Zeiteinheit. | S. 30–31 |
| S-18 | **Unschärfe auf Tagesbasis:** Schliesst ein Bar nur minimal (2–3 Punkte) ausserhalb des Aussenstabs, darf er „unscharf“ trotzdem als Innenstab gelten, zugunsten der Position (Bild 25). | S. 31–32 |
| S-19 | Im automatisierten Handel sieht das Programm nur OHLC. Stoppregeln müssen daher weitere Merkmale mathematisch fassen. | S. 29 |

## Lücken

- **L-10:** Seite mit Bild 15a–e fehlt (Doppelscan S. 21/22).
- **L-11:** „Handel des Ausbruchs“ wird genannt (Bild 2), aber kein eigener Stoppabschnitt. Vermutlich im Kapitel Einstiege.
- **L-12:** S-04 (nachziehen erst bei Überschreiten von P2) weicht von ENT-048 ab (GWL-P3 steht fest, wenn der Signaltrend grün wird). Siehe Skizze I.
- **L-13:** Rauschen (S-17) und Unschärfe (S-18) sind im Buch Ermessenssache. Für die Automatik braucht es feste Parameter.

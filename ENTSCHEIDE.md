# Entscheidungsprotokoll – Markttechnik-Addon (TradingView)

Jede Entscheidung aus dem Interview wird hier fortlaufend mit ENT-Nummer festgehalten.
Bereits getroffene Entscheide werden nicht stillschweigend geändert. Eine Änderung bekommt
eine neue ENT-Nr. mit Verweis auf den abgelösten Entscheid.

| ENT | Datum | Thema | Entscheid | Begründung |
|-----|-------|-------|-----------|------------|
| ENT-001 | 2026-09-25 | Referenz / Ground Truth | *Das grosse Buch der Markttechnik* (M. Voigt) definiert die Regeln. Wo das Buch Spielraum lässt, entscheidet die Auslegung des Auftraggebers; jede Auslegung wird als eigener ENT festgehalten. AgenaTrader-Charts (ONDaylinesDomino, MTOnLiveSignalPro) dienen als Testfälle, nicht als 1:1-Vorlage. | Buch ist bei Randfällen nicht eindeutig; Agena enthält Hersteller-Parameter (z. B. „Unschärfe“) ohne Quellcode. Kombination ergibt prüfbare, lückenlose Regeln. |
| ENT-002 | 2026-09-25 | Bereitstellung Literatur | Literatur wird als PDF/Text ins Repo gelegt (Ablage `docs/literatur/`). Repo bleibt privat. | Vollständige, nachlesbare Quelle für die Regelableitung; Urheberrecht → keine Veröffentlichung. |
| ENT-003 | 2026-09-25 | Trendgrössen-Kopplung | Trendgrössen sind fest an Zeitrahmen-Paare gekoppelt: Tick/1 Min · 1 Min/10 Min · 10 Min/60 Min · 60 Min/Tag · Tag/Woche. Die kleinere Grösse ist immer der **Signaltrend** der grösseren (übergeordneten) Grösse. Keine beliebig vielen Grössen: je nach Liquidität des Markts 4–5 Stufen. Im Chart sichtbar sind immer genau zwei Grössen: die untergeordnete (fein gestrichelt) und die übergeordnete **GWL (Grosswetterlage)**. | Vorgabe des Auftraggebers aus der Praxis (Markttechnik-Regelwerk). Die Erkennung dieser Verschachtelung ist die zentrale technische Herausforderung. |

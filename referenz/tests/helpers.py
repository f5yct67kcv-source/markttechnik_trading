from mtref.bars import Bar


def bars_from_path(points: list[float], steps: int = 4, wick: float = 0.2) -> list[Bar]:
    """Erzeugt Kerzen, die eine Zickzack-Linie durch die Wegpunkte abfahren."""
    prices: list[float] = [points[0]]
    for a, b in zip(points, points[1:]):
        prices += [a + (b - a) * s / steps for s in range(1, steps + 1)]
    bars = []
    for i, (o, c) in enumerate(zip(prices, prices[1:])):
        bars.append(Bar(i, str(i), o, max(o, c) + wick, min(o, c) - wick, c))
    return bars

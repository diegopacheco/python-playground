def total_pages(pages: list[int]) -> int:
    total = 0
    for value in pages:
        total += value
    return total


def average_price(prices: list[float]) -> float:
    if not prices:
        return 0.0
    total = 0.0
    for value in prices:
        total += value
    return round(total / len(prices), 2)


def most_expensive(titles: list[str], prices: list[float]) -> str | None:
    if len(titles) != len(prices):
        raise ValueError("titles and prices must have the same size")
    best: str | None = None
    best_price = -1.0
    for i in range(len(titles)):
        if prices[i] > best_price:
            best_price = prices[i]
            best = titles[i]
    return best

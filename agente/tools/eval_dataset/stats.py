"""Descriptive and inferential statistics of the evaluation, in pure Python (no external dependency)."""
from __future__ import annotations

import math
from dataclasses import dataclass

Z95 = 1.959963984540054


@dataclass
class Confusion:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    def add(self, outcome: str) -> None:
        setattr(self, outcome.lower(), getattr(self, outcome.lower()) + 1)

    @property
    def precision(self) -> float | None:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else None

    @property
    def recall(self) -> float | None:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else None

    @property
    def specificity(self) -> float | None:
        return self.tn / (self.tn + self.fp) if self.tn + self.fp else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p and r else (0.0 if p is not None and r is not None else None)

    @property
    def accuracy(self) -> float | None:
        n = self.tp + self.fp + self.fn + self.tn
        return (self.tp + self.tn) / n if n else None


def outcome(truth: bool, predicted: bool) -> str:
    return {(True, True): "TP", (False, True): "FP", (True, False): "FN", (False, False): "TN"}[(truth, predicted)]


def wilson(successes: int, n: int, z: float = Z95) -> tuple[float, float] | None:
    """Wilson score interval for a proportion (95 % by default). Behaves well near 0 and 1 and with small n."""
    if n == 0:
        return None
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def binom_test_greater(successes: int, n: int, p0: float) -> float | None:
    """Exact one-sided binomial test. H0: p <= p0, H1: p > p0. Returns P(X >= successes | p0)."""
    if n == 0:
        return None
    return min(1.0, sum(math.comb(n, k) * p0**k * (1 - p0) ** (n - k) for k in range(successes, n + 1)))


def fisher_exact(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact test for the 2x2 table [[a, b], [c, d]]."""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    if n == 0:
        return 1.0

    def prob(x: int) -> float:
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)

    observed = prob(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    return min(1.0, sum(p for p in (prob(x) for x in range(lo, hi + 1)) if p <= observed * (1 + 1e-9)))


def describe(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    xs = sorted(values)
    n = len(xs)
    mean = sum(xs) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0

    def quantile(q: float) -> float:
        pos = q * (n - 1)
        lo, hi = math.floor(pos), math.ceil(pos)
        return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)

    return {"n": n, "media": mean, "mediana": quantile(0.5), "desv_est": sd, "min": xs[0], "max": xs[-1], "p95": quantile(0.95)}


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1  # average rank for ties
        i = j + 1
    return ranks


def pearson(x: list[float], y: list[float]) -> float:
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx, syy = sum((a - mx) ** 2 for a in x), sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else 0.0


def _t_sf(t: float, df: int) -> float:
    """Survival function of Student's t by numerical integration (Simpson), enough for a p-value."""
    if df <= 0:
        return float("nan")
    c = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi)

    def pdf(u: float) -> float:
        return c * (1 + u * u / df) ** (-(df + 1) / 2)

    t = abs(t)
    upper, steps = max(t + 60.0, 80.0), 20000
    h = (upper - t) / steps
    area = pdf(t) + pdf(upper) + sum((4 if i % 2 else 2) * pdf(t + i * h) for i in range(1, steps))
    return max(0.0, area * h / 3)


def spearman(x: list[float], y: list[float]) -> dict:
    """Spearman rank correlation with a two-sided p-value from the t approximation."""
    n = len(x)
    if n < 3:
        return {"n": n, "rho": None, "p": None}
    rho = pearson(_ranks(x), _ranks(y))
    if abs(rho) >= 1:
        return {"n": n, "rho": rho, "p": 0.0}
    t = rho * math.sqrt((n - 2) / (1 - rho * rho))
    return {"n": n, "rho": rho, "p": min(1.0, 2 * _t_sf(t, n - 2))}


def linear_fit(x: list[float], y: list[float]) -> dict:
    """Least-squares line y = a + b x and its R squared."""
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx if sxx else 0.0
    return {"intercepto": my - b * mx, "pendiente": b, "r2": pearson(x, y) ** 2}

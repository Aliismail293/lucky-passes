"""Bootstrap confidence intervals and McNemar's test. Plain numpy, fixed seeds.

Bootstrap: resample the questions with replacement many times, recompute the rate each time, and take the
2.5th and 97.5th percentiles. That range is the 95% interval: how much the rate would wobble with a
different sample of questions of the same kind.
"""

from math import comb

import numpy as np


def bootstrap_ci(values: list[float], resamples: int = 1000, seed: int = 0) -> dict:
    """Mean of 0/1 (or real) values with a 95% percentile bootstrap interval."""
    data = np.asarray(values, dtype=float)
    n = len(data)
    if n == 0:
        return {"value": None, "lo": None, "hi": None, "n": 0}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(resamples, n))
    means = data[idx].mean(axis=1)
    return {
        "value": float(data.mean()),
        "lo": float(np.percentile(means, 2.5)),
        "hi": float(np.percentile(means, 97.5)),
        "n": n,
    }


def bootstrap_ratio_ci(numer: list[float], denom: list[float], resamples: int = 1000, seed: int = 0) -> dict:
    """Ratio of sums (e.g. lucky passes / correct answers), resampling questions as pairs."""
    a = np.asarray(numer, dtype=float)
    b = np.asarray(denom, dtype=float)
    n = len(a)
    if n == 0 or b.sum() == 0:
        return {"value": None, "lo": None, "hi": None, "n": int(b.sum()) if n else 0}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(resamples, n))
    sa, sb = a[idx].sum(axis=1), b[idx].sum(axis=1)
    ratios = np.divide(sa, sb, out=np.full_like(sa, np.nan), where=sb > 0)
    ratios = ratios[~np.isnan(ratios)]
    return {
        "value": float(a.sum() / b.sum()),
        "lo": float(np.percentile(ratios, 2.5)),
        "hi": float(np.percentile(ratios, 97.5)),
        "n": int(b.sum()),
    }


def paired_bootstrap_diff(a: list[float], b: list[float], resamples: int = 1000, seed: int = 0) -> dict:
    """Mean of (a - b) over the same questions, with a 95% interval. a and b must be aligned."""
    if len(a) != len(b):
        raise ValueError("paired values must have the same length")
    return bootstrap_ci([x - y for x, y in zip(a, b, strict=True)], resamples, seed)


def mcnemar(a: list[bool], b: list[bool]) -> dict:
    """Exact McNemar test on paired outcomes.

    Only the questions that flipped matter: b01 = wrong under a but right under b, b10 = the reverse.
    If the two conditions were equally good, each flip would go either way with probability 1/2,
    so the p-value is a two-sided binomial test on min(b01, b10) out of b01 + b10.
    """
    if len(a) != len(b):
        raise ValueError("paired values must have the same length")
    b01 = sum(1 for x, y in zip(a, b, strict=True) if not x and y)
    b10 = sum(1 for x, y in zip(a, b, strict=True) if x and not y)
    flips = b01 + b10
    if flips == 0:
        return {"b01": 0, "b10": 0, "p": 1.0}
    tail = sum(comb(flips, i) for i in range(min(b01, b10) + 1)) / 2**flips
    return {"b01": b01, "b10": b10, "p": min(1.0, 2 * tail)}


def _binom_cdf(k: int, n: int, p: float) -> float:
    return sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def clopper_pearson(successes: int, n: int, alpha: float = 0.05) -> dict:
    """Exact (Clopper-Pearson) 95% interval for a proportion.

    Unlike the percentile bootstrap, it doesn't collapse to [0, 0] when no successes are seen: 0 of 150 gives an
    upper bound of about 2.4%. Each bound is found by bisection on the binomial CDF.
    """
    if n == 0:
        return {"value": None, "lo": None, "hi": None, "n": 0}

    def solve(target, k):  # the p at which P(X <= k) = target; the CDF falls as p rises
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if _binom_cdf(k, n, mid) > target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    lower = 0.0 if successes == 0 else solve(1 - alpha / 2, successes - 1)
    upper = 1.0 if successes == n else solve(alpha / 2, successes)
    return {"value": successes / n, "lo": lower, "hi": upper, "n": n}


def holm(p_values: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, in the input order."""
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p_values) - rank) * p_values[i]))
        adjusted[i] = running
    return adjusted

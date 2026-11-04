"""Paired tests recommended for randomized testing studies (Arcuri and Briand, STVR 2014)."""
import math

def mcnemar_exact(left_only, right_only):
    """Two-sided exact McNemar p-value on discordant pairs (binomial, p=0.5)."""
    n = left_only + right_only
    if n == 0:
        return 1.0
    k = min(left_only, right_only)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)

def a12(left, right):
    """Vargha-Delaney A12: P(left > right) + 0.5 P(left == right).

    For capped call counts (lower is better), A12 > 0.5 means right needs fewer calls.
    """
    if not left or not right:
        raise ValueError("A12 requires two nonempty samples")
    greater = sum((x > y) + 0.5 * (x == y) for x in left for y in right)
    return greater / (len(left) * len(right))

def holm(pvalues):
    """Holm step-down adjusted p-values, returned in input order."""
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted, running = [0.0] * len(pvalues), 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted

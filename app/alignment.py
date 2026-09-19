"""Core quote-to-source alignment logic.

Matching rules
--------------
* Matching is whitespace-insensitive: every run of consecutive whitespace
  characters (spaces, tabs, newlines, ...) is treated as a single space,
  in both the source text and each quote.
* Leading/trailing whitespace of a quote is ignored.
* Returned offsets always refer to the *original* characters of the source
  text.  A located quote is reported as a half-open span ``(start, end)``
  such that ``text[start:end]`` is the matched original substring
  (interior whitespace included exactly as it appears in the source).

Joint selection
---------------
Quotes may occur multiple times and may be impossible to locate.  From the
candidate spans of every quote we jointly pick at most one span per quote
such that the chosen spans do not overlap and appear in the same order as
the quote array.  Among all feasible selections we:

1. maximize the number of located quotes;
2. then minimize the total number of original characters skipped between
   consecutive located segments;
3. then take the lexicographically smallest offset sequence (a located
   span sorts before an unlocated ``null`` at the same array position).
"""

from __future__ import annotations

import sys
from bisect import bisect_left
from functools import lru_cache

Span = tuple[int, int]


def _normalize(text: str) -> tuple[str, list[int]]:
    """Collapse whitespace runs to single spaces.

    Returns the normalized string together with a map from each normalized
    character index to the offset of the corresponding character in the
    original text (for a collapsed whitespace run, the offset of the first
    whitespace character of the run).
    """
    norm_chars: list[str] = []
    index_map: list[int] = []
    prev_was_space = False
    for i, ch in enumerate(text):
        if ch.isspace():
            if not prev_was_space:
                norm_chars.append(" ")
                index_map.append(i)
            prev_was_space = True
        else:
            norm_chars.append(ch)
            index_map.append(i)
            prev_was_space = False
    return "".join(norm_chars), index_map


def _normalize_quote(quote: str) -> str:
    """Normalize a quote for matching (collapse whitespace, strip ends)."""
    return _normalize(quote)[0].strip(" ")


def _find_candidates(norm_text: str, index_map: list[int], norm_quote: str) -> list[Span]:
    """All spans (original offsets, half-open) where the quote matches."""
    spans: set[Span] = set()
    start = 0
    qlen = len(norm_quote)
    while True:
        idx = norm_text.find(norm_quote, start)
        if idx < 0:
            break
        s = index_map[idx]
        e = index_map[idx + qlen - 1] + 1
        spans.add((s, e))
        start = idx + 1  # allow overlapping occurrences
    return sorted(spans)


def _better(a: tuple[int, int, tuple], b: tuple[int, int, tuple]) -> bool:
    """True if selection value ``a`` is strictly better than ``b``."""
    if a[0] != b[0]:
        return a[0] > b[0]  # more located quotes wins
    if a[1] != b[1]:
        return a[1] < b[1]  # fewer skipped characters wins
    return a[2] < b[2]  # lexicographically smaller offset sequence wins


def align_quotes(text: str, quotes: list[str]) -> list[Span | None]:
    """Align each quote to the source text.

    Returns a list parallel to ``quotes`` with ``(start, end)`` original
    offsets for located quotes and ``None`` for quotes that cannot be
    located under the joint selection rules.
    """
    norm_text, index_map = _normalize(text)

    per_quote: list[list[Span]] = []
    for quote in quotes:
        norm_quote = _normalize_quote(quote)
        if not norm_quote or not norm_text:
            per_quote.append([])
        else:
            per_quote.append(_find_candidates(norm_text, index_map, norm_quote))

    n = len(quotes)
    if n == 0:
        return []

    sys.setrecursionlimit(max(sys.getrecursionlimit(), 4 * n + 1000))

    starts = [[s for s, _ in cands] for cands in per_quote]

    # Sequence encoding per quote: located -> (0, start, end), null -> (1, 0, 0).
    # This makes located spans sort before nulls and smaller offsets first.
    @lru_cache(maxsize=None)
    def dp(i: int, prev_end: int) -> tuple[int, int, tuple]:
        """Best value (located, skipped, seq) for quotes[i:]; chosen spans
        must start at an offset >= prev_end (-1 means nothing chosen yet)."""
        if i == n:
            return (0, 0, ())

        # Option 1: leave quote i unlocated.
        located, skipped, seq = dp(i + 1, prev_end)
        best = (located, skipped, ((1, 0, 0),) + seq)

        # Option 2: place quote i at one of its feasible candidate spans.
        for k in range(bisect_left(starts[i], prev_end), len(per_quote[i])):
            s, e = per_quote[i][k]
            gap = s - prev_end if prev_end >= 0 else 0
            located, skipped, seq = dp(i + 1, e)
            cand = (located + 1, skipped + gap, ((0, s, e),) + seq)
            if _better(cand, best):
                best = cand
        return best

    _, _, seq = dp(0, -1)
    return [(s, e) if tag == 0 else None for tag, s, e in seq]

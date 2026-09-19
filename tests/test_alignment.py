"""Tests for the core alignment logic (run with: python -m pytest tests/)."""

from app.alignment import align_quotes


def test_basic_match():
    assert align_quotes("hello world", ["world"]) == [(6, 11)]


def test_whitespace_collapsed_but_original_offsets_returned():
    text = "a   b\t\nc"
    # "a b c" matches the whole text; offsets refer to original characters.
    assert align_quotes(text, ["a b c"]) == [(0, 8)]
    assert text[0:8] == "a   b\t\nc"


def test_quote_surrounding_whitespace_ignored():
    assert align_quotes("a foo b", ["  foo  "]) == [(2, 5)]


def test_unlocatable_quote_returns_none():
    assert align_quotes("hello world", ["mars", "world"]) == [None, (6, 11)]


def test_empty_quote_returns_none():
    assert align_quotes("abc", ["", "   "]) == [None, None]


def test_empty_inputs():
    assert align_quotes("", []) == []
    assert align_quotes("abc", []) == []
    assert align_quotes("", ["a"]) == [None]


def test_repeated_quote_uses_non_overlapping_occurrences_in_order():
    text = "ab ab"
    assert align_quotes(text, ["ab", "ab"]) == [(0, 2), (3, 5)]


def test_repeated_quote_without_room_leaves_null():
    assert align_quotes("ab", ["ab", "ab"]) == [(0, 2), None]


def test_maximize_located_count():
    # Locating "abc" (the only span for the middle quote) would overlap the
    # only spans of both outer quotes; skipping it locates two quotes.
    text = "abc"
    assert align_quotes(text, ["a", "abc", "c"]) == [(0, 1), None, (2, 3)]


def test_minimize_skipped_characters():
    # Both solutions locate two quotes; the closer pair wins.
    text = "a xxxx a a"
    assert align_quotes(text, ["a", "a"]) == [(7, 8), (9, 10)]


def test_lexicographically_smallest_offsets_breaks_ties():
    # Equal count and equal skipped characters -> earliest offsets win.
    assert align_quotes("a a", ["a"]) == [(0, 1)]
    assert align_quotes("ab ab", ["ab"]) == [(0, 2)]


def test_order_preserved_across_quotes():
    text = "b a b"
    # "a" then "b": the only in-order non-overlapping choice.
    assert align_quotes(text, ["a", "b"]) == [(2, 3), (4, 5)]


def test_overlapping_occurrences_of_same_quote():
    # "aa" occurs at 0 and 1 in "aaa"; only one can be taken.
    assert align_quotes("aaa", ["aa"]) == [(0, 2)]
    assert align_quotes("aaaa", ["aa", "aa"]) == [(0, 2), (2, 4)]


def test_multiline_text_and_quotes():
    text = "第一行\n第二行\t第三行"
    assert align_quotes(text, ["第二行  第三行"]) == [(4, 11)]
    assert text[4:11] == "第二行\t第三行"

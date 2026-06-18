"""
tests/claude_test_tools.py

Pytest suite for the three FitFindr tools in tools.py.

Each tool gets:
  - happy-path coverage, and
  - at least one test per documented failure mode (see planning.md):
      * search_listings  → no results match the query
      * suggest_outfit   → wardrobe is empty
      * create_fit_card  → outfit input is missing or incomplete

Tools 2 and 3 call an LLM via tools._call_llm. Those calls are stubbed with the
`fake_llm` fixture so the suite is deterministic and needs no network/API key.
Tool 1 is pure logic over the real listings dataset, so it runs unmocked.

Run:
    pytest                       # whole suite
    pytest -k search_listings    # one tool
"""

import pytest

import tools
from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import (
    load_listings,
    get_example_wardrobe,
    get_empty_wardrobe,
)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def fake_llm(monkeypatch):
    """Replace tools._call_llm with a recording stub.

    Returns the list of recorded calls; each entry is
    {"prompt": str, "temperature": float}. Tests can assert on what the tool
    handed the LLM without making a real request.
    """
    calls = []

    def _fake(prompt, temperature=0.7):
        calls.append({"prompt": prompt, "temperature": temperature})
        return "FAKE_LLM_RESPONSE"

    monkeypatch.setattr(tools, "_call_llm", _fake)
    return calls


@pytest.fixture
def sample_item():
    """A real listing dict to use as the 'new item' across tools."""
    return load_listings()[0]


def _score(listing: dict, keywords: list[str]) -> int:
    """Re-derive search_listings' keyword-overlap score for ordering checks."""
    haystack = " ".join([
        listing.get("title", ""),
        listing.get("description", ""),
        listing.get("category", ""),
        listing.get("brand") or "",
        " ".join(listing.get("style_tags", [])),
        " ".join(listing.get("colors", [])),
    ]).lower()
    return sum(1 for word in keywords if word in haystack)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

class TestSearchListings:
    """Pure-logic search over the real listings dataset (no LLM)."""

    def test_returns_list_of_matches(self):
        results = search_listings("vintage denim", max_price=50.0)
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, dict) for r in results)

    def test_max_price_filter_is_inclusive(self):
        results = search_listings("jeans", max_price=38.0)
        assert results, "expected at least one match at/under the ceiling"
        assert all(r["price"] <= 38.0 for r in results)

    def test_size_filter_is_case_insensitive(self):
        # Lowercase query size must match however the data cases its sizes.
        results = search_listings("tee", size="m")
        assert all("m" in (r.get("size") or "").lower() for r in results)

    def test_results_sorted_by_relevance_descending(self):
        query = "vintage graphic tee"
        keywords = query.lower().split()
        results = search_listings(query)
        scores = [_score(r, keywords) for r in results]
        assert scores == sorted(scores, reverse=True)
        assert all(s > 0 for s in scores), "zero-score listings must be dropped"

    # ── failure mode: no results match the query ──────────────────────────────

    def test_no_keyword_match_returns_empty_list(self):
        results = search_listings("astronaut spacesuit helmet moonboots")
        assert results == []  # empty list, not None, no exception

    def test_price_ceiling_excludes_everything_returns_empty_list(self):
        results = search_listings("jacket", max_price=0.01)
        assert results == []

    def test_size_with_no_match_returns_empty_list(self):
        results = search_listings("jeans", size="size-that-does-not-exist")
        assert results == []


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

class TestSuggestOutfit:

    def test_populated_wardrobe_returns_string(self, fake_llm, sample_item):
        result = suggest_outfit(sample_item, get_example_wardrobe())
        assert isinstance(result, str) and result.strip()
        assert len(fake_llm) == 1
        # The prompt must reference actual wardrobe pieces, not just the item.
        prompt = fake_llm[0]["prompt"]
        first_piece = get_example_wardrobe()["items"][0]["name"]
        assert first_piece in prompt

    # ── failure mode: wardrobe is empty ───────────────────────────────────────

    def test_empty_wardrobe_returns_nonempty_general_advice(self, fake_llm, sample_item):
        result = suggest_outfit(sample_item, get_empty_wardrobe())
        assert isinstance(result, str) and result.strip() != ""
        assert len(fake_llm) == 1
        # Empty-wardrobe branch asks for general advice, not specific outfits.
        assert "wardrobe" in fake_llm[0]["prompt"].lower()

    def test_missing_items_key_treated_as_empty(self, fake_llm, sample_item):
        # A malformed wardrobe with no 'items' key must not raise.
        result = suggest_outfit(sample_item, {})
        assert isinstance(result, str) and result.strip() != ""
        assert len(fake_llm) == 1


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

class TestCreateFitCard:

    def test_valid_outfit_returns_caption_at_high_temperature(self, fake_llm, sample_item):
        outfit = "Pair it with baggy jeans and chunky white sneakers for streetwear."
        result = create_fit_card(outfit, sample_item)
        assert isinstance(result, str) and result.strip()
        assert len(fake_llm) == 1
        # Spec calls for higher temperature so captions vary across inputs.
        assert fake_llm[0]["temperature"] == pytest.approx(0.9)

    # ── failure mode: outfit input is missing or incomplete ───────────────────

    def test_empty_outfit_with_item_returns_string_no_exception(self, fake_llm, sample_item):
        # Outfit missing but item present: caption the find alone, never raise.
        result = create_fit_card("", sample_item)
        assert isinstance(result, str)

    def test_whitespace_only_outfit_treated_as_missing(self, fake_llm, sample_item):
        # Whitespace must not be mistaken for a real outfit suggestion.
        result = create_fit_card("   \n\t ", sample_item)
        assert isinstance(result, str)
        assert len(fake_llm) == 1
        prompt = fake_llm[0]["prompt"].lower()
        assert "no styled outfit yet" in prompt or "no outfit" in prompt

    def test_outfit_and_item_both_missing_returns_message_without_llm(self, fake_llm):
        # Nothing to work with: return a descriptive string, never call the LLM.
        result = create_fit_card("", {})
        assert isinstance(result, str) and result.strip() != ""
        assert fake_llm == [], "LLM should not be called when there is no input"
        assert "can't" in result.lower() or "no" in result.lower()

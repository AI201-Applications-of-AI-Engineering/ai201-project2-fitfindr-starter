"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

# Default Groq-hosted model. Swap here if you want a different one.
GROQ_MODEL = "llama-3.3-70b-versatile"


def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _call_llm(prompt: str, temperature: float = 0.7) -> str:
    """Send a single user prompt to the LLM and return its text response."""
    client = _get_groq_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    # Break the description into lowercase keywords to score against.
    keywords = [word for word in description.lower().split() if word]

    scored: list[tuple[int, dict]] = []
    for listing in listings:
        # Filter by price ceiling (inclusive), if provided.
        if max_price is not None and listing["price"] > max_price:
            continue

        # Filter by size (case-insensitive substring match), if provided.
        if size is not None:
            listing_size = (listing.get("size") or "").lower()
            if size.lower() not in listing_size:
                continue

        # Score by keyword overlap across the listing's searchable text.
        haystack = " ".join([
            listing.get("title", ""),
            listing.get("description", ""),
            listing.get("category", ""),
            listing.get("brand") or "",
            " ".join(listing.get("style_tags", [])),
            " ".join(listing.get("colors", [])),
        ]).lower()

        score = sum(1 for word in keywords if word in haystack)

        # Drop listings with no relevant matches.
        if score == 0:
            continue

        scored.append((score, listing))

    # Sort by score, highest first, and return just the listing dicts.
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    # Describe the thrifted item so the LLM has something concrete to style.
    # Guard against None inputs so we never crash on missing data.
    item_desc = _format_item(new_item or {})

    items = (wardrobe or {}).get("items") or []

    if not items:
        # No wardrobe yet — offer general styling advice for the item alone.
        prompt = (
            "You are a thoughtful personal stylist for thrifted fashion.\n\n"
            f"A shopper is considering this second-hand find:\n{item_desc}\n\n"
            "They have not entered any wardrobe pieces yet, so you can't build a "
            "specific outfit from what they own. Instead, give friendly general "
            "styling advice: what kinds of pieces (tops, bottoms, shoes, "
            "accessories) pair well with it, what vibe or occasions it suits, and "
            "a couple of concrete example looks they could put together. Keep it "
            "to a short, encouraging paragraph or two."
        )
        return _call_llm(prompt)

    # Populated wardrobe — let the LLM build outfits from named pieces.
    wardrobe_lines = "\n".join(f"- {_format_item(item)}" for item in items)
    prompt = (
        "You are a thoughtful personal stylist for thrifted fashion.\n\n"
        f"A shopper is considering this second-hand find:\n{item_desc}\n\n"
        f"Here are the pieces already in their wardrobe:\n{wardrobe_lines}\n\n"
        "Suggest 1-2 complete outfits that build around the thrifted find, "
        "naming specific wardrobe pieces from the list above for each outfit. "
        "For every outfit, briefly explain the style/vibe it creates and how to "
        "wear it. If none of their pieces pair well with the find, say so "
        "honestly and offer general styling advice for the item instead. Keep "
        "the response concise and friendly."
    )
    return _call_llm(prompt)


def _format_item(item: dict) -> str:
    """Render a listing or wardrobe item dict into a compact one-line summary."""
    # Listings use 'title'; wardrobe items use 'name'.
    name = item.get("title") or item.get("name") or "Unnamed item"
    parts = [name]

    category = item.get("category")
    if category:
        parts.append(f"category: {category}")

    colors = item.get("colors")
    if colors:
        parts.append(f"colors: {', '.join(colors)}")

    tags = item.get("style_tags")
    if tags:
        parts.append(f"style: {', '.join(tags)}")

    price = item.get("price")
    if price is not None:
        parts.append(f"${price}")

    brand = item.get("brand")
    if brand:
        parts.append(f"brand: {brand}")

    notes = item.get("notes")
    if notes:
        parts.append(f"notes: {notes}")

    return " | ".join(parts)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    # Guard against an empty or whitespace-only outfit string. Without an
    # outfit there's nothing to caption, so return a descriptive error message
    # instead of crashing or calling the LLM.
    if not outfit or not outfit.strip():
        return (
            "Can't write a fit card: no outfit suggestion was provided. "
            "Run suggest_outfit first and pass its result in as `outfit`."
        )

    item = new_item or {}
    name = item.get("title") or item.get("name")
    price = item.get("price")
    platform = item.get("platform")

    # Build the item details block from whatever fields are available.
    detail_lines = []
    if name:
        detail_lines.append(f"Item: {name}")
    if price is not None:
        detail_lines.append(f"Price: ${price}")
    if platform:
        detail_lines.append(f"Platform: {platform}")
    colors = item.get("colors")
    if colors:
        detail_lines.append(f"Colors: {', '.join(colors)}")
    tags = item.get("style_tags")
    if tags:
        detail_lines.append(f"Style tags: {', '.join(tags)}")
    item_details = "\n".join(detail_lines) or "(no item details provided)"

    prompt = (
        "Write a short, shareable Instagram/TikTok caption (2-4 sentences) "
        "for a thrifted fashion find someone just scored.\n\n"
        f"Item details:\n{item_details}\n\n"
        f"The outfit they're styling it into:\n{outfit.strip()}\n\n"
        "Guidelines:\n"
        "- Sound casual and authentic, like a real OOTD post — NOT a product "
        "description.\n"
        "- Naturally mention the item's name, price, and platform once each.\n"
        "- Capture the outfit's vibe in specific terms.\n"
        "- Just return the caption text, no quotes or extra commentary."
    )

    # Higher temperature so different inputs (and re-runs) read distinctly.
    return _call_llm(prompt, temperature=0.9)

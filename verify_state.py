"""
verify_state.py

Verifies that state passes correctly through the planning loop:

  1. session["selected_item"]  == the new_item argument suggest_outfit received
  2. session["outfit_suggestion"] == the outfit argument create_fit_card received

We wrap suggest_outfit and create_fit_card so we capture the *exact* objects the
loop hands them, run the agent on the example query from planning.md, then
compare the captured arguments against the final session fields.

Run:
    ./.venv/Scripts/python.exe verify_state.py
"""

import agent
from utils.data_loader import get_example_wardrobe

# Example query straight from planning.md ("A Complete Interaction").
QUERY = (
    "I'm looking for a vintage graphic tee under $30. "
    "I mostly wear baggy jeans and chunky sneakers. "
    "What's out there and how would I style it?"
)

# Records what each tool was actually called with.
captured = {}

_real_suggest_outfit = agent.suggest_outfit
_real_create_fit_card = agent.create_fit_card


def spy_suggest_outfit(new_item, wardrobe):
    captured["suggest_outfit_new_item"] = new_item
    return _real_suggest_outfit(new_item, wardrobe)


def spy_create_fit_card(outfit, new_item):
    captured["create_fit_card_outfit"] = outfit
    return _real_create_fit_card(outfit, new_item)


# Patch the names the planning loop calls (it imported them into agent's namespace).
agent.suggest_outfit = spy_suggest_outfit
agent.create_fit_card = spy_create_fit_card

session = agent.run_agent(QUERY, get_example_wardrobe())

# `is` checks identity — proves the loop passed the very same object, not a copy.
selected_match = session["selected_item"] is captured.get("suggest_outfit_new_item")
outfit_match = session["outfit_suggestion"] is captured.get("create_fit_card_outfit")

lines = []
lines.append("=" * 70)
lines.append("STATE-PASSING VERIFICATION")
lines.append("=" * 70)
lines.append(f"\nQuery:\n  {QUERY}\n")
lines.append(f"Parsed: {session['parsed']}")
lines.append(f"Error:  {session['error']}")

lines.append("\n" + "-" * 70)
lines.append("CHECK 1: session['selected_item'] -> suggest_outfit(new_item)")
lines.append("-" * 70)
lines.append("\nsession['selected_item']:")
lines.append(f"  {session['selected_item']}")
lines.append("\nnew_item received by suggest_outfit:")
lines.append(f"  {captured.get('suggest_outfit_new_item')}")
lines.append(f"\nSame object passed through? {selected_match}  "
             f"(equal values: {session['selected_item'] == captured.get('suggest_outfit_new_item')})")

lines.append("\n" + "-" * 70)
lines.append("CHECK 2: session['outfit_suggestion'] -> create_fit_card(outfit)")
lines.append("-" * 70)
lines.append("\nsession['outfit_suggestion']:")
lines.append(f"  {session['outfit_suggestion']}")
lines.append("\noutfit received by create_fit_card:")
lines.append(f"  {captured.get('create_fit_card_outfit')}")
lines.append(f"\nSame object passed through? {outfit_match}")

lines.append("\n" + "-" * 70)
lines.append("FINAL FIT CARD")
lines.append("-" * 70)
lines.append(f"\n{session['fit_card']}")

lines.append("\n" + "=" * 70)
lines.append(f"RESULT: {'PASS — state passes correctly' if (selected_match and outfit_match) else 'FAIL — state mismatch'}")
lines.append("=" * 70)

report = "\n".join(lines)
print(report)

with open("state_verification.txt", "w", encoding="utf-8") as f:
    f.write(report + "\n")

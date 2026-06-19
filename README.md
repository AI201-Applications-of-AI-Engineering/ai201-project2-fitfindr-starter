# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

---

## Interaction Walkthrough

<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

**User query:**

**Step 1 — Tool called:**
- Tool: searching_listings
- Input: description: str, size: str | None = None, max_price: float | None = None
- Why this tool: Needed to search through all the listings, such that we are able to utilize AI to help find one that matches the user's request
- Output: list[dict], a listing of all matches

**Step 2 — Tool called:**
- Tool: suggest_outfit
- Input: new_item: dict, wardrobe: dict
- Why this tool: Utilized to help match clothes from the user's wardrobe with the matched listings
- Output: str

**Step 3 — Tool called:**
- Tool: create_fit_card
- Input: outfit: str, new_item: dict
- Why this tool: after matching a fit for the user with tool 1 and 2, create a description for the user
- Output: str

**Final output to user:**
A trendy description of the fit with the user's requested listing, alongside their clothes from their wardrobe.
---

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | there is no match for the user's description | returns an empty list |
| `suggest_outfit` | wardrobe is empty | offer general styling advice for the item |
| `create_fit_card` | outfit is empty/missing | return a descriptive error message string |

---

## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->

**One way planning.md helped during implementation:**

planning.md helped me plan all the layouts before I started coding. When I was confused and didn't know where to go, planning.md gave the steps on what to do and what to focus on. Furthermore, it helped break downt the steps as well, making sure that everything followed a guideline to address edge cases.

**One divergence from your spec, and why:**
I utilized Gemini to help me produce my architecture, feeding it tools and cases that are used within the app. Though the plan is kind of plan and not as descriptive as planning.md, it gives a framework for what the program will do.

---


## AI Usage

During the project, I utilized Claude to help analyze my answers to prompts in planning.md to make sure that I was approaching the prompts properly. Once I got it approved properly, I used Gemini to help me draw out the architecture, making sure that each part of it was done properly. If it was missing some datapoints or missed an edge case, I prompted it to fix the chart. After planning.md was fixed, I utilized Claude to help compare my answer to the instruction set. If they were similar, I was then set to ask it to help me generate the proper code, and once it was generated, I made sure that the code looked right and followed through with some testing. To make sure the code wasn't missing anything, I utilized Claude again to generate test cases, and paste the results in another file. I rinse and repeated this for all the tools, and eventually was able to finish this project, hopefully in the way that it was meant to be done.

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

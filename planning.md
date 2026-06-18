# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

This tool searches the listings in listings.json, trying to find any matches for the specific request made by the user.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): a description of the outfit
- `size` (str): how big the outfit will be
- `max_price` (float): the max price for the outfit

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
The results should return a JSON of the listings in listing.json, with the listings sorted by relevance, and returns results sorted by relevance. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If there are no listings matching the description, then it tells the user what to try differently.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
suggest_oufit takes an item and a wardrobe as an input, and finds a match for the item from the wardrobe. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): the item from the list as a dict (with all its values)
- `wardrobe` (dict): a wardrobe with other listings

**What it returns:**
<!-- Describe the return value -->
Returns a string explaining the pair it created and what style it fits. The string should advise the user how to style themselves with these clothes.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty, let the user know that there are currently nothing in the wardrobe, and offer general advice on what could go well with the listing selected.
If there are no pairs, it should explain it couldn't find a pair and offer general advice.

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
create_fit_card creates a short shareable description of a complete outfit, relatable to an Instagram story caption. Each usage must produce a different description for different inputs.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): the outfit returned by suggested_outfit
- `new_item` (dict): the clothes returned by search_listing

**What it returns:**
<!-- Describe the return value -->
Returns a string describing the outfit and how it looks/vibes via influencer style, like they just purchased the clothes.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If the outfit data is incomplete, the agent should talk only of the clothes listing.
If both are incomplete/missing, inform the user that there are no data to work with.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
The planning loop should start with a description filled out by the user on what they would like. Once that is filled, it's entered into search_listings for any potential matches. If do not have a result, we return an error message. If there is a result, we grab the top result (results[0]) and refer it to the next tool, suggest_outfit. 

From suggest_outfit, we take the previous result and use it as one of our args, and a wardrobe. The user can provide a wardrobe for us to use, or we will use an empty wardrobe. From here, the agent will find and match any clothes in the used wardrobe that forms a style for the user. If we are unable to find a match, we return an error message explaining the issue (not enough clothes, no style matches), and offer general advice on what to pair with it. If there is a match, we send the result to our final agent, create_fit_card.

Using the data from suggest_outfit, the agent will create a caption-like message for the user detailing on the new clothes from search_listing, and the style it was matched with. If there is no result, the agent can inform the user what sources are missing, and offer general advice on what it knows. If it does return a result, then we finally return the string description to the user.
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

All state for a single interaction lives in one `session` dict, created by `_new_session()` at the start of `run_agent()`. This dict is the single source of truth for the run — the planning loop reads from it and writes back to it at each step, so the tools themselves stay stateless (they just take inputs and return values).

The session tracks:
- `query` — the original user request.
- `parsed` — the description, size, and max_price extracted from the query.
- `search_results` — the list of matching listings returned by `search_listings`.
- `selected_item` — the top result, chosen from `search_results`.
- `wardrobe` — the user's wardrobe (or an empty one).
- `outfit_suggestion` — the string returned by `suggest_outfit`.
- `fit_card` — the final string returned by `create_fit_card`.
- `error` — set to a message if the run ends early; `None` on success.

Information passes between tools through this dict rather than directly between functions. The loop calls a tool, stores its return value in the matching session field, then reads that field to build the arguments for the next tool:
1. `search_listings(**session["parsed"])` → stored in `session["search_results"]`.
2. The loop picks `session["search_results"][0]` → stored in `session["selected_item"]`.
3. `suggest_outfit(session["selected_item"], session["wardrobe"])` → stored in `session["outfit_suggestion"]`.
4. `create_fit_card(session["outfit_suggestion"], session["selected_item"])` → stored in `session["fit_card"]`.

At any point, if a tool returns nothing usable, the loop sets `session["error"]` and returns the session early instead of calling the next tool with empty input. The caller inspects `session["error"]` first — if it's `None`, the output fields hold the completed result.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     Use ASCII art or a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html).
     Do NOT embed an image — graders need to read your diagram directly in the file;
     an embedded image or screenshot cannot be evaluated.
     You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

```
User query
    │
    ▼
Planning Loop ────────────────────────────────────────────────────────────────────────┐
    │                                                                                 │
    ├─► search_listings(description, size, max_price)                                 │
    │       │                                                                         │
    │       ├── results = []                                                          │
    │       │     └─► [ERROR] "No listings found..." ──► session["error"] ──► return  │
    │       │                                                                         │
    │       └── results = [item, ...]                                                 │
    │             ▼                                                                   │
    │         Session: selected_item = results[0]                                     │
    │                  search_results = results                                       │
    │       │                                                                         │
    │       ▼                                                                         │
    ├─► suggest_outfit(selected_item, wardrobe)                                       │
    │       │                                                                         │
    │       ├── wardrobe = []                                                         │
    │       │     └─► [FALLBACK] "Wardrobe empty..." ──► General advice string        │
    │       │                                                                         │
    │       └── outfit_suggestion = "..."                                             │
    │             ▼                                                                   │
    │         Session: outfit_suggestion = "..."                                      │
    │       │                                                                         │
    │       ▼                                                                         │
    └─► create_fit_card(outfit_suggestion, selected_item)                             │
            │                                                                         │
            └── fit_card = "..."                                                      │
                  ▼                                                                   │
              Session: fit_card = "..."                                               │
            │                                                                         │
            ▼                                                                         │
      Return session ◄────────────────────────────────────────────────────────────────┘
```
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

1. AI Tool
     - Will utilize Claude code to help plan/build the project, Gemini for general usage outside of the IDE.
2. Give as input
     - The AI will utilize what each tool's information above, and access the diagram to see how it's going to be utilized. From there, it will access the helper functions created, and build from there. 
     - Tool 1, Tool 2, Tool 3
          - utilize the inputs/outputs, description, and what it does
3. Expect to produce
     - I expect the AI to generate the proper code from the information above, which it will test itself to make sure it meets the testing criteria.
4.Verify output matches
     - I'll verify the output with the example given in the guide, alongside 2 random testings to make sure that all functionalities are there.


**Milestone 3 — Individual tool implementations:**

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
     The agent would use "search_listings", checking for a "vintage graphic tee" with max price "30", and return the results. If there are no results, it offers the user a separate suggestion off the data and stops. If there is a result, we scourge the top result to the next agent as an argument.
**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
     The returned listing from step 1 would then be processed and used as an arg in the tool "suggest_outfit", where the listing would be processed into the wardrobe to see if there are any matches. If there are no matches, the agent returns, apologize that there are no proper matches, and offer general advice on how to style it. If there is a match, we send the the result as an arg to the next agent.
**Step 3:**
<!-- Continue until the full interaction is complete -->
     Once the suggested oufit returns, we use the tool "create_fit_card" to piece together the listing from step 1 and the suggested outfit from the wardrobe in step 2. The agent would then return a modern trending description of the outfit, worthy of being shared online.
**Final output to user:**
<!-- What does the user actually see at the end? -->
     The user at the end sees the complete "fit card", matching the listing suggested from step 1 and the outfit from step 2, and the complete product with a modernized trendy description to go with it.
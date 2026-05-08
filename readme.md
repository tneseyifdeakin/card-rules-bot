# Sorcery: Contested Realm — Rules Bot

A RAG (Retrieval-Augmented Generation) chatbot that answers rules questions about the card game Sorcery: Contested Realm. Built as a learning project for Phase 2 of an AI Engineering roadmap.

## What it does

Ask a natural language question about the game rules. The bot searches a rules CSV (exported from the official Codex), retrieves the most relevant entries using TF-IDF scoring, and sends them as context to Claude Haiku to generate a structured JSON answer. Reference specific cards with `[[Card Name]]` to pull in card data from the card tracker database.

## How it works

1. **Rules loading** — Parses the Codex CSV into structured entries (title, content, subcodexes)
2. **IDF computation** — Computes Inverse Document Frequency scores for every word across all entries at startup (once, not per query)
3. **Card reference extraction** — Detects `[[Card Name]]` references in the user's question, looks up card data from the card tracker SQLite database, and injects card description keywords into the search query for better rule retrieval
4. **Search** — For each query:
   - Tokenises and normalises the query (lowercase, punctuation stripped)
   - Removes English stop words
   - Expands keywords using a synonym map (e.g. "play" also searches "cast", "casting")
   - Scores each entry using TF-IDF with length normalisation to prevent long entries dominating
   - Returns the top 8 results
5. **Context formatting** — Structures retrieved entries and any referenced card data into a text block for the LLM
6. **LLM response** — Claude Haiku answers using only the provided rules, returning structured JSON with answer, rules, and optional exceptions
7. **Web UI** — FastAPI serves a browser-based interface for asking questions and viewing formatted responses

## Architecture decisions

**TF-IDF over naive keyword scoring** — The initial implementation used a simple point system (+1 for content match, +3 for title match, etc). This caused two problems: common game terms like "play" and "cards" generated noise across most entries, and long entries like Ongoing Effect (1,500+ words) dominated results regardless of relevance. TF-IDF with length normalisation solved both — token usage dropped from ~7,000 to ~1,300 per query.

**Synonym expansion** — Keyword search can't bridge vocabulary mismatches. A user asking "can I play cards on my opponent's turn" won't match "Casting Spells" because the rules use "cast" not "play". A manually maintained synonym map expands queries before search.

**Length normalisation with a floor** — Dividing TF-IDF scores by entry length prevents long entries from accumulating unfair scores, but very short entries (7-13 words) get over-inflated. A minimum length floor of 50 words caps this effect.

**Structured JSON output** — The LLM returns JSON with `answer`, `rules` (array), and optional `exceptions` (array) keys rather than freeform text. This makes responses parseable by code and enables the web UI to style each section independently. A belt-and-braces approach handles markdown fencing the model occasionally adds.

**Card reference resolution** — Rules entries reference cards with `[[Card Name]]` notation. These are extracted via regex, looked up in the card tracker's SQLite database, and included in the LLM context. When users reference cards in their question, the card's description keywords are also injected into the search to find relevant rules (e.g. asking about `[[Dodge Roll]]` also searches for "attack", "move", "adjacent").

**Shared database** — The card tracker's `card.db` is used as a single source of truth rather than copying it, so card data stays current as the tracker updates.

## Known limitations

- **Vocabulary mismatch** — Even with synonyms, keyword search fundamentally cannot connect concepts described with entirely different words. Semantic search (embeddings) would solve this but is out of scope for this phase.
- **Synonym map is manual** — New game terms or alternative phrasings require manual additions.
- **No conversation memory** — Each question is independent. Follow-up questions like "what about sites?" don't carry context from the previous answer.
- **Card name matching is case-sensitive** — `[[Dodge Roll]]` works but `[[dodge roll]]` may not find the card in the database.
- **LLM output type inconsistency** — The model occasionally returns rules or exceptions as a string instead of an array. The frontend handles both types defensively.

## Project structure

```
card-rules-bot/
├── data/
│   └── codex-27 Apr 2026.csv    # Rules data from official Codex
├── static/
│   └── index.html               # Web UI frontend
├── src/
│   ├── app.py                   # FastAPI application and endpoints
│   ├── config.py                # Environment variable loading
│   ├── rules_bot.py             # LLM integration, prompt, card resolution
│   └── rules_loader.py          # CSV parsing, TF-IDF, search, synonyms
├── .env                         # API key and paths (not committed)
├── .gitignore
├── pyproject.toml               # Ruff and mypy configuration
└── README.md
```

## How to run

Requires Python 3.13, an Anthropic API key, and the card tracker database.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install anthropic python-dotenv fastapi uvicorn
```

Create a `.env` file:
```
ANTHROPIC_API_KEY=your-key-here
DATABASE_PATH=C:\path\to\card-price-tracker\data\cards.db
RULES_CSV_PATH=C:\path\to\card-rules-bot\data\codex-27 Apr 2026.csv
```

Run the web UI:
```bash
cd src
uvicorn app:app --reload
```
Then open `http://127.0.0.1:8000` in your browser.

Run the CLI bot:
```bash
python src/rules_bot.py
```

Run search directly (without LLM, for testing retrieval):
```bash
python src/rules_loader.py
```

## What I learned

- TF-IDF from scratch — understanding why term frequency alone isn't enough and how inverse document frequency down-weights common terms
- The tradeoff between search precision and token cost in RAG systems
- Length normalisation to handle entries of wildly different sizes (7 to 1,700+ words)
- Synonym expansion as a lightweight fix for vocabulary mismatch before committing to embeddings
- Prompt engineering — structured output formats, explicit instructions, XML tags for section boundaries, conditional sections, conciseness constraints
- Structured outputs — getting an LLM to return parseable JSON reliably, and defending against format inconsistencies
- Card reference resolution — connecting two separate projects through a shared database, using card data to enhance both search and LLM context
- Belt-and-braces error handling — always validate LLM output before trusting it
- FastAPI for serving both an API and a static frontend
- The gap between keyword search and semantic search — understanding exactly why embeddings matter for Phase 3

## Future improvements

- [ ] Embeddings-based search to replace TF-IDF (Phase 3)
- [ ] Evaluation suite with scored test questions
- [ ] Case-insensitive card name matching
- [ ] Conversation memory for follow-up questions
- [ ] Deployment to a public URL

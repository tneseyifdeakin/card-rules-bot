# Sorcery: Contested Realm — Rules Bot

A RAG (Retrieval-Augmented Generation) chatbot that answers rules questions about the card game Sorcery: Contested Realm. Built as a learning project for Phase 2 of an AI Engineering roadmap.

## What it does

Ask a natural language question about the game rules. The bot searches a rules CSV (exported from the official Codex), retrieves the most relevant entries using TF-IDF scoring, and sends them as context to Claude Haiku to generate an answer.

```
Ask a rules question (or 'quit' to exit): how does airborne work?

Answer:
Airborne units fly above the ground and can move over obstacles and other units.
Rules:
"Airborne units are flying units that move through air sites."
```

## How it works

1. **Rules loading** — Parses the Codex CSV into structured entries (title, content, subcodexes)
2. **IDF computation** — Computes Inverse Document Frequency scores for every word across all entries at startup (once, not per query)
3. **Search** — For each query:
   - Tokenises and normalises the query (lowercase, punctuation stripped)
   - Removes English stop words
   - Expands keywords using a synonym map (e.g. "play" also searches "cast", "casting")
   - Scores each entry using TF-IDF with length normalisation to prevent long entries dominating
   - Returns the top 8 results
4. **Context formatting** — Structures retrieved entries into a text block for the LLM
5. **LLM response** — Claude Haiku answers using only the provided rules, in a structured Answer/Rules/Exception format

## Architecture decisions

**TF-IDF over naive keyword scoring** — The initial implementation used a simple point system (+1 for content match, +3 for title match, etc). This caused two problems: common game terms like "play" and "cards" generated noise across most entries, and long entries like Ongoing Effect (1,500+ words) dominated results regardless of relevance. TF-IDF with length normalisation solved both — token usage dropped from ~7,000 to ~1,300 per query.

**Synonym expansion** — Keyword search can't bridge vocabulary mismatches. A user asking "can I play cards on my opponent's turn" won't match "Casting Spells" because the rules use "cast" not "play". A manually maintained synonym map expands queries before search.

**Length normalisation with a floor** — Dividing TF-IDF scores by entry length prevents long entries from accumulating unfair scores, but very short entries (7-13 words) get over-inflated. A minimum length floor of 50 words caps this effect.

## Known limitations

- **Vocabulary mismatch** — Even with synonyms, keyword search fundamentally cannot connect concepts described with entirely different words. The "Casting Spells" entry remains hard to surface for some phrasings. Semantic search (embeddings) would solve this but is out of scope for this phase.
- **Synonym map is manual** — New game terms or alternative phrasings require manual additions.
- **No conversation memory** — Each question is independent. Follow-up questions like "what about sites?" don't carry context from the previous answer.
- **Prompt engineering is in progress** — Output format and conciseness are improved but not finalised.

## Project structure

```
card-rules-bot/
├── data/
│   └── codex-27 Apr 2026.csv    # Rules data from official Codex
├── src/
│   ├── config.py                 # Environment variable loading
│   ├── rules_loader.py           # CSV parsing, TF-IDF, search, synonyms
│   └── rules_bot.py              # LLM integration and prompt
├── .env                          # API key (not committed)
├── .gitignore
└── README.md
```

## How to run

Requires Python 3.13 and an Anthropic API key.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install anthropic python-dotenv
```

Create a `.env` file:
```
ANTHROPIC_API_KEY=your-key-here
```

Run the bot:
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
- Prompt engineering basics — structured output formats, explicit instructions, XML tags for section boundaries
- The gap between "works on my machine" retrieval and production-quality RAG (embeddings, evaluation suites) — understanding why Phase 3 exists

## Roadmap

- [ ] Prompt engineering refinement (conciseness, conditional sections)
- [ ] Structured outputs from LLM
- [ ] Card reference resolution (e.g. [[Dodge Roll]] → card details)
- [ ] TF-IDF replacement with embeddings (Phase 3)
- [ ] FastAPI web UI
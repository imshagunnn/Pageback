# PageBack

Remember what happened. Read on.

PageBack is a literary memory layer for novels you pause mid-read. It keeps characters, events, and details up to your current chapter, then offers spoiler-safe recaps.

This README will expand in Phase 12 (schema, API, AI pipeline). Phase 1 is project setup.

## Requirements

- Python 3.12+ (developed on 3.14)
- A virtual environment

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

Set `SECRET_KEY` and `GEMINI_API_KEY` in `.env`. PageBack uses the official Google Gemini SDK for chapter analysis, recaps, and embeddings.

```bash
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/

- Landing page: `/`
- API health: `/api/health/`
- Admin: `/admin/`
- OpenAPI (after more endpoints exist): `/api/docs/`

## Tests

```bash
pytest
```

## Django apps

| App | Role |
|---|---|
| `config` | Project settings and URLs |
| `novels` | Books and chapters |
| `story` | Extracted narrative memory |
| `reading` | Progress, recaps, chat |
| `api` | REST API |
| `web` | Templates |
| `ai` | LLM provider, prompts, RAG (Python package) |

See `docs/IMPLEMENTATION_PLAN.md` for the full architecture.

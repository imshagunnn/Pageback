# PageBack implementation plan

Brand: **PageBack — Remember what happened. Read on.**

The product is a memory layer for the novel the user is reading. It is not a chatbot wrapper, a library catalog, or a generic summarizer.

## Repository status

The workspace was empty. PageBack is being built at the repository root (no existing project to preserve).

Phase 1 is complete: Django 6.0.8 boots, SQLite migrations apply, landing page and `/api/health/` return 200, three pytest checks pass.

## Architecture

```
config/     Django project (settings, root URLs)
novels/     Novel, Chapter, EmbeddingChunk
story/      Characters, relationships, events, locations, details, themes
reading/    Progress, sessions, recaps, chat
api/        Django REST Framework
web/        Templates and page views
ai/         Provider-agnostic pipeline (not mixed into views)
```

Views coordinate HTTP. Services in each app call `ai/` for generation. The OpenAI key is read from the environment only.

## Spoiler protection

`ReadingProgress.current_chapter` is the **READING_BOUNDARY**.

1. Database queries use `chapter_number <= boundary` (or an explicit range that is also capped).
2. Vector retrieval applies the same metadata filter.
3. Prompts include the boundary and forbidden-chapter instruction.
4. Tests assert that chapter 4+ never appears when the boundary is 3.

The LLM is a last line of defense, not the only one.

## Database (planned)

| Model | Purpose |
|---|---|
| Novel | Title, author, genre, cover, owner |
| Chapter | Number unique per novel, text, word count, processing_status |
| Character | Name, aliases, role, first appearance |
| CharacterRelationship | Typed edge, confidence, first/last detected chapter |
| RelationshipState | Chapter-by-chapter relationship evolution |
| Event | Typed, importance, characters, location, sequence |
| Location | Meaningful places |
| ImportantDetail | Reader-memory details |
| ThemeMotif | Only when the chapter supports it |
| ReadingProgress | Spoiler boundary + status |
| ReadingSession | Session timing |
| Recap | Cached recaps + structured JSON |
| ChatThread / ChatMessage | Story Q&A |
| EmbeddingChunk | Chunk text, vector, novel/chapter metadata |

Added vs the spec (documented decisions):

- `Novel.owner` so uploads stay private.
- `Chapter.processing_status` for analysis UX.
- `RelationshipState` for relationship timelines.
- `EmbeddingChunk` for local RAG.
- Chat models for the Ask page.

## API

Envelope:

```json
{ "success": true, "data": {}, "message": "" }
```

Errors: `{ "success": false, "error": { "code": "...", "message": "..." } }`

Core routes live under `/api/` (novels, chapters, characters, events, relationships, progress, sessions, recaps, ask, timeline, network). OpenAPI via drf-spectacular.

## AI pipeline

```
Chapter text → preprocess → LLM JSON extract → validate
  → save entities → chunk → embed → store EmbeddingChunk
```

Recap / chat:

```
boundary → structured rows (≤ boundary) → spoiler-safe chunks → prompt → cache
```

Provider: `AIProvider` with `OpenAICompatibleProvider`. Swap later without touching views.

Vector v1: numpy cosine similarity over stored vectors. FAISS / pgvector can replace the retriever class later. FAISS is not in Phase 1 because Windows + Python 3.14 packaging is unreliable.

## Frontend

Django templates, calm literary CSS, fetch() for recaps/chat/graphs. Cytoscape.js for the character map. No React.

## Phases

See the architecture canvas and the checklist in the README (expanded in Phase 12). Execute one phase at a time; verify before continuing.

## Not in v1

Celery, Redis, Docker, Kubernetes, EPUB/PDF as a primary feature, voice recaps, prediction mode, personal notes AI.

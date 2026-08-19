# PageBack

**PageBack — Remember what happened. Read on.**

PageBack is a reading companion for people who pause a novel and later forget where they stopped. It imports books, preserves reading progress, creates spoiler-safe recaps, and helps readers remember characters, events, relationships, themes, and important details.

## What It Does

- Account creation, login, logout, and private libraries
- TXT, Markdown, PDF, and EPUB book import
- Automatic chapter and section extraction
- Reading boundary selection and chapter-range recaps
- 30-second, 2-minute, and 5-minute catch-up views
- Character profiles and first-appearance tracking
- Themes, story details, and structured chapter analysis
- Boundary-safe story questions and recap caching
- Embedding chunks and retrieval filtered by the reader's chapter boundary
- Public White Nights demo without an account
- Health endpoint and OpenAPI documentation

## Technology Stack

- **Backend:** Python 3.12+, Django 6, Django REST Framework
- **Database:** SQLite for development, PostgreSQL-ready configuration
- **Frontend:** Django templates, HTML, CSS, vanilla JavaScript
- **AI layer:** Provider abstraction, structured JSON generation, embeddings, and local fallback analysis
- **Document processing:** `pypdf` for PDF, `ebooklib` and BeautifulSoup for EPUB, UTF-8 text and Markdown support
- **Retrieval:** Database-backed chapter chunks with spoiler-safe filtering and optional vectors
- **Testing:** pytest, pytest-django, Django system checks
- **Configuration:** `.env` environment variables via `python-dotenv`

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

Set the secret key and local AI credentials in `.env`. Never commit `.env`; it is ignored by Git. The app falls back to local analysis when an external provider is unavailable.

## Main Routes

| Route | Purpose |
|---|---|
| `/` | Landing page or authenticated dashboard |
| `/accounts/signup/` | Create an account |
| `/accounts/login/` | Sign in |
| `/dashboard/` | Private reading library |
| `/novels/import/` | Import a book |
| `/novels/<id>/` | Book dashboard and spoiler boundary |
| `/demo/` | Public interactive White Nights demo |
| `/api/health/` | API health check |
| `/api/docs/` | OpenAPI documentation |

## Spoiler Protection

The selected reading chapter is stored in `ReadingProgress`. Analysis context and retrieval queries filter chapters in the database before content is sent to the AI layer:

```text
Reader boundary: chapter 5
Allowed: chapters 1–5
Forbidden: chapter 6 and later
```

Prompts reinforce this rule, but the database filter is the primary protection.

## Development

```powershell
pytest
python manage.py check
python manage.py makemigrations --check --dry-run
```

| App | Responsibility |
|---|---|
| `config` | Django settings and project URLs |
| `novels` | Books, chapters, imports, and embedding chunks |
| `reading` | Reading progress, boundaries, sessions, and cached recaps |
| `story` | Characters, relationships, events, themes, and details |
| `ai` | Provider abstraction, analysis, embeddings, and retrieval |
| `api` | REST API and health endpoint |
| `web` | Page views and templates |

## Security

- Keep API credentials only in `.env`.
- Do not commit database files, uploaded books, or generated local indexes.
- Revoke any credential that has been exposed and replace it before deployment.
- The development server is not suitable for production use.

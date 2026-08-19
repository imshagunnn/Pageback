from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from novels.models import Chapter, EmbeddingChunk, Novel
from reading.models import ReadingProgress
from reading.models import Recap
from story.models import Character


def test_landing_page(client):
    response = client.get(reverse("landing"))
    assert response.status_code == 200
    assert b"PageBack" in response.content
    assert b"Forgot where you left off?" in response.content
    assert b"Create account" in response.content
    assert b"Explore demo" in response.content
    assert reverse("signup").encode() in response.content
    assert reverse("demo").encode() in response.content


def test_authenticated_user_visiting_home_is_sent_to_dashboard(client, db):
    user = User.objects.create_user(username="returning_reader", password="Pageback-check-2026")
    client.force_login(user)
    response = client.get(reverse("landing"))
    assert response.status_code == 302
    assert response.url == reverse("dashboard")


def test_signup_and_demo_pages(client):
    assert client.get(reverse("signup")).status_code == 200
    demo = client.get(reverse("demo"))
    assert demo.status_code == 200
    assert b"White Nights" in demo.content
    assert b"Create an account" in demo.content or b"create an account" in demo.content


def test_signup_creates_user_and_lands_on_dashboard(client, db):
    response = client.post(
        reverse("signup"),
        {
            "username": "nastenka",
            "password1": "white-nights-pass-92",
            "password2": "white-nights-pass-92",
        },
    )
    assert response.status_code == 302
    assert response.url == reverse("dashboard")
    follow = client.get(reverse("dashboard"))
    assert follow.status_code == 200
    assert b"Your library" in follow.content


def test_authenticated_user_can_import_novel_from_text_file(client, db, settings):
    settings.PAGEBACK_AI["api_key"] = ""
    user = User.objects.create_user(username="reader", password="Pageback-check-2026")
    client.force_login(user)
    upload = SimpleUploadedFile(
        "little-book.txt",
        b"The first chapter begins here.",
        content_type="text/plain",
    )

    response = client.post(
        reverse("import_novel"),
        {"title": "Little Book", "author": "A Reader", "text_file": upload},
    )

    assert response.status_code == 302
    assert response.url.startswith("/novels/")
    novel = Novel.objects.get(owner=user)
    assert novel.title == "Little Book"
    assert novel.total_chapters == 1
    chapter = Chapter.objects.get(novel=novel)
    assert chapter.word_count == 5
    assert chapter.processing_status == "pending"
    analysis_response = client.post(response.url, {"from_chapter": 1, "through_chapter": 1})
    assert analysis_response.status_code == 302
    novel.refresh_from_db()
    assert novel.analysis["summary"] == "The first chapter begins here."
    detail = client.get(response.url)
    assert detail.status_code == 200
    assert b"Catch me up" in detail.content
    assert b'max="1"' in detail.content
    assert b"30 seconds" in detail.content
    assert b"Ask about the story" in detail.content


def test_existing_multi_chapter_book_accepts_chapter_six(client, db):
    user = User.objects.create_user(username="multi_reader", password="Pageback-check-2026")
    novel = Novel.objects.create(owner=user, title="Many Chapters")
    for chapter_number in range(1, 10):
        Chapter.objects.create(novel=novel, chapter_number=chapter_number, content=f"Chapter {chapter_number} begins.")
    client.force_login(user)

    detail = client.get(reverse("novel_detail", kwargs={"novel_id": novel.id}))
    assert f'max="9"'.encode() in detail.content
    response = client.post(reverse("novel_detail", kwargs={"novel_id": novel.id}), {"from_chapter": 2, "through_chapter": 6})
    assert response.status_code == 302
    novel.refresh_from_db()
    assert novel.analysis_boundary == 6
    progress = ReadingProgress.objects.get(user=user, novel=novel)
    assert progress.boundary_chapter_number == 6
    assert Recap.objects.filter(user=user, novel=novel, from_chapter=2, to_chapter=6).count() == 3


def test_analysis_boundary_excludes_future_chapters(client, db):
    user = User.objects.create_user(username="spoiler_reader", password="Pageback-check-2026")
    novel = Novel.objects.create(owner=user, title="Boundary Book")
    for chapter_number in range(1, 7):
        Chapter.objects.create(
            novel=novel,
            chapter_number=chapter_number,
            content=f"Allowed chapter {chapter_number}. Future marker {chapter_number}.",
        )
    client.force_login(user)
    client.post(reverse("novel_detail", kwargs={"novel_id": novel.id}), {"from_chapter": 1, "through_chapter": 5})
    progress = ReadingProgress.objects.get(user=user, novel=novel)
    assert progress.current_chapter.chapter_number == 5
    allowed = list(novel.chapters.filter(chapter_number__lte=progress.boundary_chapter_number))
    assert len(allowed) == 5
    assert not any("chapter 6" in chapter.content for chapter in allowed)


def test_rag_retrieval_filters_future_chapters_at_database_boundary(db):
    from ai.embeddings import store_chapter_chunks
    from ai.rag import retrieve

    user = User.objects.create_user(username="rag_reader", password="Pageback-check-2026")
    novel = Novel.objects.create(owner=user, title="RAG Book")
    first = Chapter.objects.create(novel=novel, chapter_number=1, content="The blue key appears.")
    future = Chapter.objects.create(novel=novel, chapter_number=6, content="The blue key opens the secret door.")
    store_chapter_chunks(first, [first.content])
    store_chapter_chunks(future, [future.content])

    results = retrieve(novel, boundary=5, query="blue key")
    assert [result.chapter.chapter_number for result in results] == [1]
    assert not EmbeddingChunk.objects.filter(chapter__chapter_number__gt=5, id__in=[result.id for result in results]).exists()


def test_gemini_embedding_uses_provider_abstraction(monkeypatch, settings):
    from ai import embeddings

    settings.PAGEBACK_AI["api_key"] = "configured"

    class FakeProvider:
        def __init__(self, **_kwargs):
            pass

        def embed(self, text):
            assert text == "chapter text"
            return [0.1, 0.2]

    monkeypatch.setattr(embeddings, "GeminiProvider", FakeProvider)
    assert embeddings.embed_with_gemini("chapter text") == [0.1, 0.2]


def test_import_requires_authentication(client):
    response = client.get(reverse("import_novel"))
    assert response.status_code == 302
    assert reverse("login") in response.url


def test_api_health(client):
    response = client.get("/api/health/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["service"] == "PageBack"


def test_ai_provider_interface_is_abstract():
    from ai.client import AIProvider

    assert AIProvider.__abstractmethods__ == frozenset(
        {"generate", "generate_structured", "embed"}
    )


def test_ai_fallback_explains_provider_failure(monkeypatch, settings):
    from ai import analyzer

    settings.PAGEBACK_AI["api_key"] = "configured"

    class FailingProvider:
        def __init__(self, **_kwargs):
            pass

        def generate_structured(self, *_args, **_kwargs):
            raise RuntimeError("Gemini provider unavailable")

    monkeypatch.setattr(analyzer, "GeminiProvider", FailingProvider)
    result = analyzer.analyze_text_with_ai("A short chapter.", "Book", 1)
    assert result["provider"] == "local"
    assert "could not be reached" in result["ai_error"]

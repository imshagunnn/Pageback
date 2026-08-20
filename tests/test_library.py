from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from novels.models import Chapter, Collection, Novel, NovelStatus
from reading.models import ReadingProgress


def make_book(user, title="Library Book", count=2):
    novel = Novel.objects.create(owner=user, title=title)
    for number in range(1, count + 1):
        Chapter.objects.create(novel=novel, chapter_number=number, title=f"Chapter {number}", content=f"Story {number}.")
    return novel


def test_library_is_private_to_each_user(client, db):
    owner = User.objects.create_user(username="owner", password="Pageback-check-2026")
    other = User.objects.create_user(username="other", password="Pageback-check-2026")
    make_book(owner, "Private Book")
    make_book(other, "Other Book")
    client.force_login(owner)

    response = client.get(reverse("dashboard"))

    assert b"Private Book" in response.content
    assert b"Other Book" not in response.content


def test_completion_archive_trash_restore_and_permanent_delete(client, db, settings):
    settings.PAGEBACK_AI["api_key"] = ""
    user = User.objects.create_user(username="lifecycle", password="Pageback-check-2026")
    novel = make_book(user, count=2)
    client.force_login(user)

    response = client.post(reverse("novel_detail", kwargs={"novel_id": novel.id}), {"from_chapter": 1, "through_chapter": 2})
    assert response.status_code == 302
    novel.refresh_from_db()
    assert novel.status == NovelStatus.COMPLETED
    assert b"Completed" in client.get(reverse("dashboard") + "?section=completed").content

    client.post(reverse("library_action", kwargs={"novel_id": novel.id}), {"action": "archive"})
    novel.refresh_from_db()
    assert novel.status == NovelStatus.ARCHIVED
    assert novel.chapters.count() == 2
    assert b"Library Book" not in client.get(reverse("dashboard") + "?section=all").content
    assert b"Library Book" in client.get(reverse("dashboard") + "?section=archive").content

    client.post(reverse("library_action", kwargs={"novel_id": novel.id}), {"action": "restore"})
    novel.refresh_from_db()
    assert novel.status == NovelStatus.COMPLETED

    client.post(reverse("library_action", kwargs={"novel_id": novel.id}), {"action": "trash"})
    novel.refresh_from_db()
    assert novel.status == NovelStatus.TRASHED
    assert novel.chapters.exists()
    assert novel.id in list(Novel.objects.filter(status=NovelStatus.TRASHED).values_list("id", flat=True))

    client.post(reverse("library_action", kwargs={"novel_id": novel.id}), {"action": "restore"})
    novel.refresh_from_db()
    assert novel.status == NovelStatus.COMPLETED
    client.post(reverse("library_action", kwargs={"novel_id": novel.id}), {"action": "trash"})
    client.post(reverse("library_action", kwargs={"novel_id": novel.id}), {"action": "permanent_delete"})
    assert not Novel.objects.filter(id=novel.id).exists()


def test_favorites_and_multiple_collections_are_independent(client, db):
    user = User.objects.create_user(username="collector", password="Pageback-check-2026")
    novel = make_book(user, "Collected Book")
    client.force_login(user)

    client.post(reverse("library_action", kwargs={"novel_id": novel.id}), {"action": "favorite"})
    novel.refresh_from_db()
    assert novel.is_favorite is True
    client.post(reverse("library_action", kwargs={"novel_id": novel.id}), {"action": "favorite"})
    novel.refresh_from_db()
    assert novel.is_favorite is False

    client.post(reverse("create_collection"), {"name": "Classics"})
    client.post(reverse("create_collection"), {"name": "Russian Literature"})
    first, second = Collection.objects.filter(owner=user).order_by("name")
    client.post(reverse("library_action", kwargs={"novel_id": novel.id}), {"action": "collections", "collection_ids": [first.id, second.id]})
    assert set(novel.collections.values_list("id", flat=True)) == {first.id, second.id}

    client.post(reverse("collection_detail", kwargs={"collection_id": first.id}), {"novel_id": novel.id})
    assert novel.collections.filter(id=first.id).exists() is False
    assert novel.collections.filter(id=second.id).exists() is True
    assert Novel.objects.filter(id=novel.id).exists()


def test_duplicate_upload_is_rejected_for_same_user(client, db, settings):
    settings.PAGEBACK_AI["api_key"] = ""
    user = User.objects.create_user(username="duplicate", password="Pageback-check-2026")
    client.force_login(user)
    payload = b"A unique book source."

    first = client.post(reverse("import_novel"), {"title": "Unique", "author": "Author", "text_file": SimpleUploadedFile("book.txt", payload)})
    second = client.post(reverse("import_novel"), {"title": "Unique Again", "author": "Author", "text_file": SimpleUploadedFile("book.txt", payload)})

    assert first.status_code == 302
    assert second.status_code == 200
    assert User.objects.get(username="duplicate").novels.count() == 1
    assert b"already in your library" in second.content

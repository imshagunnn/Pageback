import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from novels.models import Chapter, Novel
from reading.models import ReadingProgress, Recap, RecapType
from story.models import Character, CharacterRelationship, Event, EventType, Importance

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="reader", password="test-pass-123")


@pytest.fixture
def novel(user):
    return Novel.objects.create(owner=user, title="White Nights", author="Fyodor Dostoevsky")


def test_chapter_numbers_unique_per_novel(novel):
    Chapter.objects.create(novel=novel, chapter_number=1, title="Night 1", content="The narrator walks.")
    with pytest.raises(IntegrityError):
        Chapter.objects.create(novel=novel, chapter_number=1, title="Duplicate", content="Nope.")


def test_chapter_word_count_and_novel_total(novel):
    chapter = Chapter.objects.create(
        novel=novel,
        chapter_number=1,
        title="Night 1",
        content="The narrator walks the streets of St Petersburg at night.",
    )
    novel.refresh_from_db()
    assert chapter.word_count > 0
    assert novel.total_chapters == 1


def test_character_and_relationship(novel):
    ch1 = Chapter.objects.create(novel=novel, chapter_number=1, title="Night 1", content="He meets Nastenka.")
    narrator = Character.objects.create(novel=novel, name="Narrator", role="dreamer", first_appearance=ch1)
    nastenka = Character.objects.create(novel=novel, name="Nastenka", role="young woman", first_appearance=ch1)
    rel = CharacterRelationship.objects.create(
        novel=novel,
        source_character=narrator,
        target_character=nastenka,
        relationship_type="friend of",
        first_detected_chapter=ch1,
        last_updated_chapter=ch1,
    )
    assert "Nastenka" in str(rel)


def test_event_belongs_to_chapter(novel):
    ch1 = Chapter.objects.create(novel=novel, chapter_number=1, title="Night 1", content="Meeting.")
    event = Event.objects.create(
        novel=novel,
        chapter=ch1,
        title="Meeting on the embankment",
        description="The narrator meets Nastenka.",
        event_type=EventType.MEETING,
        importance=Importance.CRITICAL,
        sequence_order=1,
    )
    assert event.chapter.chapter_number == 1


def test_reading_progress_is_unique_and_exposes_boundary(user, novel):
    ch1 = Chapter.objects.create(novel=novel, chapter_number=1, title="Night 1", content="One.")
    Chapter.objects.create(novel=novel, chapter_number=2, title="Night 2", content="Two.")
    progress = ReadingProgress.objects.create(user=user, novel=novel, current_chapter=ch1)
    assert progress.boundary_chapter_number == 1
    with pytest.raises(IntegrityError):
        ReadingProgress.objects.create(user=user, novel=novel, current_chapter=ch1)


def test_recap_cache_row(user, novel):
    Chapter.objects.create(novel=novel, chapter_number=1, title="Night 1", content="One two three.")
    recap = Recap.objects.create(
        user=user,
        novel=novel,
        from_chapter=1,
        to_chapter=1,
        recap_type=RecapType.QUICK_30,
        content="The narrator walks at night.",
        structured_data={"bullets": []},
        source_updated_at=novel.chapters.first().updated_at,
    )
    assert recap.recap_type == RecapType.QUICK_30

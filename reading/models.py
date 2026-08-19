"""Reader state: progress (the spoiler boundary), sessions, and cached recaps."""

from django.conf import settings
from django.db import models

from novels.models import Chapter, Novel


class ReadingStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not started"
    READING = "reading", "Reading"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"


class RecapType(models.TextChoices):
    QUICK_30 = "quick_30", "30-second recap"
    STANDARD_2MIN = "standard_2min", "2-minute recap"
    DETAILED_5MIN = "detailed_5min", "5-minute recap"


class ReadingProgress(models.Model):
    """current_chapter is the spoiler boundary: AI may use chapters 1..N only."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reading_progress",
    )
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="reading_progress")
    current_chapter = models.ForeignKey(
        Chapter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="progress_markers",
    )
    last_read_at = models.DateTimeField(blank=True, null=True)
    reading_status = models.CharField(
        max_length=20,
        choices=ReadingStatus.choices,
        default=ReadingStatus.NOT_STARTED,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "novel"], name="unique_progress_per_user_novel"),
        ]

    def __str__(self) -> str:
        chapter = self.current_chapter.chapter_number if self.current_chapter else 0
        return f"{self.user} / {self.novel} @ {chapter}"

    @property
    def boundary_chapter_number(self) -> int:
        if self.current_chapter is None:
            return 0
        return self.current_chapter.chapter_number


class ReadingSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reading_sessions",
    )
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="reading_sessions")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="reading_sessions")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.user} session on {self.novel} ch.{self.chapter.chapter_number}"


class Recap(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recaps",
    )
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="recaps")
    from_chapter = models.PositiveIntegerField()
    to_chapter = models.PositiveIntegerField()
    recap_type = models.CharField(max_length=20, choices=RecapType.choices)
    content = models.TextField()
    structured_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source_updated_at = models.DateTimeField(
        help_text="Latest chapter updated_at at generation time; used to invalidate cache.",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "novel", "from_chapter", "to_chapter", "recap_type"],
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_recap_type_display()} {self.novel} {self.from_chapter}-{self.to_chapter}"

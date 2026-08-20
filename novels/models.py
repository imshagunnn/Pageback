"""Novels and chapters.

A Novel is owned by one user. Chapters belong to one novel, and chapter_number
is unique within that novel.
"""

from django.conf import settings
from django.db import models


class ProcessingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class Novel(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="novels",
    )
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    genre = models.CharField(max_length=120, blank=True)
    cover_image = models.ImageField(upload_to="covers/", blank=True, null=True)
    language = models.CharField(max_length=32, blank=True, default="en")
    publication_year = models.PositiveIntegerField(blank=True, null=True)
    total_chapters = models.PositiveIntegerField(default=0)
    analysis_boundary = models.PositiveIntegerField(default=1)
    analysis = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["owner", "title"]),
        ]

    def __str__(self) -> str:
        return self.title

    def refresh_chapter_count(self) -> None:
        count = self.chapters.count()
        if self.total_chapters != count:
            self.total_chapters = count
            self.save(update_fields=["total_chapters", "updated_at"])


class Chapter(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="chapters")
    chapter_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    source_page_start = models.PositiveIntegerField(blank=True, null=True)
    source_page_end = models.PositiveIntegerField(blank=True, null=True)
    content_type = models.CharField(max_length=32, default="chapter")
    parent_title = models.CharField(max_length=255, blank=True)
    word_count = models.PositiveIntegerField(default=0)
    summary = models.TextField(blank=True)
    analysis = models.JSONField(default=dict, blank=True)
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )
    processing_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["chapter_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["novel", "chapter_number"],
                name="unique_chapter_number_per_novel",
            ),
        ]
        indexes = [
            models.Index(fields=["novel", "chapter_number"]),
        ]

    def __str__(self) -> str:
        label = self.title or f"Chapter {self.chapter_number}"
        return f"{self.novel.title} — {label}"

    def save(self, *args, **kwargs):
        text = (self.content or "").strip()
        self.word_count = len(text.split()) if text else 0
        super().save(*args, **kwargs)
        self.novel.refresh_chapter_count()


class EmbeddingChunk(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="embedding_chunks")
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    vector = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chapter__chapter_number", "chunk_index"]
        constraints = [
            models.UniqueConstraint(fields=["chapter", "chunk_index"], name="unique_embedding_chunk")
        ]
        indexes = [models.Index(fields=["chapter", "chunk_index"])]

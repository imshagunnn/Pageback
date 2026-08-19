"""Narrative memory extracted from chapters the reader has reached."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from novels.models import Chapter, Novel


class Importance(models.TextChoices):
    CRITICAL = "critical", "Critical"
    IMPORTANT = "important", "Important"
    MINOR = "minor", "Minor"


class EventType(models.TextChoices):
    MEETING = "meeting", "Meeting"
    CONVERSATION = "conversation", "Conversation"
    CONFLICT = "conflict", "Conflict"
    REVELATION = "revelation", "Revelation"
    DECISION = "decision", "Decision"
    RELATIONSHIP_CHANGE = "relationship_change", "Relationship change"
    TRAVEL = "travel", "Travel"
    DEATH = "death", "Death"
    DISCOVERY = "discovery", "Discovery"
    EMOTIONAL_CHANGE = "emotional_change", "Emotional change"
    INTRODUCTION = "introduction", "Introduction"
    OTHER = "other", "Other"


class DetailCategory(models.TextChoices):
    OBJECT = "object", "Object"
    SETTING_DETAIL = "setting_detail", "Setting"
    CHARACTER_DETAIL = "character_detail", "Character"
    HISTORICAL_CONTEXT = "historical_context", "Historical context"
    CONVERSATION_DETAIL = "conversation_detail", "Conversation"
    SYMBOL = "symbol", "Symbol"
    MOTIF = "motif", "Motif"
    FORESHADOWING = "foreshadowing", "Foreshadowing"
    PLOT = "plot", "Plot"
    RELATIONSHIP = "relationship", "Relationship"
    EMOTIONAL = "emotional", "Emotional"
    OTHER = "other", "Other"


class Character(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="characters")
    name = models.CharField(max_length=200)
    aliases = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    role = models.CharField(max_length=120, blank=True)
    first_appearance = models.ForeignKey(
        Chapter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="introduced_characters",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["novel", "name"], name="unique_character_name_per_novel"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.novel.title})"


class Location(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    first_appearance = models.ForeignKey(
        Chapter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="introduced_locations",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["novel", "name"], name="unique_location_name_per_novel"),
        ]

    def __str__(self) -> str:
        return self.name


class CharacterRelationship(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="relationships")
    source_character = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
    )
    target_character = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
    )
    relationship_type = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    first_detected_chapter = models.ForeignKey(
        Chapter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="relationships_first_seen",
    )
    last_updated_chapter = models.ForeignKey(
        Chapter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="relationships_last_seen",
    )
    confidence = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["source_character__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["novel", "source_character", "target_character", "relationship_type"],
                name="unique_relationship_edge",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.source_character.name} → {self.relationship_type} → {self.target_character.name}"


class RelationshipState(models.Model):
    """How a relationship looked in a specific chapter (evolution, not a static label)."""

    relationship = models.ForeignKey(
        CharacterRelationship,
        on_delete=models.CASCADE,
        related_name="states",
    )
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="relationship_states")
    status_label = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    evidence_reference = models.TextField(blank=True)
    confidence = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chapter__chapter_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["relationship", "chapter"],
                name="unique_relationship_state_per_chapter",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.relationship} @ ch.{self.chapter.chapter_number}: {self.status_label}"


class Event(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="events")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=255)
    description = models.TextField()
    event_type = models.CharField(max_length=40, choices=EventType.choices, default=EventType.OTHER)
    importance = models.CharField(max_length=20, choices=Importance.choices, default=Importance.IMPORTANT)
    characters_involved = models.ManyToManyField(Character, blank=True, related_name="events")
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    sequence_order = models.PositiveIntegerField(default=0)
    evidence_reference = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chapter__chapter_number", "sequence_order", "id"]
        indexes = [
            models.Index(fields=["novel", "chapter"]),
            models.Index(fields=["event_type", "importance"]),
        ]

    def __str__(self) -> str:
        return self.title


class ImportantDetail(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="important_details")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="important_details")
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=40,
        choices=DetailCategory.choices,
        default=DetailCategory.OTHER,
    )
    importance = models.CharField(max_length=20, choices=Importance.choices, default=Importance.MINOR)
    evidence_reference = models.TextField(blank=True)
    confidence = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )

    class Meta:
        ordering = ["chapter__chapter_number", "id"]

    def __str__(self) -> str:
        return self.title


class ThemeMotif(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="themes")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="themes")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    evidence_reference = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class CharacterDevelopment(models.Model):
    novel = models.ForeignKey(Novel, on_delete=models.CASCADE, related_name="character_developments")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="character_developments")
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name="developments")
    description = models.TextField()
    evidence_reference = models.TextField(blank=True)

    class Meta:
        ordering = ["chapter__chapter_number", "id"]

    def __str__(self) -> str:
        return f"{self.character.name} @ ch.{self.chapter.chapter_number}"

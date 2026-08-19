from django.contrib import admin

from story.models import (
    Character,
    CharacterDevelopment,
    CharacterRelationship,
    Event,
    ImportantDetail,
    Location,
    RelationshipState,
    ThemeMotif,
)


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "novel", "role", "first_appearance")
    list_filter = ("novel",)
    search_fields = ("name", "description")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "novel", "first_appearance")
    search_fields = ("name",)


class RelationshipStateInline(admin.TabularInline):
    model = RelationshipState
    extra = 0


@admin.register(CharacterRelationship)
class CharacterRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "source_character",
        "relationship_type",
        "target_character",
        "novel",
        "confidence",
    )
    list_filter = ("novel", "relationship_type")
    inlines = [RelationshipStateInline]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "novel", "chapter", "event_type", "importance")
    list_filter = ("event_type", "importance", "novel")
    filter_horizontal = ("characters_involved",)


@admin.register(ImportantDetail)
class ImportantDetailAdmin(admin.ModelAdmin):
    list_display = ("title", "novel", "chapter", "category", "importance")
    list_filter = ("category", "importance")


@admin.register(ThemeMotif)
class ThemeMotifAdmin(admin.ModelAdmin):
    list_display = ("name", "novel", "chapter")


@admin.register(CharacterDevelopment)
class CharacterDevelopmentAdmin(admin.ModelAdmin):
    list_display = ("character", "chapter", "novel")

from django.contrib import admin

from reading.models import ReadingProgress, ReadingSession, Recap


@admin.register(ReadingProgress)
class ReadingProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "novel", "current_chapter", "reading_status", "last_read_at")
    list_filter = ("reading_status",)


@admin.register(ReadingSession)
class ReadingSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "novel", "chapter", "started_at", "ended_at")


@admin.register(Recap)
class RecapAdmin(admin.ModelAdmin):
    list_display = ("user", "novel", "recap_type", "from_chapter", "to_chapter", "created_at")
    list_filter = ("recap_type",)
    readonly_fields = ("content", "structured_data")

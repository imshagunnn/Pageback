from django.contrib import admin

from novels.models import Chapter, Novel


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ("chapter_number", "title", "word_count", "processing_status")
    readonly_fields = ("word_count",)


@admin.register(Novel)
class NovelAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "owner", "total_chapters", "updated_at")
    list_filter = ("genre",)
    search_fields = ("title", "author")
    inlines = [ChapterInline]


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("novel", "chapter_number", "title", "word_count", "processing_status")
    list_filter = ("processing_status", "novel")
    search_fields = ("title", "content")

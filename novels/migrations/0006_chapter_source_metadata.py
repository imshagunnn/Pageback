from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("novels", "0005_rename_novels_embed_chapter_idx_novels_embe_chapter_bc4f98_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="chapter",
            name="content_type",
            field=models.CharField(default="chapter", max_length=32),
        ),
        migrations.AddField(
            model_name="chapter",
            name="source_page_end",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="chapter",
            name="source_page_start",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
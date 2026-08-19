from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("novels", "0003_novel_analysis")]

    operations = [
        migrations.CreateModel(
            name="EmbeddingChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chunk_index", models.PositiveIntegerField()),
                ("text", models.TextField()),
                ("vector", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("chapter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="embedding_chunks", to="novels.chapter")),
            ],
            options={"ordering": ["chapter__chapter_number", "chunk_index"]},
        ),
        migrations.AddConstraint(
            model_name="embeddingchunk",
            constraint=models.UniqueConstraint(fields=("chapter", "chunk_index"), name="unique_embedding_chunk"),
        ),
        migrations.AddIndex(
            model_name="embeddingchunk",
            index=models.Index(fields=["chapter", "chunk_index"], name="novels_embed_chapter_idx"),
        ),
    ]
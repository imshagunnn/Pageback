from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("novels", "0004_embeddingchunk")]

    operations = [
        migrations.RenameIndex(
            model_name="embeddingchunk",
            new_name="novels_embe_chapter_bc4f98_idx",
            old_name="novels_embed_chapter_idx",
        ),
    ]

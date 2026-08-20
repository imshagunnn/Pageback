from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("novels", "0006_chapter_source_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="chapter",
            name="parent_title",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
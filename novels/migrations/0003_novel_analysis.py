from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("novels", "0002_chapter_analysis")]

    operations = [
        migrations.AddField(
            model_name="novel",
            name="analysis_boundary",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="novel",
            name="analysis",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
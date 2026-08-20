from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("novels", "0007_chapter_parent_title")]

    operations = [
        migrations.CreateModel(
            name="Collection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="book_collections", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddField(model_name="novel", name="completed_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="novel", name="deleted_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="novel", name="is_favorite", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="novel", name="last_opened_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="novel", name="source_fingerprint", field=models.CharField(blank=True, db_index=True, max_length=64)),
        migrations.AddField(model_name="novel", name="status", field=models.CharField(choices=[("active", "Active"), ("completed", "Completed"), ("archived", "Archived"), ("trashed", "Trash")], default="active", max_length=20)),
        migrations.AddField(model_name="novel", name="collections", field=models.ManyToManyField(blank=True, related_name="novels", to="novels.collection")),
        migrations.AddConstraint(model_name="collection", constraint=models.UniqueConstraint(fields=("owner", "name"), name="unique_collection_name_per_user")),
    ]
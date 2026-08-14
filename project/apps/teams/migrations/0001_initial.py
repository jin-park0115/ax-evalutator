import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("evaluations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Team",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                (
                    "round",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="evaluations.evaluationround"),
                ),
            ],
        ),
    ]


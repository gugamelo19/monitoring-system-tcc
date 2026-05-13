import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("anomalies", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrustedSource",
            fields=[
                ("id", models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False)),
                ("ip_address", models.GenericIPAddressField(unique=True)),
                ("description", models.CharField(
                    blank=True, default="", max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Trusted source",
                "verbose_name_plural": "Trusted sources",
                "ordering": ["ip_address"],
            },
        ),
        migrations.CreateModel(
            name="FalsePositiveFeedback",
            fields=[
                ("id", models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False)),
                ("source_ip", models.GenericIPAddressField()),
                ("anomaly_type", models.CharField(max_length=100)),
                ("suppress_until", models.DateTimeField()),
                ("note", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "False positive feedback",
                "verbose_name_plural": "False positive feedbacks",
                "ordering": ["-suppress_until"],
                "unique_together": {("source_ip", "anomaly_type")},
            },
        ),
    ]

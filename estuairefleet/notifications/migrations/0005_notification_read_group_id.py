from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0004_notification_event_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="read_group_id",
            field=models.UUIDField(
                blank=True,
                db_index=True,
                editable=False,
                null=True,
                verbose_name="groupe de lecture partagé",
            ),
        ),
    ]

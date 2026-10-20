from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0003_notification_notificatio_recipie_da81fd_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="event_key",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=180,
                null=True,
                verbose_name="clé d'événement",
            ),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(
                condition=models.Q(("event_key__isnull", False)),
                fields=("recipient", "event_key"),
                name="unique_notification_event_per_recipient",
            ),
        ),
    ]

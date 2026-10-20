from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fleet", "0005_incident"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="trajet",
            index=models.Index(fields=["is_active", "direction"], name="fleet_trajet_active_direction_idx"),
        ),
        migrations.AddIndex(
            model_name="bus",
            index=models.Index(
                fields=["trajet", "status", "position_updated_at"], name="fleet_bus_map_position_idx"
            ),
        ),
    ]

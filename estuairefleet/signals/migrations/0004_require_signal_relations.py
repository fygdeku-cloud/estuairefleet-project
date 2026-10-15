from django.db import migrations, models


def remove_orphan_signals(apps, schema_editor):
    signal_model = apps.get_model("signals", "Signal")
    signal_model.objects.filter(student__isnull=True).delete()
    signal_model.objects.filter(trajet__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("signals", "0003_alter_signal_status")]

    operations = [
        migrations.RunPython(remove_orphan_signals, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="signal",
            name="student",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="signals",
                to="users.student",
                verbose_name="étudiant",
            ),
        ),
        migrations.AlterField(
            model_name="signal",
            name="trajet",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="signals",
                to="fleet.trajet",
                verbose_name="trajet",
            ),
        ),
    ]

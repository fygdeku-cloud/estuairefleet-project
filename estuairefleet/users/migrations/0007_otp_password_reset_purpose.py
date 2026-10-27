# Generated manually for the EstuaireFleet password reset OTP flow.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0006_rename_users_otpcha_email_8f2c2c_idx_users_otpch_email_52c9f8_idx")]

    operations = [
        migrations.AlterField(
            model_name="otpchallenge",
            name="purpose",
            field=models.CharField(
                choices=[
                    ("login", "Connexion"),
                    ("signup", "Inscription"),
                    ("password_reset", "Réinitialisation du mot de passe"),
                ],
                max_length=20,
                verbose_name="usage",
            ),
        ),
    ]

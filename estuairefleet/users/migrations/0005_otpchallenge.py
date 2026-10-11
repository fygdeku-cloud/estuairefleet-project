# Generated manually for the EstuaireFleet email OTP flow.
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0004_remove_driver_user_remove_staffprofile_user_and_more")]

    operations = [
        migrations.CreateModel(
            name="OTPChallenge",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="créé le")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="modifié le")),
                ("email", models.EmailField(db_index=True, max_length=254, verbose_name="adresse e-mail")),
                ("purpose", models.CharField(choices=[("login", "Connexion"), ("signup", "Inscription")], max_length=20, verbose_name="usage")),
                ("code_hash", models.CharField(max_length=128, verbose_name="code")),
                ("expires_at", models.DateTimeField(verbose_name="expire le")),
                ("attempts", models.PositiveSmallIntegerField(default=0, verbose_name="tentatives")),
                ("consumed_at", models.DateTimeField(blank=True, null=True, verbose_name="utilisé le")),
            ],
            options={"verbose_name": "code OTP", "verbose_name_plural": "codes OTP"},
        ),
        migrations.AddIndex(
            model_name="otpchallenge",
            index=models.Index(fields=["email", "purpose", "created_at"], name="users_otpcha_email_8f2c2c_idx"),
        ),
    ]

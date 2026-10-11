from django.contrib import admin
from django.contrib.auth import admin as auth_admin

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import AdministratorProfile, Driver, OTPChallenge, StaffProfile, Student, User


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("email", "matricule", "password")}),
        ("Identité", {"fields": ("first_name", "last_name", "phone_number", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")
    list_display = ("email", "matricule", "first_name", "last_name", "role", "is_active")
    search_fields = ("email", "matricule", "first_name", "last_name")
    ordering = ("email",)
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "matricule", "password1", "password2", "role")}),
    )


admin.site.register(Student)
admin.site.register(Driver)
admin.site.register(AdministratorProfile)
admin.site.register(StaffProfile)

admin.site.register(OTPChallenge)

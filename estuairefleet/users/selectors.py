from django.db.models import Count, Q

from .models import Chauffeur, User, UserRole


def get_user_by_identifier(identifier):
    return User.objects.filter(Q(email__iexact=identifier) | Q(matricule__iexact=identifier)).first()


def get_users_for_admin(*, search="", role=None, active=None, ordering="-created_at"):
    queryset = User.objects.all().order_by(ordering)
    if search:
        queryset = queryset.filter(
            Q(email__icontains=search)
            | Q(matricule__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
        )
    if role:
        queryset = queryset.filter(role=role)
    if active in {True, False}:
        queryset = queryset.filter(is_active=active)
    return queryset


def get_user_detail(user_id):
    return User.objects.select_related("student", "chauffeur", "administrateur", "personnel").get(pk=user_id)


def get_driver_candidates():
    return (
        Chauffeur.objects.select_related("user")
        .filter(user__is_active=True, user__role=UserRole.DRIVER)
        .filter(bus__isnull=True)
    )


def count_users_by_role():
    return {row["role"]: row["count"] for row in User.objects.values("role").annotate(count=Count("id"))}

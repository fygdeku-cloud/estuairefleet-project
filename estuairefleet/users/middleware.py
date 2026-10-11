from django.shortcuts import redirect


class ForcePasswordChangeMiddleware:
    """Empêche l'accès à l'application tant que le mot de passe temporaire reste actif."""

    allowed_names = {"users:password_change", "users:logout", "users:login", "users:otp_verify"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and request.user.must_change_password
            and request.resolver_match
            and request.resolver_match.view_name not in self.allowed_names
        ):
            return redirect("users:password_change")
        return self.get_response(request)

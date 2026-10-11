class BusinessRuleError(Exception):
    """Erreur métier traduisible par une vue HTML ou une API."""

    code = "business_rule"

    def __init__(self, detail: str, *, code: str | None = None):
        super().__init__(detail)
        self.detail = detail
        if code:
            self.code = code


class ConsentRequired(BusinessRuleError):
    code = "consent_required"


class OutOfZone(BusinessRuleError):
    code = "out_of_zone"


class ActiveSignalExists(BusinessRuleError):
    code = "active_signal_exists"


class RenewalLimitReached(BusinessRuleError):
    code = "renewal_limit_reached"


class InvalidBusTransition(BusinessRuleError):
    code = "invalid_bus_transition"


class RateLimitExceeded(BusinessRuleError):
    code = "rate_limit_exceeded"

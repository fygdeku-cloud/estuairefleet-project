from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from estuairefleet.core.exceptions import BusinessRuleError
from estuairefleet.fleet.models import Trajet
from estuairefleet.users.permissions import IsDriver, IsNotStudent, IsStudent

from ..models import Signal
from ..selectors import get_active_signal_for_student, get_student_signal_history, get_visible_signals_for
from ..services import cancel_signal, close_signal, emit_signal, flag_false_signal, renew_signal
from .serializers import SignalSerializer


def _error(exc):
    return Response(
        {"code": getattr(exc, "code", "business_rule"), "detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
    )


def _payload(item):
    return {key: str(value) if key == "id" and value else value for key, value in item.items() if key != "signal"}


class SignalCollectionView(APIView):
    serializer_class = SignalSerializer
    permission_classes = [IsStudent]

    def post(self, request):
        try:
            trajet = Trajet.objects.get(pk=request.data["trajet"]) if request.data.get("trajet") else None
            signal = emit_signal(
                student=request.user,
                lat=request.data["lat"],
                lng=request.data["lng"],
                accuracy=request.data.get("accuracy"),
                trajet=trajet,
            )
        except (BusinessRuleError, KeyError, ValueError, Trajet.DoesNotExist) as exc:
            return _error(exc)
        return Response(
            {"id": signal.id, "status": signal.status, "expires_in_seconds": signal.seconds_left}, status=201
        )


class MineSignalsView(APIView):
    serializer_class = SignalSerializer
    permission_classes = [IsStudent]

    def get(self, request):
        active = get_active_signal_for_student(request.user)
        return Response(
            {
                "active": {"id": active.id, "status": active.status, "expires_in_seconds": active.seconds_left}
                if active
                else None,
                "history": [
                    {"id": item.id, "status": item.status, "created_at": item.created_at}
                    for item in get_student_signal_history(request.user, 10)
                ],
            }
        )


class VisibleSignalsView(APIView):
    serializer_class = SignalSerializer
    permission_classes = [IsNotStudent]

    def get(self, request):
        return Response(
            {
                "server_time": __import__("django.utils.timezone", fromlist=["now"]).now(),
                "signals": [_payload(item) for item in get_visible_signals_for(request.user)],
            }
        )


class SignalActionView(APIView):
    serializer_class = SignalSerializer
    action = None

    def post(self, request, pk):
        try:
            signal = Signal.objects.select_related("student__user", "trajet").get(pk=pk)
            if self.action == "cancel":
                result = cancel_signal(signal=signal, by=request.user)
            elif self.action == "renew":
                result = renew_signal(signal=signal, by=request.user)
            elif self.action == "close":
                result = close_signal(signal=signal, by=request.user)
            else:
                result = flag_false_signal(signal=signal, by=request.user)
        except (BusinessRuleError, PermissionError, Signal.DoesNotExist) as exc:
            return _error(exc)
        return Response({"id": result.id, "status": result.status, "expires_in_seconds": result.seconds_left})


class CancelSignalView(SignalActionView):
    permission_classes = [IsStudent]
    action = "cancel"


class RenewSignalView(SignalActionView):
    permission_classes = [IsStudent]
    action = "renew"


class CloseSignalView(SignalActionView):
    permission_classes = [IsNotStudent]
    action = "close"


class FlagFalseSignalView(SignalActionView):
    permission_classes = [IsDriver]
    action = "flag"

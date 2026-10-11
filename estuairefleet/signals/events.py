from django.dispatch import Signal as DjangoSignal

signal_emitted = DjangoSignal()
signal_state_changed = DjangoSignal()

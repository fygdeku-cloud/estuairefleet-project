# Architecture

L’application est server-rendered avec Django templates, CSS local et JavaScript vanille. PostgreSQL est la cible de production, SQLite reste utile pour les contrôles isolés. Redis et Celery sont configurés pour les tâches d’expiration et de purge.

Le navigateur interroge les endpoints légers toutes les cinq secondes lorsque l’onglet est visible. Le selector `signals.get_visible_signals_for` applique le rôle avant la sérialisation : un étudiant ne reçoit que son signal, le personnel reçoit un libellé anonyme, et les positions expirées sont exclues.

Les écritures métier sont regroupées dans `services.py`, verrouillent les objets sensibles et émettent les événements internes `signal_emitted` et `signal_state_changed` après validation.

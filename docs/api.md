# API

L’API utilise la session Django et expose une structure d’erreur `{code, detail}` pour les règles métier.

- `/api/users/` : profil courant.
- `/api/campuses/`, `/api/trajets/`, `/api/buses/` : lectures Fleet.
- `/api/buses/positions/` et les actions `my-bus` : position, statut et occupation chauffeur.
- `/api/signals/` : émission étudiante.
- `/api/signals/mine/`, `/api/signals/{id}/cancel/`, `/renew/` : espace étudiant.
- `/api/signals/visible/`, `/close/`, `/flag-false/` : acteurs autorisés uniquement.

La documentation OpenAPI est disponible sur `/api/schema/` et `/api/docs/`.

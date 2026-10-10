# EstuaireFleet

EstuaireFleet est le MVP INSAM de gestion du transport étudiant. Le projet fournit un socle Django server-rendered pour les étudiants, chauffeurs et responsables transport : trajets, flotte, signaux de localisation, alertes prioritaires, inter-campus et notifications.

## Démarrage local

Pré-requis : Docker Compose et [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

Pour lancer l’environnement complet avec PostgreSQL, Redis, Celery et Mailpit :

```bash
docker compose -f docker-compose.local.yml up --build
```

L’application est disponible sur `http://localhost:8000`, la boîte de développement sur `http://localhost:8025`, et la documentation API sur `/api/docs/`.

## Commandes utiles

```bash
uv run python manage.py check
uv run pytest
uv run ruff check .
uv run ruff format .
uv run python manage.py makemigrations
uv run python manage.py migrate
```

## Architecture

Les apps Django sont regroupées sous `estuairefleet/` :

- `users` : utilisateur custom, matricule/e-mail et rôles ;
- `fleet` : campus, trajets, bus et positions des bus ;
- `signals` : émission, consentement, géorepérage et expiration ;
- `alerts` : seuil prioritaire, réponse chauffeur et escalade ;
- `intercampus` : cours et affectations de bus ;
- `notifications` : notifications in-app et canaux préparés.

Chaque domaine sépare `models.py`, `forms.py`, `views/`, `services.py`, `selectors.py`, `validators.py`, `permissions.py` et `tests/`. Les services réalisent les écritures dans des transactions atomiques ; les selectors portent les lectures.

La configuration est séparée dans `config/settings/base.py`, `local.py`, `test.py` et `production.py`. PostgreSQL est utilisé par les environnements applicatifs ; SQLite est réservé aux tests locaux isolés. Redis et Celery sont prêts pour l’expiration des signaux, les alertes et les notifications asynchrones.

## Sécurité et confidentialité

Les coordonnées des étudiants ne sont jamais exposées dans les lectures étudiantes. La carte des signaux est réservée aux acteurs transport autorisés. Le consentement de localisation est vérifié avant émission, les signaux expirent automatiquement et l’authentification utilise Argon2 en priorité.

## Interface

Le design system INSAM est dans `estuairefleet/static/css/design-system.css`. Il utilise la palette rouge/blanc/noir, Bootstrap 5 et Leaflet/OpenStreetMap. Le bouton de signal est conçu pour une interaction mobile en un geste.

## Déploiement

Le fichier `docker-compose.production.yml` orchestre Django/Gunicorn, Celery, PostgreSQL et Redis. Les secrets et paramètres d’hôte doivent être fournis par l’environnement de déploiement ; ne pas versionner `.env`.

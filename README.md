# EstuaireFleet

EstuaireFleet est l’application web responsive de transport étudiant d’INSAM. Elle permet aux étudiants de signaler leur présence, aux chauffeurs de suivre les demandes utiles à leur trajet et aux responsables de superviser la flotte.

## Démarrage local

Pré-requis : Docker Compose et [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver
```

Ou avec l’environnement complet : `just up`. Les coordonnées du seeder sont des placeholders autour de Yaoundé.

En local, les e-mails OTP sont capturés par Mailpit. Consultez-les sur http://localhost:8025 ; le serveur SMTP utilisé par Django est `mailpit:1025`.

Comptes de démonstration : `admin@insam.local`, `scolarite@insam.local`, `chauffeur1@insam.local` et `INS-2026-001` avec le mot de passe `EstuaireDemo2026!` en mode DEBUG uniquement.

## Commandes

`just test`, `just lint`, `just fmt`, `just css`, `just verify`, `just migrate`, `just makemigrations`, `just seed`, `just shell`, `just logs`, `just screenshots`.

Les simulations sont `python manage.py simulate_signals --trajet R1-AL --count 5` et `python manage.py simulate_bus_movement --bus CE-2026-EF`.

## Architecture

Les domaines `users`, `fleet`, `signals`, `alerts`, `intercampus` et `notifications` séparent modèles, validateurs, services d’écriture et selectors de lecture. Les profils de rôle sont composés par OneToOne. Les positions étudiant sont filtrées au selector central de Signals avant tout rendu ou payload JSON.

Les alertes, cours inter-campus et notifications disposent de parcours HTML, de tâches Celery et d’endpoints REST. La position des bus est rafraîchie par polling JSON et les points de signal sont visibles uniquement aux rôles autorisés.

## Qualité et déploiement

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
DJANGO_SECRET_KEY='clé-de-contrôle-longue' DJANGO_ALLOWED_HOSTS='localhost' DJANGO_SETTINGS_MODULE=config.settings.production uv run python manage.py check --deploy
```

Les secrets, l’URL PostgreSQL, Redis, l’e-mail et les paramètres métier sont fournis par variables d’environnement. En production, activer HTTPS, HSTS, les cookies sécurisés et les volumes persistants PostgreSQL/Redis.

# Rapport de finalisation du MVP — EstuaireFleet

Date : 19 octobre 2026

## A. État du projet avant l'intervention

Le dépôt était un MVP Django déjà avancé. Les domaines Core & Users, Fleet, Signals, Alerts, Intercampus et Notifications existaient avec leurs modèles, migrations, services, selectors, permissions, vues, templates et endpoints REST secondaires. Le cœur Signal → Alerte → réponse chauffeur → escalade était déjà présent et couvert par des tests.

Les écarts principaux étaient l'absence de vraie fondation PWA, un contrôle OpenAPI qui échouait avec un utilisateur anonyme, une classe Tailwind non générée dans le template de base et l'impossibilité d'exécuter les contrôles via le `.venv` local illisible de cet environnement.

## B. Bugs corrigés

- Ajout d'une route racine `/sw.js` servie avec le bon type MIME et des en-têtes de non-cache.
- Correction de `UserViewSet` afin que la génération du schéma fonctionne aussi avec `AnonymousUser`.
- Correction de la classe `text-insam-950`, absente de la palette Tailwind, puis recompilation du bundle CSS.
- Ajout d'un repli JavaScript local pour le menu mobile et la fermeture des alertes quand Flowbite n'est pas disponible hors connexion.
- Vérification des migrations, du système Django, du contrôle de déploiement et de la collecte des fichiers statiques.

## C. Modules finalisés

- **Core & Users** : modèle utilisateur UUID, rôles étudiant/chauffeur/administrateur/personnel, authentification par matricule ou e-mail, mot de passe, OTP par e-mail, profils, permissions et API de profil.
- **Fleet** : campus, trajets, arrêts, bus, affectations, états métier, position du bus, occupation, incidents, ETA et écrans de supervision.
- **Signals** : un signal actif par étudiant, consentement, géorepérage, TTL, renouvellement limité, annulation, clôture, expiration, anti-abus et purge différée des coordonnées.
- **Alerts** : seuil configurable par trajet avec valeur par défaut de cinq, notification des chauffeurs, réponse « J'arrive » ou « Indisponible », relais séquentiels, escalade Celery et résolution administrateur.
- **Intercampus** : cours, campus distincts, horaires valides, affectation de bus sans chevauchement, transitions et rappels.
- **Notifications** : notifications in-app, e-mail via fournisseur SMTP configuré, canal SMS préparé avec fallback journalisé, lecture limitée au destinataire et tâches Celery.
- **Frontend** : templates Django server-side, Tailwind CSS, plugin Flowbite, design system rouge INSAM `#C8102E`, Leaflet local et tuiles OpenStreetMap.
- **API REST** : endpoints secondaires pour les utilisateurs, flotte, signaux, alertes, inter-campus et notifications, avec permissions par rôle.

## D. Mise en place et finalisation de la PWA

- Manifest avec nom, nom court, description, langue, portée `/`, affichage `standalone`, orientation mobile, couleurs INSAM et icônes 192/512.
- Icônes SVG carrées adaptées à l'installation et au masque des lanceurs.
- Service worker enregistré depuis le template de base et servi à la racine pour couvrir toute l'application.
- Cache de l'app shell : accueil, CSS, JavaScript local, Leaflet, manifest, icônes et page de repli.
- Stratégie réseau : navigation en priorité réseau, page hors connexion de secours et cache-first pour les assets locaux ; les mutations API restent toujours réseau afin de ne pas rejouer une action métier par erreur.
- Métadonnées d'installation Android/iOS, bandeau d'installation déclenché par le navigateur, état hors connexion et repli du menu mobile.
- Le mode hors connexion est volontairement basique : les écrans shell restent accessibles, mais l'émission d'un signal nécessite une reconnexion et les tuiles OpenStreetMap ne sont pas mises en cache.

## E. Inventaire complet actuel du projet

```text
config/                         settings, URLs, ASGI/WSGI, Celery, routeur API
compose/                        Dockerfiles local et production
estuairefleet/core/             socle UUID, géométrie, dashboard, commandes, PWA
estuairefleet/users/            identité, profils, OTP, permissions, API
estuairefleet/fleet/            campus, trajets, arrêts, bus, incidents, API
estuairefleet/signals/          signaux, confidentialité, géorepérage, API, tâches
estuairefleet/alerts/           seuils, réponses, relais, escalade, API, tâches
estuairefleet/intercampus/      cours, affectations, rappels, API
estuairefleet/notifications/   in-app, e-mail/SMS préparés, API, tâches
estuairefleet/templates/        templates Django et composants communs
estuairefleet/static/           Tailwind, Flowbite, Leaflet, JavaScript, PWA
estuairefleet/*/tests/          tests métier, API, confidentialité et PWA
tests/                          tests d'infrastructure et scripts visuels
docs/                           architecture, décisions, audit et rapports
```

Le contrôle d'exclusion métier confirme qu'aucun modèle, champ, endpoint, template ou test ne porte de fonctionnalité financière. Les occurrences de `transaction` conservées sont exclusivement celles de `django.db.transaction.atomic`, utilisées pour garantir l'atomicité des écritures.

## F. Liste des commits effectués

Commits de cette finalisation :

- `e237370 chore: analyse de l’état actuel du projet avant finalisation`
- `05b9da2 feat(pwa): ajouter manifest service worker et mode hors connexion`
- `ad60d3c fix: corriger la robustesse API et finaliser le shell PWA`
- Commit final de livraison : `docs: rapport de finalisation complète du MVP EstuaireFleet`.

Principaux commits fonctionnels déjà présents dans l'historique : finalisation Users, Fleet, Signals, Alerts, Intercampus/Notifications, Core/API et suivi temps réel des bus.

## G. Démarrer le projet en local

### Avec uv

```bash
cp .env.example .env
uv sync --dev
npm ci
npm run build:css
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver
```

L'application est disponible sur `http://localhost:8000`. Le jeu de démonstration est réservé au mode DEBUG. Les comptes et le mot de passe sont indiqués par la commande `seed_demo`.

### Avec Docker Compose

```bash
cp .env.example .env
docker compose --env-file .env -f docker-compose.local.yml up --build
```

Dans un autre terminal :

```bash
docker compose --env-file .env -f docker-compose.local.yml exec django python manage.py migrate
docker compose --env-file .env -f docker-compose.local.yml exec django python manage.py seed_demo
```

L'application est alors disponible sur `http://localhost:8001` et la boîte de développement sur `http://localhost:8025`.

### Contrôles qualité

```bash
UV_PROJECT_ENVIRONMENT=/tmp/estuairefleet-venv uv run pytest -q
UV_PROJECT_ENVIRONMENT=/tmp/estuairefleet-venv uv run ruff check .
UV_PROJECT_ENVIRONMENT=/tmp/estuairefleet-venv uv run python manage.py check
```

Résultat final : **28 tests passants**, Ruff propre, migrations cohérentes, `check --deploy` propre et `collectstatic` réussi.

## H. Ce qui reste éventuel et points d'attention

- Brancher un véritable fournisseur SMS si ce canal devient nécessaire en production ; le provider actuel journalise le fallback.
- Prévoir les secrets, certificats, sauvegardes PostgreSQL, supervision et reverse proxy de production.
- Effectuer une recette navigateur sur Android/iOS pour confirmer l'installation PWA selon les versions ciblées.
- Les cartes nécessitent une connexion pour les tuiles OpenStreetMap ; les données métier restent protégées par les permissions et le polling.
- L'émission d'un signal n'est pas mise en file hors connexion afin d'éviter de créer un signal avec une position devenue obsolète.

Aucune application mobile native n'est prévue : l'expérience mobile est portée par la PWA installable.

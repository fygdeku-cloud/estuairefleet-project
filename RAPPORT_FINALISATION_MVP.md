# Rapport de finalisation complète du MVP — EstuaireFleet

Date : 20 octobre 2026

## A. État du projet avant cette intervention

Le projet était un MVP Django structuré par domaines, avec les domaines Core, Users, Fleet, Signals, Alerts, Intercampus et Notifications déjà présents. Les modèles, migrations, services, selectors, permissions, vues, API REST, templates Tailwind et premières briques PWA existaient.

L’audit initial a relevé plusieurs écarts : parcours staff Intercampus incomplet, rappel chauffeur calculé sur la fin du cours, absence de badge global de notifications, événements métier non idempotents, supervision sans snapshot unifié, icônes PWA uniquement vectorielles, vues historiques hétérogènes et fermeture incomplète des signaux après réponse chauffeur.

## B. Modules finalisés

### Intercampus

- édition sécurisée des cours et contrôle des transitions métier ;
- affectation manuelle ou automatique d’un bus sans chevauchement ;
- actions staff de confirmation, annulation et notification chauffeur ;
- rappel Celery basé sur `start_at` et non sur la fin du cours ;
- notifications typées `intercampus` ;
- selectors enrichis avec les campus, le bus et le chauffeur ;
- interface de gestion responsive et exploitable sur mobile.

### Notifications

- notifications in-app limitées au destinataire ;
- badge non lu dans la navigation et compteur caché court ;
- clé d’événement unique par destinataire pour éviter les doublons ;
- branchement sur émission/expiration de signal, alerte, réponse chauffeur, relais, escalade et Intercampus ;
- dispatch e-mail différé et provider SMS de repli conservés ;
- verrouillage d’une notification avant envoi et marquage lu atomique ;
- endpoint API `unread_count` conservé.

### Supervision Admin

- endpoint de snapshot protégé pour les données opérationnelles ;
- rafraîchissement périodique des statistiques, bus, trajets, alertes et incidents ;
- carte Leaflet des bus géolocalisés ;
- indicateur de fraîcheur, message de dégradation et arrêt du polling lorsque l’onglet est masqué ;
- tableau de bord responsive avec liens vers les listes détaillées.

## C. Mise en place et finalisation de la PWA

- manifest complet : nom, description, portée, affichage standalone, orientation, couleurs, catégories et démarrage ;
- icônes PNG réelles `192x192` et `512x512`, avec variantes SVG conservées ;
- meta tags mobile, thème rouge et icône Apple ;
- service worker exposé à `/sw.js` avec MIME JavaScript et en-têtes de non-cache ;
- cache shell versionné `v3`, récupération tolérante des assets et page offline ;
- navigation en priorité réseau avec repli vers `/about/` puis l’écran hors connexion ;
- cache-first des ressources statiques et mise en cache dynamique des assets récupérés ;
- les mutations métier restent réseau afin d’éviter les actions rejouées hors connexion.

## D. Améliorations visuelles et responsivité

- uniformisation des surfaces, titres, boutons principaux/secondaires, badges et états vides ;
- refonte de la supervision flotte avec carte et liste de bus ;
- historique Signal et formulaire de réponse Alerte alignés sur le design system ;
- tableaux et planning Intercampus placés dans des conteneurs scrollables ;
- actions tactiles, espacements mobiles, barre de navigation basse et zones sûres conservés ;
- responsive mobile-first avec Tailwind CSS et Flowbite uniquement ;
- identité rouge/blanc/noir conservée autour de `#C8102E` et `#9B0C24`.

## E. Corrections du parcours critique Signal → Alerte

- consentement, position GPS, géorepérage, anti-abus et limite d’un signal actif conservés ;
- évaluation du seuil et création d’alerte protégées par transaction et verrou de trajet ;
- réponse « J’arrive » validée avec ETA ;
- réponse « Indisponible » validée avec motif et bus relais ;
- relais séquentiels protégés par tentatives uniques et délai de réponse ;
- timeout Celery et escalade finale idempotente ;
- prise en charge chauffeur ou relais ferme atomiquement les signaux actifs concernés ;
- clôture administrateur ferme également les signaux ;
- les réponses concurrentes d’un autre chauffeur ne remplacent plus la réponse déjà enregistrée ;
- notifications de prise en charge et d’escalade alignées avec l’état réel des signaux.

## F. Optimisations de performance backend

- indexes ajoutés sur l’activité des trajets et les positions opérationnelles des bus ;
- agrégation SQL du nombre de signaux par trajet ;
- suppression d’un N+1 lors de la résolution d’un trajet habituel ;
- `select_related` et `prefetch_related` maintenus sur les écrans et services sensibles ;
- cache court Redis-compatible pour statistiques, seuils, compteurs et positions de supervision ;
- itération Celery bornée et ordonnée pour alertes, cours et notifications ;
- tâches d’expiration, d’escalade et de rappel conservées dans le beat Celery ;
- caches courts adaptés au polling sans masquer durablement les changements métier.

## G. Liste complète des commits effectués

1. `818ca41 chore: analyse complète de l’existant avant finalisation MVP`
2. `e6161e1 feat(intercampus): finalisation complète du module Cours inter-campus`
3. `e3830cb feat(notifications): finalisation du système de notifications in-app et email`
4. `1a29862 feat(admin): finalisation du module de supervision et tableau de bord admin`
5. `829034d feat(pwa): PWA réellement installable avec service worker et manifest complets`
6. `5a10d9b feat(ui): amélioration visuelle majeure et responsivité totale mobile-first`
7. `c82f663 fix: renforcement et correction du parcours critique Signal → Alerte → Escalade`
8. `c36ddcc perf(backend): optimisation des requêtes, indexes et mise en cache Redis`
9. `149091c chore: nettoyage final du projet avant livraison MVP`
10. `docs: rapport de finalisation complète du MVP EstuaireFleet` — présent commit documentaire.

## H. Comment démarrer le projet en local

### Avec uv et npm

```bash
cp .env.example .env
uv sync --dev
npm ci
npm run build:css
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver
```

L’application est disponible sur `http://localhost:8000`. PostgreSQL et Redis doivent être accessibles selon le contenu du fichier `.env`.

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

### Contrôles qualité

```bash
UV_PROJECT_ENVIRONMENT=/tmp/estuairefleet-venv uv run pytest -q
UV_PROJECT_ENVIRONMENT=/tmp/estuairefleet-venv uv run ruff check .
UV_PROJECT_ENVIRONMENT=/tmp/estuairefleet-venv uv run ruff format --check .
UV_PROJECT_ENVIRONMENT=/tmp/estuairefleet-venv uv run python manage.py check
npm run build:css
```

État vérifié lors de la livraison : **29 tests passants**, Ruff check et formatage propres, `manage.py check` propre, migrations cohérentes et scripts JavaScript valides.

## I. Points d’attention restants

- PostgreSQL et Redis doivent être configurés avec des identifiants valides avant un déploiement réel ;
- les tâches Celery worker/beat doivent être lancées pour les expirations, rappels, dispatch et escalades ;
- les tuiles OpenStreetMap nécessitent une connexion réseau ;
- le mode offline reste limité au shell public et aux assets déjà disponibles ;
- le provider SMS actuel est une structure de repli journalisée et devra être remplacé par un fournisseur opérationnel si nécessaire ;
- une recette navigateur Android, iOS, tablette et desktop reste recommandée avant production ;
- la supervision temps réel repose sur un polling borné, adapté au MVP mais à surveiller avec la montée en charge.

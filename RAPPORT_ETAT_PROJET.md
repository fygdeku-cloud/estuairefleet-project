# Rapport d'état du projet — EstuaireFleet

## A. État avant l'intervention

Le dépôt était arrêté après les modules 1 à 3 : Core & Users, Fleet et Signals étaient présents et couverts par une base de tests. Les domaines Alerts, Intercampus et Notifications existaient sous forme de squelettes, sans parcours HTML complet ni raccordement global. L'API REST couvrait Users, Fleet et Signals, mais pas les trois domaines suivants.

Éléments déjà présents :

- `config/` avec settings local/test/production, URLs, routeur REST, ASGI, WSGI et Celery.
- `core` avec `BaseModel` UUID, géométrie, constantes, exceptions, permissions et commandes de démonstration.
- `users` avec `User`, profils `Student`, `Chauffeur`, `Administrateur`, `Personnel`, authentification par identifiant, OTP par e-mail, services, selectors, formulaires, middleware, API et migrations.
- `fleet` avec `Campus`, `Trajet`, `Stop`, `Bus`, services de statut/position/occupation, selectors, API et écrans de flotte.
- `signals` avec `Signal`, unicité conditionnelle du signal actif, géorepérage, expiration, renouvellement, annulation, clôture, anti-abus, purge des coordonnées, API et écrans de supervision.
- `alerts` avec les modèles `Alert` et `AlertResponse`, un service de seuil partiel et une tâche d'escalade partielle.
- `intercampus` avec `CoursInterCampus`, un formulaire minimal, deux services et un selector minimal.
- `notifications` avec `Notification`, un service de création dans l'application et un selector des éléments non lus.
- Leaflet local, CSS INSAM, Docker Compose et uv étaient déjà configurés.

Dysfonctionnements relevés :

- Dockerfile de production invalide à cause d'une déclaration `ENV` mal formée.
- `redirect` manquant dans les permissions Users.
- Migration manquante pour le renommage d'index OTP sous la version Django verrouillée.
- Validation du Bus exécutée après insertion et absence de validation GPS dans la mise à jour de position.
- Selector `get_nearest_available_bus` importé par Alerts mais inexistant.
- Références incohérentes entre `driver` et `chauffeur`, et entre les relations Fleet utilisées par Alerts.
- Validator de position Signals incorrect pour les campus et rayon très permissif, expiration obsolète pouvant bloquer l'émission suivante malgré l'unicité conditionnelle.
- Exceptions Django non prises en compte correctement par l'API Signals.
- Alerts sans URLs, vues, templates ni parcours de réponse complet.
- Intercampus et Notifications sans URLs, parcours HTML, tâches ou API complètes.
- Absence de templates communs et de styles organisés par domaine.
- Doublon mort `fleet/views.py` alors qu'un package `fleet/views/` existait déjà.
- Ruff signalait des imports, chaînes et formats non conformes.

## B. Corrections effectuées

- Correction du Dockerfile de production et validation des deux configurations Compose.
- Correction de l'import de redirection Users et reformatage des fichiers concernés.
- Ajout de la migration Users `0006` pour l'index OTP.
- Correction de la création de Bus afin de valider avant écriture.
- Validation systématique des coordonnées GPS de Bus.
- Ajout du selector de bus disponible le plus proche pour les relais.
- Correction des relations chauffeur dans selectors, services, permissions et API Alerts.
- Ajout du verrouillage de trajet lors de l'évaluation d'une alerte afin d'éviter les créations concurrentes incohérentes.
- Ajout de la contrainte de seuil positif des alertes et de la validation modèle correspondante.
- Correction de l'escalade des alertes arrivées à échéance.
- Nettoyage des signaux actifs expirés avant une nouvelle émission.
- Correction du validator de géorepérage et des erreurs d'autorisation de l'API Signals.
- Conservation de la compatibilité des anciennes relations Signals nullable, explicitement introduite par l'historique du projet, sans rattachement arbitraire de données.
- Retrait du doublon de vues Fleet.
- Retrait de l'extension d'authentification non utilisée et régénération de `uv.lock`.
- Correction des imports, du formatage et de la migration documentaire existante.

## C. Modules terminés

### Module 4 — Alerts

- Modèles `Alert` et `AlertResponse` avec `TextChoices`, timestamps UUID, seuil positif, unicité d'une alerte ouverte par trajet, priorité, délai de réponse et date d'escalade.
- Services atomiques : évaluation du seuil, réponse chauffeur, escalade et clôture administrateur.
- Selectors d'alertes ouvertes, alertes d'un chauffeur, comptage des signaux actifs et proposition de bus relais.
- Formulaire de réponse avec validation métier du type de réponse, de l'ETA, du motif et du bus relais.
- Permissions DRF et mixins HTML par rôle.
- Vues CBV, URLs namespacées, templates de liste, détail et réponse.
- Notification dans l'application envoyée aux chauffeurs affectés au trajet.
- Tâche Celery d'escalade automatique toutes les 60 secondes.
- Endpoints REST de lecture, réponse et clôture.
- Tests du seuil, de la priorité, de l'accès chauffeur, de la réponse et de l'escalade.

### Module 5 — Intercampus et Notifications

- `CoursInterCampus` complété par des contraintes SQL de campus distincts et de fin postérieure au début.
- Services de création, mise à jour, affectation avec détection de chevauchement, transition d'état, notification chauffeur et suppression.
- Validator des transitions `PLANNED`, `CONFIRMED`, `COMPLETED`, `CANCELLED`.
- Selectors de planning public et de gestion.
- Formulaire, vues CBV, URLs namespacées et templates de planning/gestion.
- Tâche Celery de notification préalable des cours affectés.
- `Notification` complété par selectors utilisateur, lecture sécurisée et service atomique de marquage comme lue.
- Vue CBV, URL et template de consultation des notifications.
- Endpoints REST pour le planning inter-campus et les notifications personnelles.
- Tests de conflit de bus, transitions, notification chauffeur et confidentialité du destinataire.

### Module 6 — API REST skeleton

- Routeur REST étendu à `alerts`, `intercampus` et `notifications`.
- Serializers en lecture contrôlée et permissions par rôle.
- Documentation OpenAPI générée et validée avec `drf-spectacular`.
- Les notifications ne sont lisibles que par leur destinataire.
- Les alertes chauffeur sont filtrées par bus et trajet.
- Les étudiants ne disposent toujours pas de l'endpoint de carte des signaux.

## D. Inventaire actuel

### Structure principale

- `config/` : settings multi-environnements, URLs, API, ASGI, WSGI et Celery.
- `estuairefleet/core/` : socle, géométrie, permissions, exceptions, commandes.
- `estuairefleet/users/` : identité, profils, authentification, OTP, API.
- `estuairefleet/fleet/` : campus, trajets, arrêts, bus, services, selectors, API et vues.
- `estuairefleet/signals/` : signaux, règles de localisation, anti-abus, API et tâches.
- `estuairefleet/alerts/` : alertes, réponses, services, selectors, vues, API et tâche d'escalade.
- `estuairefleet/intercampus/` : planning, transitions, services, vues, API et tâche de notification.
- `estuairefleet/notifications/` : notifications personnelles, lecture, services, vues et API.
- `estuairefleet/templates/` : base, `common/`, comptes, utilisateurs, flotte, signaux, alertes, inter-campus et notifications.
- `estuairefleet/static/` : design system Tailwind/Flowbite, CSS par domaine, Leaflet et JavaScript.
- `tests/` et `estuairefleet/*/tests/` : tests de parcours, métier, API et confidentialité.

### Modèles et statuts

- `User` : e-mail, matricule, identité, téléphone, rôle, état actif et changement de mot de passe requis. Rôles : étudiant, chauffeur, administrateur, personnel.
- `OTPChallenge` : e-mail, usage, hash, expiration, tentatives et consommation. Usages : connexion, inscription.
- `Student` : matricule, campus, trajets habituels, consentement de géolocalisation, avertissements et suspension.
- `Chauffeur` : utilisateur et numéro de licence.
- `Administrateur` : utilisateur et fonction.
- `Personnel` : utilisateur, service et campus.
- `Campus` : nom, code, adresse, coordonnées, rayon et activation.
- `Trajet` : nom, code, direction, campus, itinéraire, horaires, jours, seuil, durée de vie du signal, rayon et activation.
- `Stop` : trajet, nom, coordonnées et ordre unique par trajet.
- `Bus` : immatriculation, libellé, capacité, statut, chauffeur, trajet, position, ETA et occupation. Statuts : hors service, disponible, en route, plein, indisponible.
- `Signal` : étudiant, trajet, position, précision, expiration, renouvellements, prise en charge et indicateurs anti-abus. Statuts : inactif, actif, expiré, annulé, pris en charge.
- `Alert` : trajet, signaux, statut, seuil, compteur, priorité, délai, escalade et résolution. Statuts : en attente, déclenchée, en cours, résolue, escalade.
- `AlertResponse` : alerte, chauffeur, réponse, ETA, motif, bus relais et date de réponse. Réponses : j'arrive, indisponible.
- `CoursInterCampus` : groupe, campus départ/arrivée, début/fin, effectif, bus, délai de notification, statut et date de notification. Statuts : planifié, confirmé, terminé, annulé.
- `Notification` : destinataire, titre, message, canal, état, lecture, envoi, échec et métadonnées. Canaux préparés : application, e-mail, SMS. États : en attente, envoyée, échec.

### Design system et configuration

- Palette INSAM présente dans `design-system.css` : rouge principal `#C8102E`, rouge foncé `#9B0C24`, rouge de signal contrasté, noir `#1A1A1A`, fond `#F8F8F8` et bordure `#E5E5E5`.
- Composants réutilisables : boutons, cartes, badges, tableaux, formulaires, états vides, notifications, cartes et navigation responsive.
- CSS par domaine ajouté pour Alerts, Intercampus et Notifications.
- Django, DRF, PostgreSQL, Redis, Celery, Tailwind CSS, Flowbite, Leaflet, Gunicorn et WhiteNoise sont configurés.
- `uv.lock` est synchronisé après retrait des dépendances d'authentification non utilisées.
- Local et production disposent chacun d'un Dockerfile et d'un Compose avec PostgreSQL, Redis, Django, worker Celery et beat.

### Vérifications réalisées

- 20 tests passent.
- Ruff check passe.
- Ruff format check passe.
- `makemigrations --check --dry-run` passe.
- `manage.py check` passe.
- `manage.py check --deploy` passe avec des secrets et hôtes de validation.
- `collectstatic --noinput --clear` passe.
- Configuration Compose locale et production valide.
- Schéma OpenAPI généré et validé.

Prêt : Core, Users, Fleet, Signals, Alerts, Intercampus, Notifications et API REST préparée.

À faire ensuite : finaliser le parcours cartographique Leaflet avec tuiles OpenStreetMap, polling de carte, émission GPS réelle côté chauffeur, éditeur avancé d'itinéraire, contrôles visuels automatisés et branchements de diffusion externes des canaux de notification préparés.

## E. Démarrage local

### Avec uv

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Comptes de démonstration après `seed_demo` : `admin@insam.local`, `scolarite@insam.local`, `chauffeur1@insam.local` et `INS-2026-001`, avec le mot de passe `EstuaireDemo2026!` en mode DEBUG.

### Avec Docker Compose

```bash
cp .env.example .env
docker compose --env-file .env -f docker-compose.local.yml up --build
```

Dans un autre terminal :

```bash
docker compose --env-file .env -f docker-compose.local.yml exec django python manage.py migrate
docker compose --env-file .env -f docker-compose.local.yml exec django python manage.py seed_demo
docker compose --env-file .env -f docker-compose.local.yml exec django python manage.py createsuperuser
```

URLs locales : application sur `http://localhost:8001`, boîte e-mail de développement sur `http://localhost:8025`, API sur `/api/` et documentation sur `/api/docs/`.

### Commandes qualité

```bash
just test
just lint
just migrate
just seed
```

## F. Points d'attention et risques restants

- L'environnement `.venv` présent dans cet espace était un artefact root inaccessible et pointait vers un interpréteur absent. Les contrôles ont été exécutés dans un environnement uv isolé ; sur une machine normale, `uv sync` recrée l'environnement local.
- PostgreSQL et Redis doivent être disponibles pour le fonctionnement local complet avec Docker ou pour la production.
- Le rafraîchissement temps réel actuel reste à finaliser côté interface cartographique ; les tâches Celery sont prêtes mais ne remplacent pas encore une carte interactive complète.
- Les anciennes lignes Signals avec relations nullable sont conservées pour compatibilité historique. Les nouveaux parcours passent exclusivement par les services qui exigent un profil étudiant et un trajet valides.
- Le calcul géographique est local et adapté au géorepérage urbain ; une vérification cartographique plus précise sera utile pour les trajets complexes.
- Les canaux e-mail et SMS de Notification sont modélisés mais leur fournisseur opérationnel n'est pas branché dans ce MVP.
- Une supervision de production complète devra ajouter reverse proxy, certificats, sauvegardes PostgreSQL, rotation des secrets et observabilité.

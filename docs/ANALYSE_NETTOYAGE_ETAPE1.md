# Analyse complète du projet — étape 1

Date de l’audit : 24 octobre 2026  
Référence Git : `126bbf6` (`main`, arbre propre au démarrage)

## A. Périmètre analysé

L’audit a couvert :

- les sept domaines Django (`core`, `users`, `fleet`, `signals`, `alerts`, `intercampus`, `notifications`) ;
- les modèles, migrations, managers, services, selectors, formulaires, permissions, vues HTML et API, tâches Celery et commandes de management ;
- la configuration Django locale, test et production, les URLs, le routeur API et les fichiers Docker/Compose ;
- `pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json`, Tailwind et Flowbite ;
- tous les templates, partials, CSS, JavaScript, Leaflet, manifest et service worker PWA ;
- les tests, fixtures pytest et scripts auxiliaires ;
- les commits récents et les rapports existants afin de ne pas confondre un reliquat historique avec une fonctionnalité active.

## B. Architecture effectivement utilisée

Le projet est une application Django avec UUID via `core.models.BaseModel`, `TextChoices` pour les états métier et séparation par domaine :

| Domaine | Modèles principaux | Entrées actives |
| --- | --- | --- |
| Users | `User`, `Student`, `Chauffeur`, profils admin/personnel, OTP | HTML, allauth account, API Users, admin |
| Fleet | `Campus`, `Trajet`, `Stop`, `Bus`, `Incident` | HTML, API Fleet, admin, services métier |
| Signals | `Signal` et statuts | HTML, API, tâches d’expiration |
| Alerts | alertes, réponses et relais | HTML, API, tâches d’escalade/évaluation |
| Intercampus | `CoursInterCampus` | HTML, API, tâche de rappel |
| Notifications | `Notification`, `Announcement` | HTML, API, providers, tâche d’envoi |
| Core | dashboard, exports, PWA root service worker | HTML, API d’instantané, admin supervision |

Les selectors sont employés par les vues/services pour les lectures et les services encapsulent les écritures. Le frontend chargé par `base.html` est Tailwind compilé, Flowbite et quelques feuilles de design/CSS métier ; l’application conserve un manifest et un service worker PWA.

## C. Vérifications de référence

| Contrôle | Résultat |
| --- | --- |
| `pytest` | 11 tests collectés, 11 réussis |
| `ruff check .` | OK |
| `ruff format --check .` | 169 fichiers déjà formatés |
| `python manage.py check` | OK, aucune erreur |
| `python manage.py check --deploy` | OK avec un seul avertissement attendu sur la clé secrète courte fournie au contrôle |
| `npm ls --depth=0` | `flowbite` et `tailwindcss` présents |
| Recherche paiement | aucune occurrence de paiement/Stripe/PayPal/checkout/facturation détectée |

L’environnement virtuel versionné n’est pas dans Git mais le lien `.venv/bin/python3` était cassé. Les contrôles ont été exécutés dans un environnement temporaire reconstruit depuis `uv.lock`, sans modifier les dépendances déclarées.

## D. Inventaire : éléments utilisés à conserver

- Les modèles et migrations restent nécessaires, y compris `core.validators` car les migrations historiques les importent directement.
- Les `AppConfig`, enregistrements admin, middleware, context processor de notifications et adaptateur allauth configuré sont chargés indirectement par Django.
- Les pages `403`, `403_csrf`, `404` et `500` sont des points d’extension Django ; les templates allauth sont chargés par le moteur allauth et ne doivent pas être jugés uniquement par une recherche de chaînes locale.
- Les tâches `signals`, `alerts`, `intercampus` et `notifications` sont référencées par `config.celery_app` ou appelées par des services.
- Le manifest, les icônes PNG, Leaflet, les scripts de carte, `project.js`, les feuilles CSS de domaines et les assets cités dans le service worker sont utilisés.
- Les dépendances runtime ont une utilisation identifiée dans les settings, les imports ou les images Docker : Django, allauth account, DRF, drf-spectacular, Celery/beat, PostgreSQL, Redis/django-redis, CORS, environ, Argon2, Gunicorn et WhiteNoise.
- Les dépendances de développement servent aux tests, au lint/formatage, à la documentation Sphinx, au rendu des templates ou aux environnements locaux. `factory-boy`, `mypy`, `pre-commit` et `coverage` n’ont pas d’import applicatif, mais sont des outils déclarés et seront arbitrés à l’étape 3 selon l’outillage réellement documenté.

## E. Candidats confirmés pour l’étape 2

Les références ont été recherchées dans le code, la configuration, les templates, les commandes, Docker et les scripts. Les éléments suivants n’ont aucun appel interne actif et sont isolés de tout mécanisme dynamique connu :

### Code Python

- `estuairefleet/users/context_processors.py` : `allauth_settings` n’est pas enregistré dans `TEMPLATES`.
- `estuairefleet/users/tasks.py` : `get_users_count` est une tâche de démonstration (« pointless »), absente du beat et sans appel.
- `estuairefleet/signals/permissions.py` : `CanViewSignalMap` n’est référencée par aucune vue/API ; les parcours actifs utilisent les permissions du socle/users.
- `signals.selectors` : `get_active_signals_for_route`, `count_active_signals`, `get_active_signals_by_trajet` et `get_students_with_abuse` ne sont appelées par aucun module actif.
- `signals.services` : `close_signals_for_trajet` et `expire_signal` ne sont appelées nulle part ; les flux actifs utilisent `close_signal` et `expire_stale_signals`.
- `estuairefleet/signals/validators.py` : `validate_signal_position` est un ancien doublon de la résolution de géorepérage faite dans `resolve_trajet_for_position` ; aucun service ne l’appelle.
- `fleet.selectors` : `get_trajet_detail`, `get_buses_for_trajet`, `get_campuses` et `get_free_chauffeurs` n’ont aucun appel interne.
- `fleet.services` : `deactivate_campus`, `assign_trajet` et `estimate_eta` n’ont aucun appel interne.
- `estuairefleet/fleet/forms.py` : `BusForm` n’est référencé par aucune vue, URL ou API.

### Templates et assets

- `templates/fleet/my_bus.html` et `templates/fleet/network.html` sont les anciennes versions statiques ; les vues actives rendent respectivement `my_bus_live.html` et `network_live.html`.
- Les partials jamais inclus : `_alert_banner.html`, `_badge_status.html`, `_confirm_modal.html`, `_empty_state.html`, `_form_field.html`, `_navbar.html`, `_sidebar.html`, `_stat_card.html` et `common/form_fields.html`.
- `static/css/project.css` n’est chargé par aucun template, configuration ou service worker.
- `static/pwa/icons/icon-192.svg` et `icon-512.svg` ne sont référencés ni par le manifest, ni par les templates, ni par le service worker ; seuls les PNG sont livrés à l’exécution.

Ces éléments seront supprimés seulement après une vérification de démarrage, de résolution des URLs/templates et de non-régression à l’étape 2.

## F. Points à traiter à l’étape 3 plutôt qu’à l’étape 2

- `allauth.socialaccount` et `SocialAccountAdapter` semblent non utilisés : aucune configuration de provider ni route métier sociale n’existe. Leur retrait doit être testé comme un changement de configuration/dépendance, donc reporté à l’étape 3.
- `factory-boy`, `mypy`, `pre-commit` et `coverage` n’ont pas d’usage applicatif direct. Leur maintien ou retrait doit tenir compte des commandes de qualité et de la documentation du projet.
- `hiredis` et `redis` sont consommés indirectement par l’écosystème Redis/Celery ; ils ne doivent pas être retirés sur la seule base de l’absence d’import direct.
- `test.sqlite3` est suivi par Git et utilisé comme base déclarée par `config.settings.test` ; il faudra décider lors de la consolidation des tests s’il doit être remplacé par une base éphémère avant de le supprimer.

## G. Couverture de tests constatée

La couverture actuelle est limitée à 11 tests : inscription/OTP et intégration SMTP du domaine Users, plus le script de fusion `.env`. Il n’existe pas encore de suite dédiée pour Core, Fleet, Signals, Alerts, Intercampus, Notifications ou la supervision Admin. Les étapes 4 à 9 ajoutent ces tests domaine par domaine et l’étape 10 publie le rapport final.

## H. Contraintes confirmées

- Aucun élément de paiement n’est présent dans le dépôt audité.
- Tailwind CSS et Flowbite sont les seuls outils UI déclarés côté frontend ; Leaflet est conservé uniquement pour les cartes.
- La PWA est active via `manifest.json`, `sw.js` servi à la racine, l’installation depuis `project.js` et le cache du shell dans le service worker.
- La palette rouge/blanc est présente avec la couleur principale `#C8102E`.
- Les commits des étapes suivantes devront rester atomiques et être créés dans l’ordre demandé.

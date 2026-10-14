# Audit initial — EstuaireFleet

Date : 14 octobre 2026

## 1. Périmètre et sources

L’audit porte sur l’état du dépôt avant modification. Les deux fichiers nommés « Cahier des charges EstuaireFleet » et « Cahier des diagrammes UML » ne sont pas présents dans l’arborescence ni dans les fichiers suivis par Git. Les exigences détaillées dans la mission utilisateur sont donc la référence fonctionnelle et UML retenue pour l’audit et la suite des travaux. Cette hypothèse est reprise dans `docs/DECISIONS.md`.

## 2. Arborescence réelle et écart avec la cible

La structure réelle comprend :

- `config/` avec settings multi-environnements, URLs, routeur API, ASGI/WSGI et Celery ;
- `estuairefleet/` avec les apps `core`, `users`, `fleet`, `signals`, `alerts`, `intercampus` et `notifications`, plus `contrib/sites` ;
- `estuairefleet/templates/` avec les écrans des domaines et un seul composant commun minimal ;
- `estuairefleet/static/` avec le pipeline Tailwind, CSS de design system, CSS par domaine, JavaScript, Leaflet local et assets ;
- `compose/`, les deux fichiers Compose, `locale/`, `docs/`, `tests/`, `pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json`, `tailwind.config.js` et `justfile`.

Écarts avec l’architecture cible :

- `config/settings/` est conforme à la cible ; `config/api_router.py` existe ;
- les apps ont bien les couches métier principales, mais certaines n’ont pas de tests unitaires complets ni de permissions réellement implémentées ;
- la cible demande plusieurs composants dans `templates/common/`, alors qu’un seul fichier `form_fields.html` existe ;
- la cible attend un répertoire racine `tests/` organisé par domaine ; le dépôt contient surtout les tests sous chaque app et seulement des tests d’infrastructure dans `tests/` ;
- la cible indique des répertoires `compose/local` et `compose/production`, présents, mais il faut encore vérifier l’exécution réelle des images ;
- aucun cahier de référence n’est versionné dans `docs/`.

## 3. État par app

Légende : 0 = absent, partiel = présent mais incomplet ou non conforme aux exigences, complet = couche présente et raccordée, sous réserve des tests finaux.

### `core` — partiel

- Modèles : `BaseModel` UUID, `created_at`, `updated_at` — complet.
- Constantes, configuration métier, géométrie, exceptions et validateurs — présents.
- Services/selectors : pas de séparation métier dédiée nécessaire au socle, mais les helpers sont dispersés entre `core`, `fleet` et `signals`.
- Permissions : `IsTransportStaff` présent.
- URLs, vues et admin : accueil, tableau de bord admin et URLs présents.
- Templates : accueil et tableau de bord présents ; pas encore de composants génériques factorisés.
- Tests : quasi absents au niveau core.
- Commandes : `seed_demo`, simulations de bus et de signaux présentes.

### `users` — partiel avancé

- Modèles : `User`, OTP et profils `Student`, `Chauffeur`, `Administrateur`, `Personnel` présents ; consentement, suspension et relations principales présents.
- Forms : inscription publique, OTP, formulaires d’administration et utilisateur présents.
- Views/URLs : connexion par identifiant, OTP, inscription, déconnexion, profil et changement de mot de passe présents.
- Services/selectors : création et mise à jour de comptes, activation, mot de passe, consentement, abus et OTP présents.
- Permissions : mixins CBV et permissions DRF par rôle présents.
- Admin/API : admin et API de lecture présents ; la gestion complète des comptes par l’interface reste limitée.
- Templates : présents pour compte et profil, mais plusieurs composants communs manquent.
- Tests : inscription et OTP présents ; couverture des rôles, consentement, activation et suspension insuffisante.

### `fleet` — partiel avancé

- Modèles : `Campus`, `Trajet`, `Stop`, `Bus`, directions, statuts, itinéraire, arrêts, horaires, seuil, durée de vie du signal, position et ETA présents.
- Services : CRUD, affectations, transitions de bus, position, occupation et ETA présents.
- Selectors : carte des bus, bus chauffeur, bus disponibles et plus proche présents.
- Validators : itinéraire, horaires, jours et positions partiellement présents.
- Permissions : classe de permission minimale ; les permissions d’administration CRUD doivent être durcies.
- Views/URLs/templates : vues d’aperçu, réseau, bus chauffeur et écrans de carte présents ; gestion CRUD HTML avancée manquante.
- Admin/API : admin et endpoints Campus/Trajet/Bus présents, mais actions métier et pagination à vérifier.
- Tests : tests métier dédiés insuffisants, notamment transitions invalides et position chauffeur.
- Incident : aucun modèle `Incident` identifié. Décision d’emplacement à prendre dans `fleet`, domaine de rattachement de la flotte.

### `signals` — partiel avancé

- Modèle : signal, statuts, TTL, prise en charge, renouvellement, annulation, signalement abusif et contrainte conditionnelle d’unicité présents.
- Services : émission, annulation, renouvellement, clôture, expiration, anti-abus et purge de coordonnées présents.
- Selectors : historique, signaux actifs par trajet, résolution géographique et filtrage de visibilité présents.
- Validators/forms : présents mais l’émission HTML dépend de coordonnées fournies par le navigateur ; consentement explicite à l’interface à compléter.
- Permissions : visibilité étudiant/chauffeur/personnel/admin présente ; à renforcer par des tests d’autorisation exhaustifs.
- API/views : émission, signal courant, historique, actions et endpoint des points visibles présents.
- Temps réel : endpoint JSON léger et JavaScript d’émission présents ; paramètre `since`, retry automatique, état dégradé et polling carte complet manquants.
- Machine d’état : statuts présents, mais les transitions sont principalement implicites dans les services et l’expiration n’émet pas systématiquement les événements.
- Tests : quelques tests de confidentialité et service ; les scénarios d’intégration demandés manquent.

### `alerts` — partiel

- Modèles : `Alert`, `AlertResponse`, seuil, statut, priorité, délai et unicité d’alerte ouverte présents.
- Services/selectors : seuil, réponse chauffeur, escalade et résolution présents ; relais séquentiel, timeout par bus, motif structuré et rappel intermédiaire restent incomplets.
- Forms/views/URLs/templates : présents pour liste, détail et réponse.
- Permissions/API/admin : présents mais la réponse `J'arrive` ne clôt pas l’alerte selon la machine d’état cible et la réponse `Indisponible` ne pilote pas encore une chaîne de relais complète.
- Tâches : escalade périodique présente ; rappels intermédiaires et timeouts de relais manquants.
- Tests : quelques tests de seuil, réponse et escalade ; couverture des relais accepté/refusé, idempotence et doubles déclenchements insuffisante.

### `intercampus` — partiel

- Modèle : cours, campus départ/arrivée, début/fin, effectif, bus, statut et notification présents.
- Services/selectors/forms/views/URLs/templates : présents pour création, édition, affectation, transitions et planning.
- API/admin/permissions : présents avec restrictions de base.
- Tâches : notification préalable unique présente, mais le rappel, les changements avancés/annulés/prolongés et la planification à 30 minutes ne sont pas complets.
- Tests : conflits d’affectation et notification présents ; couverture des changements de dernière minute et rappels manquante.

### `notifications` — partiel

- Modèle : destinataire, titre, message, canal, état, lecture, date d’envoi et métadonnées présents.
- Services/selectors/views/URLs/templates/API/admin : centre in-app, lecture sécurisée et création in-app présents.
- Fournisseurs : aucune interface de fournisseur e-mail/SMS abstraite complète ; l’e-mail Django et le backend console de développement restent à raccorder.
- Types métier : les notifications des événements de bus, retard, changement, prise en charge, alerte, escalade et cours inter-campus ne sont pas toutes centralisées.
- Tests : isolation du destinataire présente ; couverture des compteurs, canaux et échecs manquante.

## 4. Tailwind, Flowbite et frontend

- Outil : npm avec `tailwindcss` 3.x et `flowbite` 2.x ; un seul script de build `npm run build:css` écrit `estuairefleet/static/css/tailwind.css` depuis `estuairefleet/static/src/tailwind.css`.
- Configuration : `tailwind.config.js` scanne les templates, le JavaScript et Flowbite ; le plugin Flowbite est activé.
- Templates : `base.html` charge le CSS compilé, le design system, les styles de domaines, Leaflet local et Flowbite JavaScript.
- Composants Flowbite déjà utilisés : navbar/collapse, toasts/dismiss, formulaires et interactions data attributes ; les composants réutilisables sont encore trop peu factorisés.
- Tokens : la palette INSAM est présente dans Tailwind et `design-system.css`, avec rouge principal, rouge foncé, rouge de signal, noir, fond clair et bordure.
- Leaflet : fichiers locaux présents ; la carte et les marqueurs nécessitent encore le polling opérationnel, le point rouge animé et le mode dégradé.
- Bootstrap : aucun reste détecté dans les sources suivies par Git. Un répertoire Bootstrap existe dans `staticfiles/`, artefact généré non suivi ; il doit être exclu de la livraison ou régénéré proprement.
- CDN : Flowbite et les polices sont encore chargés depuis des URLs externes ; cela doit être documenté pour les connexions faibles et la production.

## 5. Configuration et outillage

- Settings : base/local/test/production présents ; Django 5.2+, DRF, drf-spectacular, Celery, Redis, PostgreSQL, WhiteNoise, CORS et Argon2 configurés.
- Docker Compose : local et production présents avec Django, PostgreSQL, Redis, worker Celery, beat et Mailpit en local.
- Celery : autodiscovery et beat configurés pour expiration, escalade et cours à venir ; purge des positions, rappels et relais à ajouter.
- DRF : routeur global et endpoints par domaine présents ; pagination et schéma doivent être finalisés.
- Environnement : `.env.example` et exemples de production présents ; les paramètres métier principaux sont configurables.
- Python : `pyproject.toml` et `uv.lock` présents ; Ruff et pytest configurés.
- Pre-commit : aucun fichier `.pre-commit-config.yaml` identifié.
- Just : commandes d’installation, lancement, tests, lint, formatage, migration, seed et logs présentes ; build CSS absent.
- Export/statistiques : aucun module d’export PDF/Excel ni statistiques admin dédiées identifié.

## 6. Migrations et état de départ

Les migrations existent pour toutes les apps métier, avec plusieurs migrations correctives. La cohérence finale ne peut pas être certifiée par `makemigrations --check` dans l’environnement initial, car l’interpréteur `.venv/bin/python3` est un lien vers un environnement appartenant à `root` et retourne `Permission denied`. Les migrations devront être revalidées après réparation de l’environnement Python.

Le build Tailwind npm se lance et reconstruit le fichier CSS minifié ; il signale seulement une base Browserslist ancienne.

État de départ demandé :

| Contrôle | Résultat initial |
| --- | --- |
| `uv run python manage.py check` | bloqué par `.venv` non lisible |
| `uv run pytest` | bloqué par `.venv` non lisible |
| `uv run ruff check .` | bloqué par `.venv` non lisible |
| `uv run ruff format --check .` | bloqué par `.venv` non lisible |
| `uv run python manage.py makemigrations --check --dry-run` | bloqué par `.venv` non lisible |
| `npm run build:css` | lancé avec avertissement Browserslist |

## 7. Écarts UML et dettes identifiés

- Les documents UML absents empêchent une comparaison ligne à ligne ; la mission utilisateur est utilisée comme contrat de remplacement.
- `Incident` manque.
- La machine Bus accepte encore des transitions implicites d’occupation qui ne correspondent pas exactement aux transitions prescrites et ne réoriente pas les signaux quand le bus devient plein.
- La machine Signal ne garantit pas encore partout l’émission d’événements et la fermeture atomique attendues.
- La machine Alert ne possède pas le statut de relais explicite, la chaîne de bus suivante, le timeout par relais ni l’escalade complète.
- Le seuil par tranche horaire n’a pas de modèle dédié.
- Les rappels, notifications multi-canaux et annonces admin sont incomplets.
- L’API ne fournit pas encore partout les actions de profil, position bus, pagination et paramètre `since` requis.
- Les interfaces étudiant, chauffeur, admin et personnel ne couvrent pas encore tout le périmètre demandé.
- Les permissions `fleet` et `intercampus` sont des coquilles ou trop permissives.
- Le seed ne crée pas encore de signaux de démonstration et n’offre pas un compte explicitement complet pour chaque scénario métier.
- La couverture de tests des six machines d’état et des scénarios de confidentialité est insuffisante.
- Aucun pre-commit, export statistique ou commande de build CSS dans `justfile`.

## 8. Dette et bugs potentiels

- Environnement `.venv` non exploitable à cause des permissions.
- `get_active_signals_for_route()` attend un objet trajet alors que son nom et son argument suggèrent un identifiant.
- Les réponses API peuvent contenir des UUID et dates sans sérialisation uniforme.
- Le statut `AlertStatus.RELAY` demandé n’existe pas.
- L’alerte créée au seuil utilise un délai de cinq minutes alors que la cible demande trois minutes par défaut.
- La création de `Signal` autorise encore des coordonnées nulles au niveau modèle, ce qui est incompatible avec l’émission GPS du MVP si aucun contrôle de service ne les bloque.
- La position de bus et les points de signal ne sont pas purgés/anonymisés selon une tâche périodique complète.
- Le JavaScript d’émission affiche « envoyé » avant le retour serveur et ne gère pas le retry/polling.
- Le pipeline CSS n’est pas exposé par `justfile` et aucune vérification CI dédiée n’est visible dans l’audit initial.

## 9. Plan d’exécution retenu

1. Réparer l’environnement d’exécution et créer `docs/DECISIONS.md`.
2. Stabiliser `core` et `users` : constantes, consentement, profils, gestion admin, permissions et tests.
3. Finaliser `fleet` : `Incident`, transitions strictes, réorientation, CRUD, actions chauffeur et tests.
4. Finaliser `signals` : événements, TTL, `since`, polling, purge, anti-abus, confidentialité et tests d’intégration.
5. Refaire la machine `alerts` avec seuils horaires, relais et escalade idempotente.
6. Finaliser `intercampus` et `notifications`, leurs fournisseurs abstraits, rappels et annonces.
7. Harmoniser l’API DRF, permissions, pagination et OpenAPI.
8. Compléter les interfaces par rôle, composants communs, carte Leaflet et mode dégradé.
9. Ajouter le seed de démonstration, les exports/statistiques sans données commerciales et la documentation.
10. Exécuter tous les contrôles finaux : Ruff, format, migrations, Django, pytest, build CSS et scan de termes interdits.

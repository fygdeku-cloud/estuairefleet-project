# Rapport de nettoyage et de couverture de tests — EstuaireFleet

Date : 24 octobre 2026  
Branche : `main`

## A. Ce qui a été analysé

L’analyse a porté sur l’ensemble du dépôt : domaines Django, modèles et migrations, services/selectors, vues HTML et API, permissions, formulaires, tâches Celery, commandes de management, templates, partials, CSS/JavaScript, PWA, Docker/Compose, settings local/test/production, dépendances Python/JavaScript et tests existants.

La cartographie détaillée de départ est conservée dans [`docs/ANALYSE_NETTOYAGE_ETAPE1.md`](docs/ANALYSE_NETTOYAGE_ETAPE1.md).

Contraintes vérifiées : aucun élément de paiement détecté ; Tailwind CSS + Flowbite conservés côté UI ; PWA conservée ; UUID/BaseModel/TextChoices et architecture par domaine conservés ; palette principale `#C8102E` conservée.

## B. Éléments supprimés ou nettoyés

### Code mort et fichiers orphelins

- Suppression des helpers Signals jamais appelés : aliases/counts/groupements inutilisés, liste d’abus non consommée, fonctions de clôture globale et d’expiration unitaire non utilisées.
- Suppression de l’ancien validateur Signals remplacé par la résolution géographique active.
- Suppression des selectors Fleet non référencés (`get_trajet_detail`, `get_buses_for_trajet`, `get_campuses`, `get_free_chauffeurs`) et des services Fleet non référencés (`deactivate_campus`, `assign_trajet`, `estimate_eta`).
- Suppression de `BusForm`, du context processor Users non enregistré et de la tâche Celery Users de démonstration.
- Suppression de l’ancienne permission `CanViewSignalMap` devenue orpheline.
- Suppression des templates Fleet remplacés (`my_bus.html`, `network.html`) et des partials Common jamais inclus.
- Suppression de `static/css/project.css` non chargé et des deux icônes PWA SVG non référencées ; les PNG utilisés par le manifest sont conservés.
- Retrait de deux constantes Core inutilisées ; la constante d’alerte intermédiaire active est conservée.

### Dépendances et configuration

- Retrait des outils Python sans usage ou configuration dans le dépôt : `factory-boy`, `mypy`, `pre-commit` et `djlint`.
- Retrait de `allauth.socialaccount`, sans provider ni parcours social configuré ; l’authentification allauth account/e-mail reste active.
- Conservation des dépendances runtime indirectes nécessaires à Django, PostgreSQL, Redis/Celery, Argon2, DRF, drf-spectacular, CORS, WhiteNoise et Gunicorn.
- Régénération de `uv.lock` et synchronisation validée.
- Libellé de l’application Users traduit en français (`Utilisateurs`).
- Bundle Tailwind régénéré après suppression des templates orphelins ; Flowbite et Tailwind restent les seules dépendances frontend déclarées.

### Correction métier révélée par les tests

`create_user_with_profile()` transmettait le matricule au compte mais pas au profil `Student`. Le service a été corrigé et le comportement est désormais testé.

## C. Tests ajoutés par module

Les fixtures communes sont dans `estuairefleet/conftest.py`. Chaque domaine possède désormais son répertoire `tests/`.

| Module | Couverture ajoutée | Tests |
| --- | --- | ---: |
| Users | authentification e-mail/matricule + OTP, rôles, profils, permissions, création et modification | 11 |
| Fleet | Campus, Trajet, Bus, relations, capacité, statut, occupation, position | 5 |
| Signals | émission, unicité active, consentement, géorepérage, anti-abus, expiration, annulation, prise en charge | 7 |
| Alerts | seuil 5, réponses chauffeur, relais, acceptation, timeout, escalade, résolution admin | 7 |
| Core/Admin | fixtures partagées, accès supervision, snapshot live, exports CSV/XLSX/PDF | 7 |
| Intercampus | création, transitions, conflit d’affectation, notification chauffeur et rappel | 3 |
| Notifications | idempotence événementielle, non-lu/lu, contrôle du destinataire, e-mail, annonce | 3 |
| Existant hors domaines | fusion des fichiers `.env` | 6 |
| **Total** |  | **49** |

## D. Résultat de l’exécution

| Contrôle | Résultat |
| --- | --- |
| `pytest` global | **49 passed** en 16,12 s |
| Couverture `coverage run -m pytest` | **72 %** — 3 039 statements, 844 non couverts |
| `ruff check .` | OK |
| `ruff format --check .` | OK — 179 fichiers formatés |
| `manage.py check` avec settings test | OK |
| `makemigrations --check --dry-run` | OK — aucune migration manquante |
| `manage.py check --deploy` | OK, avec clé de contrôle suffisamment longue |
| `npm ls --depth=0` | Flowbite 2.5.2, Tailwind CSS 3.4.19 |
| `npm run build:css` | OK |
| `collectstatic --noinput` | OK — 212 fichiers inchangés, 2 copiés |

Les 28 % non couverts concernent surtout les endpoints API non exercés par HTTP, les templates HTML secondaires, les tâches Celery et les commandes de démonstration. Ils constituent la principale marge d’amélioration future ; ils ne correspondent pas à des échecs de la suite.

## E. Liste des commits effectués

1. `7287c26` — `chore: analyse complète du projet pour identification des inutilités`
2. `668e2fa` — `chore: suppression du code mort et des fichiers non utilisés`
3. `c312b33` — `chore: nettoyage des dépendances et configurations inutilisées`
4. `c219c60` — `test: mise en place et consolidation de la structure de tests par module`
5. `b5449d5` — `test(users): ajout et validation des tests du module Users`
6. `6cf25e0` — `test(fleet): ajout et validation des tests du module Fleet`
7. `9e42280` — `test(signals): ajout et validation des tests du module Signals`
8. `ab7813e` — `test(alerts): ajout et validation des tests du module Alerts`
9. `432ee53` — `test(intercampus+notifications+admin): ajout des tests des modules restants`
10. Le présent rapport est livré dans le commit final `docs: rapport de nettoyage et de couverture de tests par module`.

## F. Points d’attention restants

- La couverture globale de 72 % peut progresser sur les tâches Celery, les viewsets API et les parcours HTML secondaires.
- Le lien `.venv/bin/python3` présent dans l’environnement local était cassé et appartenait à un interpréteur supprimé ; les contrôles ont été exécutés dans un environnement temporaire reconstruit depuis `uv.lock`. Le dépôt lui-même reste inchangé sur ce point, car `.venv` est ignoré par Git.
- Le build frontend signale uniquement que la base Browserslist/caniuse-lite est obsolète ; aucune dépendance frontend inutilisée n’a été identifiée.
- Les exports PDF/XLSX sont des générateurs internes minimaux et mériteraient des tests de conformité de fichiers plus poussés si ces formats deviennent contractuels.
- Aucun élément de paiement n’a été introduit.

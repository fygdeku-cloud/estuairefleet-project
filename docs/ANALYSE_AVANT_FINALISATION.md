# Analyse avant finalisation du MVP

Date de l'audit : 19 octobre 2026

## Niveau actuel

Le dépôt est un MVP Django avancé, mais il n'est pas encore livrable comme PWA complète. Les domaines Core & Users, Fleet, Signals, Alerts, Intercampus et Notifications sont présents avec modèles, services, selectors, permissions, vues, templates, API et migrations. Le cœur métier Signal → Alerte → réponse chauffeur → escalade est déjà raccordé et dispose d'une base de tests.

Le niveau retenu avant finalisation est donc : **fonctionnel avancé, PWA manquante, vérifications locales à rejouer dans un environnement propre**.

## Éléments présents

- Django avec templates server-side, PostgreSQL, Redis, Celery et Docker Compose.
- Architecture par domaine avec `models.py`, `services.py`, `selectors.py`, formulaires, validateurs, permissions, vues et URLs.
- Modèles UUID et modèle socle `BaseModel`, statuts `TextChoices` et libellés/messages français.
- Authentification par e-mail ou matricule, OTP, profils étudiant/chauffeur/administrateur/personnel.
- Campus, trajets, arrêts et bus ; statuts métier et suivi de position des bus.
- Signal étudiant privé, unicité du signal actif, TTL, géorepérage et mécanismes anti-abus.
- Seuil d'alerte configurable à cinq signaux, réponse chauffeur, bus relais et escalade Celery.
- Cours inter-campus, notifications in-app/e-mail préparées et endpoints REST secondaires.
- Tailwind CSS + Flowbite, design system INSAM rouge/blanc, Leaflet local et OpenStreetMap.

## Écarts et risques identifiés

- Aucun `manifest.json`, service worker ou jeu d'icônes PWA n'est présent ; l'installation et le mode hors connexion sont donc incomplets.
- Le template de base ne référence pas encore de bundle Flowbite ni de script d'enregistrement du service worker.
- Les cartes disposent de pages et de polling, mais les parcours doivent être vérifiés dans le navigateur avec les routes API réellement disponibles.
- L'ancienne feuille CSS `design-system.css` coexiste avec le rendu Tailwind ; elle doit rester compatible sans réintroduire un second système visuel.
- Le fichier `.venv` local est illisible dans cet environnement ; les contrôles doivent utiliser un environnement uv temporaire distinct.
- Le contrôle du périmètre métier ne retourne aucun module financier ; les occurrences de `transaction` restantes correspondent exclusivement à `django.db.transaction.atomic`.

## Plan de finalisation

1. Rejouer les contrôles dans un environnement uv isolé et corriger les défauts révélés.
2. Ajouter la fondation PWA : manifest, icônes, service worker, cache offline minimal, enregistrement et métadonnées.
3. Vérifier les parcours Signals/Alerts/Intercampus/Notifications, les cartes et les permissions ; compléter les tests critiques.
4. Nettoyer les incohérences de configuration, lancer les contrôles finaux et produire le rapport de livraison.


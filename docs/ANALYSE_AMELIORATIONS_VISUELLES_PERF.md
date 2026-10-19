# Analyse avant améliorations visuelles, performance et architecture

Date : 19 octobre 2026

## État de référence

Le projet est un MVP Django server-side fonctionnel, avec Tailwind CSS, Flowbite, Leaflet, PWA, PostgreSQL, Redis et Celery. Les 28 tests existants passent avant cette phase d'amélioration.

## Frontend et UX

- 56 templates HTML sont présents. La navigation, les écrans Signals, Fleet, Alerts, Intercampus et Notifications mélangent des composants Tailwind récents avec l'ancien design system `.ef-*` dans `design-system.css`.
- Le template global charge six feuilles de style, Leaflet, Flowbite depuis un CDN et trois scripts métier sur chaque page, y compris les pages sans carte.
- Plusieurs écrans restent sur une seule ligne HTML ou utilisent des styles inline (`fleet/my_bus.html`, `fleet/network.html`, dashboard et anciens composants `.ef-*`). Les vues actives utilisent cependant surtout `my_bus_live.html` et `network_live.html`.
- La page étudiant possède un CTA clair, mais la carte de l'écran d'émission reste une illustration et la hiérarchie peut être renforcée avec un état de trajet, des garanties de confidentialité et un feedback plus explicite.
- Les écrans de carte n'exposent pas de légende ou de contrôle dédié à la localisation. Les zones cartographiques n'ont pas toutes une hauteur adaptative explicite pour les petits écrans.

## Carte et temps réel

- `signal_map.js` et `bus_tracking.js` interrogent toutes les cinq secondes, mais les marqueurs absents des réponses suivantes ne sont jamais retirés ; une carte reste donc visuellement obsolète.
- Les timers ne sont pas annulés lorsqu'une page devient cachée et les requêtes concurrentes ne sont pas annulées avec `AbortController`.
- Les cartes sont initialisées sans contrôle de zoom personnalisé, sans état vide intégré et sans gestion explicite de `visibilitychange` ou `prefers-reduced-motion`.

## Backend, requêtes et scalabilité

- Les statistiques admin chargent toutes les paires `created_at`/`taken_at` en mémoire pour calculer la moyenne ; ce calcul doit être borné ou agrégé pour éviter une croissance linéaire non maîtrisée.
- `get_operational_statistics()` exécute plusieurs compteurs indépendants à chaque affichage du dashboard sans cache court.
- `get_active_trajets()` précharge les relations puis boucle en Python pour le calendrier de service. C'est acceptable pour un petit réseau mais coûteux avec beaucoup de trajets.
- `evaluate_active_routes()` parcourt tous les trajets actifs et déclenche des accès métier par trajet chaque minute. Une sélection ciblée des trajets concernés et des verrous `skip_locked` amélioreront le comportement sous concurrence.
- Les tâches d'escalade et d'envoi récupèrent des lots sans verrouillage explicite ; deux workers peuvent donc examiner le même élément avant son changement d'état.
- Redis est utilisé pour le rate-limit des signaux et est configuré comme cache partagé en production, mais aucun cache court n'est exploité par les selectors de dashboard ou les lectures répétées.
- Les indexes métier existent déjà pour les signaux par trajet/statut/expiration, les bus et les notifications ; il manque des indexes alignés sur les filtres des tâches (`status` + échéance) et sur les lectures personnelles d'un signal ou d'une notification.

## Architecture et maintenabilité

- La séparation selectors/services est globalement respectée. Les améliorations doivent rester dans ces couches et éviter les accès ORM dans les templates.
- Les champs `count` dans les templates doivent être remplacés par des annotations ou des relations préchargées avec compteurs afin de rendre le coût lisible.
- Le template de base concentre la navigation et les scripts ; des partials de navigation, d'état réseau et de légende cartographique rendront les évolutions moins risquées.
- Les scripts carte partagent une logique de polling qui mérite un petit utilitaire commun pour la visibilité, le backoff, le nettoyage des marqueurs et l'état dégradé.

## Plan de travail retenu

1. Harmoniser le shell visuel, les composants et les parcours principaux avec Tailwind/Flowbite.
2. Corriger la responsivité et les cartes sur les tailles mobile, tablette et desktop.
3. Réduire le JavaScript chargé globalement et fiabiliser le polling/caching PWA.
4. Ajouter les indexes et optimisations ciblées, un cache dashboard et des tâches Celery sûres sous concurrence.
5. Factoriser les composants et valider tests, qualité, migrations et parcours clés.


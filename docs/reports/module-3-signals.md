# Module 3 — Signals

## 1. Objectif du module

Permettre une émission de localisation consentie, géorepérée et temporaire, avec affichage différent selon le rôle.

## 2. Livré

Signal UUID, unicité conditionnelle par étudiant, expiration, renouvellement plafonné, annulation, clôture, faux signal, avertissement/suspension et purge des coordonnées. Les selectors filtrent les signaux expirés et anonymisent le personnel. L’API couvre émission, mine, visible, cancel, renew, close et flag-false. Les événements internes sont prêts pour le module 4.

## 3. Écrans et UX

Accueil étudiant avec bouton rouge « Je suis là », historique, carte chauffeur, supervision et écran anti-abus. La boucle de conception a augmenté la taille du bouton, isolé le message d’état dans une région live et rendu les listes lisibles sur 390 px.

## 4. Décisions et écarts

`INACTIF` est présent dans les TextChoices mais n’est jamais créé par le service. La purge remplace les coordonnées par NULL. Les anciennes entrées de démonstration sont migrées avec relation nullable car aucun trajet/étudiant fiable ne pouvait être déduit.

## 5. Tests

8 tests de régression verts, check Django, Ruff et check production verts. Des contrôles ciblés ont prouvé : étudiant visible uniquement pour son propre signal, endpoint visible refusé en 403 et accès direct à l’ID d’un autre étudiant en 404. La couverture chiffrée et le test de concurrence dédié restent à compléter.

## 6. Sécurité et vie privée

Consentement horodaté, verrouillage étudiant, quota de cinq tentatives par minute, filtre `expires_at`, labels anonymisés pour le personnel et purge périodique. Aucune position étudiante n’est injectée dans le template étudiant.

## 7. Reproduire

`uv run python manage.py seed_demo`, `uv run python manage.py simulate_signals --trajet R1-AL --count 5`, puis ouvrir `/signals/`, `/signals/driver/` et `/signals/monitor/` avec les rôles correspondants.

## 8. Limites connues et dette

Le bouton HTML de démonstration obtient encore la position sans poster le payload complet ; l’API est la voie fonctionnelle. Le clustering, le polling JavaScript complet, la confirmation modale et les captures Playwright restent à finaliser.

## 9. Points d’accroche

Les signaux Django `signal_emitted` et `signal_state_changed`, le seuil de trajet et la clôture en lot sont prêts pour Alerts.

## 10. Checklist

- [x] Modèle, géorepérage, confidentialité et API
- [x] Expiration, renouvellement, purge et anti-abus
- [ ] Parcours visuel complet émettre → chauffeur → clôture

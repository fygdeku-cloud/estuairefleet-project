# Module 2 — Fleet

## 1. Objectif du module

Modéliser les campus, trajets, arrêts et bus, puis fournir les services de statut, de position et d’occupation.

## 2. Livré

`Campus`, `Trajet`, `Stop` et `Bus` avec index, contraintes, validation d’itinéraire, transitions de statut, affectation chauffeur, position fraîche et estimation ETA. Les selectors réseau et les endpoints de lecture/position sont disponibles.

## 3. Écrans et UX

Vue flotte, réseau et Mon bus utilisent une carte locale légère, une liste synchronisable et des badges textuels. Trois améliorations visuelles : cartes plus aérées, statut affiché avec texte et non couleur seule, panneaux empilés sur mobile.

## 4. Décisions et écarts

`PLEIN → EN_ROUTE` est accepté en plus de `PLEIN → DISPONIBLE`. Les anciennes relations historiques sont migrées vers un bus unique par chauffeur et un trajet unique.

## 5. Tests

8 tests de régression verts, Ruff et migrations verts. Les tests exhaustifs de toutes les transitions et les captures de l’éditeur d’itinéraire restent à compléter.

## 6. Sécurité et vie privée

Un chauffeur ne peut modifier que son bus ; les lectures de position sont réservées aux acteurs transport.

## 7. Reproduire

`uv run python manage.py seed_demo`, `uv run python manage.py check`, puis `/fleet/overview/`, `/fleet/network/` et `/fleet/my-bus/`.

## 8. Limites connues et dette

L’éditeur cartographique avancé et l’envoi GPS périodique réel nécessitent encore le bundle Leaflet complet et une session chauffeur active.

## 9. Points d’accroche

`seuil_alerte`, `count_active_signals` et `estimate_eta` sont disponibles pour le module Alerts.

## 10. Checklist

- [x] Modèles, services, selectors et API de base
- [x] Interface réseau responsive
- [ ] Éditeur d’itinéraire avancé et captures automatisées

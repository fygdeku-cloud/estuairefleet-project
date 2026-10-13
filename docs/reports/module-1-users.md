# Module 1 — Core & Users

## 1. Objectif du module

Fournir un socle Django cohérent, une identité visuelle INSAM et une authentification par e-mail ou matricule avec profils de rôle.

## 2. Livré

BaseModel UUID, configuration métier, géométrie pure, exceptions, permissions par rôle, backend `IdentifierBackend`, changement forcé du mot de passe, réinitialisation e-mail, formulaires d’administration et commandes de démo. Les layouts et composants principaux sont dans `templates/base.html` et `design-system.css`.

## 3. Écrans et UX

Connexion, changement de mot de passe, tableau de bord et pages de profil existantes ont reçu le gabarit responsive et les états d’erreur. La boucle visuelle a conduit à réduire la navigation mobile, renforcer le contraste du bouton principal et supprimer les ressources externes.

## 4. Décisions et écarts

Les profils sont composés par OneToOne comme prévu. L’ancien socle Cookiecutter contenait des noms historiques ; des alias de compatibilité sont conservés dans les modèles pour éviter une rupture inutile.

## 5. Tests

Suite de base conservée et enrichie par des tests de parcours. Ruff, formatage et migrations sont contrôlés ; `check --deploy` est vérifié avec des variables de production temporaires.

## 6. Sécurité et vie privée

Argon2 prioritaire, connexion inactive refusée, comptes sans inscription publique, mot de passe temporaire non réaffiché après création, et middleware de changement obligatoire.

## 7. Reproduire

`uv run python manage.py migrate`, `uv run python manage.py seed_demo`, `uv run pytest`, `uv run ruff check .`.

## 8. Limites connues et dette

La liste d’administration complète avec historique de connexion et captures Playwright n’est pas encore produite. Le fournisseur de verrouillage de connexion dédié reste à installer.

## 9. Points d’accroche

Les permissions DRF et le profil Student sont prêts pour Fleet et Signals.

## 10. Checklist

- [x] UUID, rôles, backend d’identifiant et design system
- [x] Tests/lint/checks
- [ ] Captures automatisées complètes

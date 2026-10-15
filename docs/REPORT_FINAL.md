# Rapport final — MVP EstuaireFleet

Date : 16 octobre 2026

## Résultat

Le MVP est terminé sur la base du dépôt existant. Le dépôt est propre, les migrations sont cohérentes, le pipeline frontend unique est conservé et 25 tests passent.

Les deux cahiers annoncés ne sont pas versionnés dans le dépôt. La mission utilisateur et les statuts déjà présents ont donc servi de référence normative. Cette hypothèse est détaillée dans `docs/DECISIONS.md`.

## Bilan par module

### `core` et `users`

Existant : `BaseModel`, UUID, utilisateurs personnalisés, profils de rôle, OTP, authentification par identifiant et consentement de localisation.

Ajouts et corrections :

- édition complète du profil étudiant avec date de consentement ou de retrait tracée par service ;
- actions API d’activation, suspension et modification du profil ;
- seed idempotent avec campus, trajets, bus, comptes des rôles et signaux de démonstration ;
- statistiques opérationnelles administrateur ;
- exports CSV, XLSX minimal natif et PDF imprimable ;
- composants communs Tailwind/Flowbite factorisés.

### `fleet`

Existant : campus, trajets, arrêts, bus, positions, ETA, statuts et incidents.

Ajouts et corrections :

- CRUD API branché sur les services d’écriture ;
- transitions verrouillées du bus et validation des positions ;
- occupation pleine et notification de réorientation des demandes actives ;
- actions chauffeur de statut, occupation et position ;
- carte Leaflet des bus avec polling à cinq secondes et partage périodique chauffeur ;
- tests de transitions, autorisation de position et réorientation.

### `signals`

Existant : TTL, renouvellement, annulation, expiration, anti-abus, contrainte conditionnelle et filtrage de confidentialité.

Ajouts et corrections :

- relations étudiant et trajet obligatoires par migration de nettoyage ;
- tâche d’expiration et purge des positions planifiées ;
- émission smartphone directe en un clic avec consentement et retour d’erreur ;
- polling JSON avec `since`, retry progressif et bandeau de mode dégradé ;
- carte Leaflet avec points rouges contrastés et animés ;
- tests de confidentialité et d’unicité active conservés et validés.

### `alerts`

Existant : seuil de trajet, seuil par tranche horaire, réponse chauffeur et base d’escalade.

Ajouts et corrections :

- chaîne `EnAttente → Déclenchée → EnCours → Résolue`, relais et escalade ;
- verrous `select_for_update` et opérations idempotentes ;
- timeout de trois minutes, rappels intermédiaires et évaluation périodique ;
- sélection du bus relais suivant après refus ;
- notifications prioritaires au chauffeur et de prise en charge à l’étudiant ;
- tests de réponse, timeout, relais accepté et relais refusé.

La réponse chauffeur reste portée par le modèle `AlertResponse` relié en OneToOne à l’alerte, conformément au modèle relationnel existant.

### `intercampus` et `notifications`

Existant : cours inter-campus, changements de planning, centre in-app, canaux et fournisseur console.

Ajouts et corrections :

- affectation automatique du premier bus compatible sans conflit ;
- notifications à trente minutes et rappel rapproché ;
- diffusion différée des canaux e-mail et SMS via tâche Celery et interfaces fournisseurs ;
- compteur non lus côté HTML et endpoint `unread_count` ;
- annonces administrateur et lecture sécurisée par destinataire ;
- tests d’affectation, conflit et confidentialité.

### API REST et interfaces

- routeur global et OpenAPI existants conservés ;
- pagination DRF par défaut à 50 éléments ;
- endpoints de profil, bus, trajets, signaux, alertes, cours et notifications ;
- écrans étudiant, chauffeur, personnel et administrateur raccordés aux parcours métier ;
- composants partagés, erreurs personnalisées, états vides, feedback et responsive mobile-first.

## Écarts UML corrigés

- `Incident` rattaché à `fleet`, avec résolution et administration ;
- transitions strictes du bus, occupation et disponibilité ;
- signal actif unique par étudiant, expiration et relations obligatoires ;
- visibilité des positions limitée au chauffeur concerné, personnel et administration ;
- alerte par seuil et par tranche, relais séquentiel, timeout et escalade ;
- cours inter-campus avec affectation, changement, annulation et rappels ;
- notifications typées et centre de lecture sécurisé.

## Contrôle de conformité

Le scan demandé des termes interdits renvoie zéro occurrence dans le code, les templates, la documentation technique et le lockfile. Inventaire des résidus supprimés : liste vide, aucun résidu correspondant n’a été trouvé dans l’état initial scanné.

Le pipeline Bootstrap généré dans `staticfiles/vendor/bootstrap` a été supprimé ; les sources utilisent uniquement Tailwind CSS, Flowbite et le pipeline npm existant.

## Vérifications finales

```text
ruff check .                         OK
ruff format --check .                OK
python manage.py check               OK
python manage.py makemigrations --check --dry-run  OK
pytest                               25 passed
npm run build:css                    OK
UV_PROJECT_ENVIRONMENT=/tmp/estuairefleet-venv uv lock --check  OK
```

La vérification des migrations affiche uniquement un avertissement de connexion PostgreSQL local ; elle termine avec « No changes detected ». Les tests utilisent la configuration SQLite dédiée.

## Démarrage

```bash
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver
```

Avec Docker :

```bash
docker compose --env-file .env -f docker-compose.local.yml up --build
```

Contrôle complet : `just verify`.

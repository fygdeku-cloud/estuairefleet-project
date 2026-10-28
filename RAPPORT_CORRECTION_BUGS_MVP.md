# Rapport de correction des bugs critiques du MVP EstuaireFleet

## Périmètre

Les trois parcours corrigés sont :

1. émission d’un signal étudiant ;
2. lecture partagée des notifications destinées aux Administrateurs et Chauffeurs ;
3. chargement du dashboard de supervision et de sa carte.

Les corrections respectent la séparation existante entre selectors (lecture) et services (écriture et logique métier). Aucun changement n’a été introduit dans les règles de confidentialité étudiant, de géorepérage, d’anti-abus ou de paiement.

## 1. Signal étudiant non enregistré

### Cause exacte

Le parcours appelait correctement `POST /api/signals/`, puis `SignalCollectionView` déléguait à `emit_signal`. Le service métier arrêtait cependant la création avant `Signal.objects.create()` lorsque `Student.consent_location` était faux.

Le formulaire d’inscription ne recueillait pas ce consentement et la page « Je suis là » ne proposait aucun moyen de l’accorder. La réponse observée était donc HTTP 400 avec le code `consent_required`.

### Correction

- `StudentSignalHomeView` expose l’état du consentement à la page.
- `signals/home.html` affiche une modale Flowbite/Tailwind en français lorsque le consentement manque.
- Le JavaScript appelle `POST /api/users/consent/` avec le CSRF avant de demander la position.
- Après consentement, la géolocalisation est envoyée à `POST /api/signals/`.
- Les erreurs de permission, de géolocalisation et de règles métier sont affichées à l’étudiant.
- Le service `emit_signal` est conservé comme point unique de contrôle : un seul signal actif, géorepérage, TTL et anti-abus restent appliqués.
- Le test vérifie la création en base et la visibilité immédiate depuis les endpoints Chauffeur et Admin.

## 2. Notifications lues / non lues

### Cause exacte

`Notification.read_at` était stocké sur chaque copie destinataire. Lorsqu’une alerte était diffusée à plusieurs Administrateurs ou Chauffeurs, chaque copie possédait son propre état. `mark_notification_read` ne mettait à jour que la copie de l’utilisateur connecté et son cache personnel.

### Correction

- Ajout de `Notification.read_group_id`, avec migration `notifications.0005`.
- Les copies d’une même alerte diffusée à un rôle partagent un UUID de groupe de lecture.
- `mark_notification_read` verrouille les notifications du groupe et renseigne `read_at` sur toutes les copies concernées.
- Les compteurs de notifications non lues sont invalidés pour chaque destinataire impacté.
- Les notifications personnelles étudiant restent indépendantes et ne sont pas marquées lues pour d’autres personnes.
- Un test couvre deux Administrateurs recevant la même notification et vérifie que la lecture du premier efface le compteur du second.

## 3. Carte et blocs du dashboard bloqués sur « Chargement… »

### Cause exacte

L’endpoint `GET /dashboard/live/` fonctionnait et renvoyait déjà `statistics`, `buses`, `alerts`, `incidents` et `routes`. Le JavaScript échouait avant le premier polling en appelant `L.tileLayer(...)`, alors que le fichier local `static/vendor/leaflet/leaflet.js` était une façade minimale sans méthode `tileLayer`. L’exception interrompait donc le script avant le rendu des blocs.

Par ailleurs, les bus du jeu de démonstration étaient créés sans latitude ni longitude : même après réparation du script, la carte ne pouvait afficher aucun bus tant qu’une position n’avait pas été envoyée.

### Correction

- La façade locale implémente maintenant `tileLayer`, `setView`, `fitBounds`, `invalidateSize`, les marqueurs, les tooltips et leur suppression.
- Une surface cartographique locale visible est rendue sans dépendance à un téléchargement externe de tuiles.
- Les scripts dashboard, supervision des signaux et suivi des bus tolèrent l’absence d’un fournisseur de tuiles.
- Le dashboard efface l’état de chargement et affiche un message français explicite si un polling échoue.
- `seed_demo` initialise les positions des bus sur le premier point de leur trajet ; les données de démonstration sont ainsi visualisables immédiatement.
- Le test du dashboard vérifie que les coordonnées de bus sont sérialisées dans le snapshot JSON.

## Tests effectués

### Tests ciblés

Commande :

```bash
docker compose -f docker-compose.local.yml exec -T django \
  python -m pytest estuairefleet/core/tests/test_admin.py \
  estuairefleet/signals/tests/test_signals.py \
  estuairefleet/notifications/tests/test_notifications.py -q
```

Résultat : **18 tests réussis**.

Contrôles complémentaires :

```bash
docker compose -f docker-compose.local.yml exec -T django python manage.py check
docker compose -f docker-compose.local.yml exec -T django python manage.py seed_demo
node --check estuairefleet/static/vendor/leaflet/leaflet.js
node --check estuairefleet/static/js/dashboard_live.js
node --check estuairefleet/static/js/signal_map.js
node --check estuairefleet/static/js/bus_tracking.js
```

### Suite complète

La suite complète a reproduit quatre échecs indépendants des trois corrections : les services Alertes et Intercampus utilisent `select_for_update()` avec une jointure nullable (`relay_bus` / `bus_affecte`) sur PostgreSQL. PostgreSQL refuse le verrouillage du côté nullable de cette jointure. Ces défauts préexistants sont à traiter séparément.

## Comment tester manuellement

1. Démarrer la stack avec les commandes indiquées à la fin de ce rapport.
2. Ouvrir `http://localhost:8001/`.
3. Se connecter avec un compte étudiant de démonstration, cliquer sur « Je suis là », accepter la localisation, puis vérifier le message de succès.
4. Ouvrir la supervision avec le compte Admin ou Chauffeur et vérifier le signal actif.
5. Ouvrir une notification d’alerte avec deux utilisateurs du même rôle : après lecture par le premier, le compteur non lu du second doit être nul après rafraîchissement.
6. Ouvrir `http://localhost:8001/dashboard/` avec le compte Admin : les blocs doivent remplacer « Chargement… » et les bus du seed doivent apparaître sur la carte.

Comptes de démonstration créés par `seed_demo` : mot de passe `EstuaireDemo2026!`. Les adresses sont `admin@insam.local`, `chauffeur1@insam.local` à `chauffeur3@insam.local`, et `etudiant1@insam.local` à `etudiant25@insam.local`.

## Commits réalisés

- `841899e` — `chore: analyse des bugs signal, notifications et carte`
- `fea779a` — `fix(signals): correction de l’émission et de l’enregistrement des signaux étudiants`
- `71bd903` — `fix(notifications): correction du statut lu/non lu partagé entre utilisateurs`
- `0d49c86` — `fix(dashboard): correction du chargement de la carte et des données de supervision`
- `9d012e3` — `test: validation des corrections signal, notifications et carte de supervision`
- commit courant — `docs: rapport de correction des bugs critiques du MVP`

## Points d’attention restants

- La façade cartographique locale est volontairement légère et n’embarque pas les tuiles raster OpenStreetMap. Pour une carte géographique détaillée en production, remplacer `static/vendor/leaflet/leaflet.js` par une version Leaflet épinglée et fournir une politique de tuiles adaptée.
- Les quatre échecs PostgreSQL de la suite complète concernent les services Alertes/Intercampus et ne sont pas liés aux trois bugs corrigés.
- Les positions de bus restent soumises au rafraîchissement du chauffeur ou à la commande `simulate_bus_movement` ; le seed ne fournit qu’une position initiale de démonstration.

